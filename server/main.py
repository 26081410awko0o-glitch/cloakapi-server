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



# CORS

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



class DeployRequest(BaseModel):
  
    encrypted_code: str
  
    encryption_key: str
  
    endpoint_name: str = "my-api"
  
    description: str = ""
  
    original_filename: str = "script.py"
  


class RunRequest(BaseModel):
  
    inputs: dict[str, Any] = {}
  


@app.get("/health")

async def health_check():
  
    return {"status": "healthy", "timestamp": time.time()}
  


@app.post("/deploy")

async def deploy_endpoint(payload: DeployRequest):
  
    endpoint_id = key_generator.generate_endpoint_id()
  
    api_key = key_generator.generate()
  
    code_vault.store(endpoint_id, payload.encrypted_code, payload.encryption_key, {"name": payload.endpoint_name})
  
    key_manager.register(api_key, endpoint_id)
  
    base_url = os.environ.get("CLOAKAPI_BASE_URL", "https://cloakapi-server.onrender.com")
  
    return {"success": True, "endpoint_id": endpoint_id, "api_key": api_key, "api_url": f"{base_url}/run/{endpoint_id}"}
  


@app.post("/run/{endpoint_id}")

async def run_endpoint(endpoint_id: str, payload: RunRequest, x_api_key: str = Header(..., alias="X-API-Key")):
  
    key_data = key_manager.validate(x_api_key)
  
    if not key_data or key_data["endpoint_id"] != endpoint_id:
      
        raise HTTPException(status_code=401, detail="Unauthorized")
      
    code_data = code_vault.retrieve(endpoint_id)
  
    raw_code = encryptor.decrypt(code_data["encrypted_code"], code_data["encryption_key"])
  
    result = executor.execute(raw_code, payload.inputs)
  
    return result
  


if __name__ == "__main__":
  
    import uvicorn
  
    uvicorn.run(app, host="0.0.0.0", port=8000)
  












































