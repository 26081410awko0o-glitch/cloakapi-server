FROM python:3.11-slim

# إعداد بيئة العمل
WORKDIR /app

# نسخ ملفات المتطلبات أولاً (لاستخدام Docker cache بكفاءة)
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود كاملاً
COPY . .

# متغيرات البيئة الافتراضية
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# فتح المنفذ
EXPOSE 8000

# أمر التشغيل
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
