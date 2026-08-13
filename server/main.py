"""
CloakAPI Server — الخادم الرئيسي (FastAPI)
يستقبل طلبات الرفع والتشغيل ويديرها بأمان.
"""

import time
import logging
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Any
import sys
import os

# إضافة المسار للاستيراد
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloak_sdk.crypto import CodeEncryptor, APIKeyGenerator
from .core.security import RateLimiter, APIKeyManager, CodeVault, SecurityHeaders
from .core.executor import SafeExecutor

# ==================== إعداد التطبيق ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("cloakapi")

app = FastAPI(
    title="CloakAPI Server",
    description="منصة تحويل الكود إلى API محمي ومستضاف",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — السماح بالطلبات من أي مصدر في الـ MVP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ==================== المكونات الأساسية ====================
encryptor = CodeEncryptor()
key_generator = APIKeyGenerator()
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
key_manager = APIKeyManager()
code_vault = CodeVault()
executor = SafeExecutor(timeout_seconds=10)

# ==================== نماذج البيانات (Pydantic) ====================

class DeployRequest(BaseModel):
    encrypted_code: str = Field(..., description="الكود المشفر بصيغة Base64")
    encryption_key: str = Field(..., description="مفتاح التشفير")
    secrets: dict[str, str] = Field(default={}, description="متغيرات البيئة والأسرار المشفرة")
    endpoint_name: str = Field(default="my-api", description="اسم الـ Endpoint")
    description: str = Field(default="", description="وصف الـ API")
    original_filename: str = Field(default="script.py", description="اسم الملف الأصلي")


class RunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default={}, description="المدخلات للدالة الرئيسية")


# ==================== Middleware للـ Logging ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} ({duration}ms) "
        f"[{request.client.host if request.client else 'unknown'}]"
    )

    # إضافة Headers الأمان
    for key, value in SecurityHeaders.get().items():
        response.headers[key] = value

    return response


# ==================== نقاط الـ API ====================

@app.get("/", tags=["Health"])
async def root():
    """نقطة التحقق من حالة الخادم."""
    return {
        "service": "CloakAPI Server",
        "version": "1.0.0",
        "status": "operational",
        "message": "حوّل كودك إلى API محمي في ثوانٍ 🚀",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """فحص صحة الخادم — يُستخدم من خدمات المراقبة."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "endpoints_count": len(code_vault._vault),
    }


@app.post("/deploy", tags=["Deploy"])
async def deploy_endpoint(payload: DeployRequest):
    """
    يستقبل الكود المشفر ويسجله كـ API جديد.
    يعيد رابط الـ API ومفتاح المصادقة.
    """
    # التحقق من صحة الكود المشفر بفك تشفيره مؤقتاً
    try:
        raw_code = encryptor.decrypt(payload.encrypted_code, payload.encryption_key)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="فشل فك تشفير الكود. تأكد من صحة البيانات المرسلة."
        )

    # التحقق من وجود الدالة الرئيسية
    if "def main(" not in raw_code and "def handler(" not in raw_code:
        raise HTTPException(
            status_code=422,
            detail="الكود يجب أن يحتوي على دالة 'main(**kwargs)' أو 'handler(**kwargs)'."
        )

    # توليد معرف فريد ومفتاح API
    endpoint_id = key_generator.generate_endpoint_id()
    api_key = key_generator.generate()

    # تخزين الكود المشفر في الخزنة
    code_vault.store(
        endpoint_id=endpoint_id,
        encrypted_code=payload.encrypted_code,
        encryption_key=payload.encryption_key,
        secrets=payload.secrets,
        metadata={
            "name": payload.endpoint_name,
            "description": payload.description,
            "filename": payload.original_filename,
            "deployed_at": time.time(),
        }
    )

    # تسجيل مفتاح الـ API
    key_manager.register(
        api_key=api_key,
        endpoint_id=endpoint_id,
        metadata={"name": payload.endpoint_name}
    )

    # بناء رابط الـ API
    base_url = os.environ.get("CLOAKAPI_BASE_URL", "https://cloakapi-server.onrender.com")
    api_url = f"{base_url}/run/{endpoint_id}"

    logger.info(f"✅ Endpoint جديد: {endpoint_id} ({payload.endpoint_name})")

    return {
        "success": True,
        "endpoint_id": endpoint_id,
        "api_key": api_key,
        "api_url": api_url,
        "endpoint_name": payload.endpoint_name,
        "description": payload.description,
        "message": "تم رفع الكود بنجاح كـ API محمي!",
        "usage": {
            "method": "POST",
            "url": api_url,
            "headers": {"X-API-Key": api_key},
            "body": {"inputs": {"param1": "value1"}},
        }
    }


@app.post("/run/{endpoint_id}", tags=["Execute"])
async def run_endpoint(
    endpoint_id: str,
    payload: RunRequest,
    x_api_key: str = Header(..., alias="X-API-Key", description="مفتاح المصادقة")
):
    """
    يستدعي كود مرفوع مسبقاً مع المدخلات المحددة.
    يتطلب مفتاح API صالح في الـ Header.
    """
    # التحقق من مفتاح الـ API
    key_data = key_manager.validate(x_api_key)
    if not key_data:
        raise HTTPException(
            status_code=401,
            detail="مفتاح API غير صالح أو منتهي الصلاحية."
        )

    # التحقق من أن المفتاح مرتبط بهذا الـ Endpoint
    if key_data["endpoint_id"] != endpoint_id:
        raise HTTPException(
            status_code=403,
            detail="هذا المفتاح غير مخول للوصول لهذا الـ Endpoint."
        )

    # تطبيق Rate Limiting
    allowed, rate_info = rate_limiter.is_allowed(x_api_key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"تجاوزت الحد المسموح ({rate_info['limit']} طلب/دقيقة).",
                "retry_after_seconds": rate_info["reset_seconds"],
                "rate_limit_info": rate_info,
            }
        )

    # استرجاع الكود المشفر
    code_data = code_vault.retrieve(endpoint_id)
    if not code_data:
        raise HTTPException(
            status_code=404,
            detail="الـ Endpoint غير موجود أو تم حذفه."
        )

    # فك تشفير الكود في الذاكرة
    try:
        raw_code = encryptor.decrypt(
            code_data["encrypted_code"],
            code_data["encryption_key"]
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="خطأ داخلي: فشل فك تشفير الكود."
        )

    # تنفيذ الكود بأمان
    result = executor.execute(raw_code, payload.inputs, env=code_data.get("secrets", {}))
    
    # تحديث الإحصاءات
    with key_manager._lock:
        key_data["total_calls"] += 1
        key_data["last_used"] = time.time()
        key_manager._save_keys()
    
    with code_vault._lock:
        code_data["execution_count"] += 1
        code_vault._save_vault()

    if not result["success"]:
        logger.warning(f"⚠️ خطأ في تنفيذ {endpoint_id}: {result['error'][:100]}")
        raise HTTPException(
            status_code=422,
            detail={
                "message": "فشل تنفيذ الكود.",
                "error": result["error"],
                "execution_time_ms": result["execution_time_ms"],
            }
        )

    logger.info(f"✅ تنفيذ ناجح: {endpoint_id} ({result['execution_time_ms']}ms)")

    return {
        "success": True,
        "result": result["result"],
        "execution_time_ms": result["execution_time_ms"],
        "stdout": result.get("stdout", ""),
        "rate_limit": {
            "remaining": rate_info["remaining"],
            "limit": rate_info["limit"],
            "window_seconds": rate_info["window_seconds"],
        }
    }


@app.delete("/endpoint/{endpoint_id}", tags=["Manage"])
async def delete_endpoint(
    endpoint_id: str,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """يحذف Endpoint مرفوع مسبقاً."""
    key_data = key_manager.validate(x_api_key)
    if not key_data or key_data["endpoint_id"] != endpoint_id:
        raise HTTPException(status_code=403, detail="غير مخول.")

    code_vault.delete(endpoint_id)
    key_manager.revoke(x_api_key)

    logger.info(f"🗑️ تم حذف Endpoint: {endpoint_id}")
    return {"success": True, "message": f"تم حذف الـ Endpoint '{endpoint_id}' بنجاح."}


@app.get("/stats/{endpoint_id}", tags=["Manage"])
async def get_stats(
    endpoint_id: str,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """يعرض إحصاءات الاستخدام لـ Endpoint محدد."""
    key_data = key_manager.get_stats(x_api_key)
    if not key_data or key_data["endpoint_id"] != endpoint_id:
        raise HTTPException(status_code=403, detail="غير مخول.")

    code_data = code_vault.retrieve(endpoint_id)

    return {
        "endpoint_id": endpoint_id,
        "total_calls": key_data["total_calls"],
        "created_at": key_data["created_at"],
        "last_used": key_data["last_used"],
        "metadata": code_data["metadata"] if code_data else {},
    }


# ==================== معالج الأخطاء العام ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"خطأ غير متوقع: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "خطأ داخلي في الخادم. يرجى المحاولة لاحقاً."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
