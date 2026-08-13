"""
CloakAPI Executor — محرك التنفيذ الآمن للأكواد
يقوم بفك تشفير الكود وتنفيذه في بيئة مقيدة (Restricted Execution).
"""

import sys
import io
import time
import traceback
import builtins
from typing import Any


# القائمة البيضاء للوحدات المسموح باستيرادها داخل الأكواد المرفوعة
ALLOWED_MODULES = {
    "math", "json", "re", "datetime", "collections", "itertools",
    "functools", "string", "random", "hashlib", "base64",
    "statistics", "decimal", "fractions", "operator",
    # مكتبات علمية شائعة (إذا كانت مثبتة)
    "numpy", "pandas", "scipy", "requests",
}

# الدوال المحظورة من builtins
BLOCKED_BUILTINS = {
    "__import__", "open", "exec", "eval", "compile",
    "input", "breakpoint", "__loader__", "__spec__",
}


class SafeExecutor:
    """
    محرك التنفيذ الآمن.
    يستخدم بيئة مقيدة (Restricted Globals) لمنع الوصول للنظام.

    ملاحظة معمارية:
        هذا الحل مناسب للـ MVP. في الإنتاج يجب استبداله بـ Docker/Firecracker
        لضمان عزل كامل على مستوى نظام التشغيل.
    """

    def __init__(self, timeout_seconds: int = 10, max_output_size: int = 1_000_000):
        """
        المعاملات:
            timeout_seconds: الحد الأقصى لوقت تنفيذ الكود (ثواني).
            max_output_size: الحد الأقصى لحجم المخرجات (bytes).
        """
        self.timeout_seconds = timeout_seconds
        self.max_output_size = max_output_size

    def execute(self, code: str, inputs: dict, env: dict = None) -> dict:
        """
        ينفذ الكود بأمان ويعيد النتيجة.

        المعاملات:
            code: كود Python كنص.
            inputs: المدخلات كـ dict تُمرر للدالة الرئيسية.

        المخرجات:
            dict: {success, result, error, execution_time_ms, stdout}
        """
        start_time = time.time()

        # بناء بيئة التنفيذ المقيدة
        safe_globals = self._build_safe_globals(env or {})
        safe_locals = {}

        # التقاط stdout
        stdout_capture = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = stdout_capture

            # تنفيذ الكود في البيئة المقيدة
            exec(code, safe_globals, safe_locals)  # noqa: S102

            # البحث عن الدالة الرئيسية
            main_func = safe_locals.get("main") or safe_locals.get("handler")

            if main_func is None:
                raise ValueError("لم يتم العثور على دالة 'main' أو 'handler' في الكود.")

            if not callable(main_func):
                raise ValueError("'main' أو 'handler' يجب أن تكون دالة قابلة للاستدعاء.")

            # استدعاء الدالة مع المدخلات
            result = main_func(**inputs)

            # التحقق من نوع المخرجات
            if not isinstance(result, (dict, list, str, int, float, bool, type(None))):
                result = str(result)

            execution_time = (time.time() - start_time) * 1000

            return {
                "success": True,
                "result": result,
                "error": None,
                "execution_time_ms": round(execution_time, 2),
                "stdout": stdout_capture.getvalue()[:self.max_output_size],
            }

        except TimeoutError:
            return {
                "success": False,
                "result": None,
                "error": f"تجاوز الكود الحد الزمني ({self.timeout_seconds} ثانية).",
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "stdout": stdout_capture.getvalue(),
            }

        except Exception as e:
            # تنظيف رسالة الخطأ من المعلومات الحساسة
            error_msg = self._sanitize_error(str(e), traceback.format_exc())
            return {
                "success": False,
                "result": None,
                "error": error_msg,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                "stdout": stdout_capture.getvalue(),
            }

        finally:
            sys.stdout = original_stdout

    def _build_safe_globals(self, env: dict) -> dict:
        """
        يبني بيئة globals مقيدة تمنع الوصول لموارد النظام.
        """
        # نسخ من builtins مع إزالة الدوال الخطرة
        safe_builtins = {
            name: getattr(builtins, name)
            for name in dir(builtins)
            if name not in BLOCKED_BUILTINS and not name.startswith("__")
        }

        # إضافة __builtins__ المقيد
        safe_globals = {
            "__builtins__": safe_builtins,
            "__name__": "__cloakapi_sandbox__",
            "__doc__": None,
            "ENV": env,  # توفير متغيرات البيئة داخل الساندبوكس
        }

        # إضافة مكتبة __import__ مقيدة
        def restricted_import(name, *args, **kwargs):
            if name not in ALLOWED_MODULES:
                raise ImportError(
                    f"استيراد '{name}' غير مسموح به في بيئة CloakAPI. "
                    f"المكتبات المسموح بها: {', '.join(sorted(ALLOWED_MODULES))}"
                )
            return __import__(name, *args, **kwargs)

        safe_globals["__builtins__"]["__import__"] = restricted_import
        
        # إضافة دعم os.environ بشكل محدود
        import os
        class FakeOS:
            environ = env
            def getenv(self, key, default=None):
                return self.environ.get(key, default)
        
        safe_globals["os"] = FakeOS()

        return safe_globals

    def _sanitize_error(self, error: str, tb: str) -> str:
        """
        ينظف رسالة الخطأ من المعلومات الحساسة (مسارات الملفات، إلخ).
        """
        # إزالة مسارات الملفات الداخلية
        lines = tb.split("\n")
        safe_lines = []
        for line in lines:
            if "/home/" in line or "/usr/" in line or "site-packages" in line:
                continue
            safe_lines.append(line)

        safe_tb = "\n".join(safe_lines).strip()
        return safe_tb if safe_tb else error
