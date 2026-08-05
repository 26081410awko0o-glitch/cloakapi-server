"""
CloakAPI Client — المسؤول عن التواصل مع خادم CloakAPI
"""

import os
import json
import requests
from pathlib import Path
from .crypto import CodeEncryptor

# عنوان الخادم المستضاف — يمكن تغييره عبر متغير البيئة
SERVER_URL = os.environ.get("CLOAKAPI_SERVER", "https://cloakapi-server.koyeb.app")


class CloakClient:
    """
    العميل الرئيسي للتواصل مع منصة CloakAPI.
    يدير عمليات الرفع، الاستدعاء، وإدارة الـ Endpoints.
    """

    def __init__(self, server_url: str = None):
        self.server_url = (server_url or SERVER_URL).rstrip("/")
        self.encryptor = CodeEncryptor()
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "CloakAPI-SDK/1.0.0"
        })

    def deploy(self, file_path: str, endpoint_name: str = None, description: str = "") -> dict:
        """
        يقرأ ملف Python، يشفره، ويرفعه على الخادم كـ API.
        يعيد رابط الـ API ومفتاح المصادقة.
        """
        path = Path(file_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")
        if not path.suffix == ".py":
            raise ValueError("يجب أن يكون الملف بامتداد .py")

        # قراءة الكود
        raw_code = path.read_text(encoding="utf-8")

        # التحقق من وجود الدالة الرئيسية
        if "def main(" not in raw_code and "def handler(" not in raw_code:
            raise ValueError(
                "يجب أن يحتوي الملف على دالة رئيسية باسم 'main' أو 'handler'.\n"
                "مثال:\n"
                "def main(**kwargs):\n"
                "    return {'result': kwargs.get('x', 0) * 2}"
            )

        # تشفير الكود
        encrypted_code, encryption_key = self.encryptor.encrypt(raw_code)

        # إرسال الكود المشفر للخادم
        payload = {
            "encrypted_code": encrypted_code,
            "encryption_key": encryption_key,
            "endpoint_name": endpoint_name or path.stem,
            "description": description,
            "original_filename": path.name,
        }

        try:
            response = self._session.post(
                f"{self.server_url}/deploy",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"تعذر الاتصال بخادم CloakAPI على: {self.server_url}\n"
                "تأكد من اتصالك بالإنترنت."
            )
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json().get("detail", "")
            except Exception:
                pass
            raise RuntimeError(f"خطأ من الخادم: {e} — {error_detail}")

        data = response.json()

        # عرض النتيجة بشكل واضح
        self._print_success(data)
        return data

    def call(self, endpoint_id: str, api_key: str, **kwargs) -> dict:
        """
        يستدعي API محمي مع إرسال المعطيات كـ JSON.
        """
        payload = {"inputs": kwargs}
        try:
            response = self._session.post(
                f"{self.server_url}/run/{endpoint_id}",
                json=payload,
                headers={"X-API-Key": api_key},
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                detail = response.json().get("detail", "خطأ غير معروف")
            except Exception:
                detail = response.text
            raise RuntimeError(f"فشل الاستدعاء: {detail}")

        return response.json()

    def list_endpoints(self) -> list:
        """يجلب قائمة الـ Endpoints المحفوظة محلياً."""
        config_file = Path.home() / ".cloakapi" / "endpoints.json"
        if not config_file.exists():
            return []
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete(self, endpoint_id: str, api_key: str) -> dict:
        """يحذف Endpoint من الخادم."""
        try:
            response = self._session.delete(
                f"{self.server_url}/endpoint/{endpoint_id}",
                headers={"X-API-Key": api_key},
                timeout=15
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RuntimeError(f"فشل الحذف: {response.text}")
        return response.json()

    def _print_success(self, data: dict):
        """يطبع رسالة نجاح منسقة."""
        print("\n" + "="*60)
        print("✅  تم رفع الكود بنجاح كـ API محمي!")
        print("="*60)
        print(f"🔗  رابط الـ API   : {data.get('api_url', 'N/A')}")
        print(f"🔑  مفتاح المصادقة: {data.get('api_key', 'N/A')}")
        print(f"🆔  معرف الـ Endpoint: {data.get('endpoint_id', 'N/A')}")
        print("-"*60)
        print("📌  مثال على الاستخدام (Python):")
        print(f"""
import requests
response = requests.post(
    "{data.get('api_url', 'YOUR_URL')}",
    json={{"inputs": {{"x": 5, "y": 10}}}},
    headers={{"X-API-Key": "{data.get('api_key', 'YOUR_KEY')}"}}
)
print(response.json())
""")
        print("="*60 + "\n")

        # حفظ البيانات محلياً
        self._save_endpoint_locally(data)

    def _save_endpoint_locally(self, data: dict):
        """يحفظ بيانات الـ Endpoint محلياً للرجوع إليها لاحقاً."""
        config_dir = Path.home() / ".cloakapi"
        config_dir.mkdir(exist_ok=True)
        endpoints_file = config_dir / "endpoints.json"

        endpoints = []
        if endpoints_file.exists():
            try:
                with open(endpoints_file, "r", encoding="utf-8") as f:
                    endpoints = json.load(f)
            except Exception:
                endpoints = []

        endpoints.append(data)

        with open(endpoints_file, "w", encoding="utf-8") as f:
            json.dump(endpoints, f, ensure_ascii=False, indent=2)
