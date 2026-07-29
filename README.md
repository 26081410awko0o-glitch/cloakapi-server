# CloakAPI 🔐

> **حوّل كودك إلى API محمي ومستضاف فورياً — في سطر واحد.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)

---

## ما هو CloakAPI؟

**CloakAPI** هي منصة وبنية تحتية تتيح للمطورين تحويل أي سكربت Python إلى واجهة برمجة تطبيقات (API) سحابية آمنة ومستضافة مجاناً، مع **إخفاء الكود المصدري تماماً** وحمايته من السرقة أو الهندسة العكسية.

### لماذا CloakAPI؟
- **حماية الملكية الفكرية:** كودك لا يُرى أبداً — يُشفَّر قبل الرفع ولا يُفكّ إلا في الذاكرة وقت التنفيذ.
- **نشر فوري:** سطر واحد يحول سكربتك المحلي إلى API عالمي.
- **مجاني ودائم:** مستضاف على خدمات Serverless تعمل 24/7 بدون توقف.
- **آمن:** Rate Limiting، API Keys، وبيئة تنفيذ مقيدة.

---

## التثبيت السريع

```bash
pip install cloakapi
```

أو من المصدر:
```bash
git clone https://github.com/YOUR_USERNAME/cloakapi.git
cd cloakapi
pip install -e .
```

---

## الاستخدام

### الخطوة 1: اكتب سكربتك

```python
# my_script.py
def main(**kwargs):
    x = kwargs.get("x", 0)
    y = kwargs.get("y", 0)
    return {"result": x + y, "message": "مرحباً من CloakAPI!"}
```

> **مهم:** يجب أن يحتوي الملف على دالة `main(**kwargs)` أو `handler(**kwargs)` تعيد `dict`.

### الخطوة 2: ارفع الكود كـ API

```python
import cloakapi as cloak

result = cloak.deploy("my_script.py")
```

**المخرجات:**
```
============================================================
✅  تم رفع الكود بنجاح كـ API محمي!
============================================================
🔗  رابط الـ API   : https://cloakapi-server.onrender.com/run/ep_abc123
🔑  مفتاح المصادقة: cloak_a3f8b2c1d4e5f6a7b8c9d0e1
🆔  معرف الـ Endpoint: ep_abc123
------------------------------------------------------------
📌  مثال على الاستخدام (Python):

import requests
response = requests.post(
    "https://cloakapi-server.onrender.com/run/ep_abc123",
    json={"inputs": {"x": 5, "y": 10}},
    headers={"X-API-Key": "cloak_a3f8b2c1d4e5f6a7b8c9d0e1"}
)
print(response.json())
============================================================
```

### الخطوة 3: استخدم الـ API من أي مكان

```python
import requests

response = requests.post(
    "https://cloakapi-server.onrender.com/run/ep_abc123",
    json={"inputs": {"x": 5, "y": 10}},
    headers={"X-API-Key": "cloak_a3f8b2c1d4e5f6a7b8c9d0e1"}
)

print(response.json())
# {"success": true, "result": {"result": 15, "message": "مرحباً من CloakAPI!"}, ...}
```

---

## واجهة سطر الأوامر (CLI)

```bash
# رفع سكربت كـ API
cloakapi deploy my_script.py --name "my-calculator" --desc "حاسبة بسيطة"

# عرض الـ APIs المرفوعة
cloakapi list

# استدعاء API
cloakapi call ep_abc123 cloak_key_xxx --input '{"x": 5, "y": 10}'
```

---

## نشر الخادم الخاص بك (مجاناً)

### الطريقة 1: Render.com (موصى به — 24/7 مجاناً)

```bash
# 1. انسخ المستودع
git clone https://github.com/YOUR_USERNAME/cloakapi.git

# 2. ارفعه على GitHub
# 3. اذهب إلى render.com → New Web Service
# 4. اختر المستودع وأدخل هذه الإعدادات:
#    Build Command: pip install -r requirements.txt
#    Start Command: uvicorn server.main:app --host 0.0.0.0 --port $PORT
#    Plan: Free
```

### الطريقة 2: النشر التلقائي

```bash
python deploy_server.py --github-token YOUR_GITHUB_TOKEN --repo-name cloakapi-server
```

### الطريقة 3: Docker

```bash
docker build -t cloakapi .
docker run -p 8000:8000 -e CLOAKAPI_BASE_URL=http://localhost:8000 cloakapi
```

---

## بنية المشروع

```
cloakapi/
├── cloak_sdk/              # مكتبة العميل (SDK)
│   ├── __init__.py         # الواجهة الرئيسية (deploy, call, list)
│   ├── client.py           # منطق الاتصال بالخادم
│   ├── crypto.py           # تشفير الكود (Fernet/AES)
│   └── cli.py              # واجهة سطر الأوامر
│
├── server/                 # الخادم السحابي (FastAPI)
│   ├── main.py             # نقطة الدخول الرئيسية
│   └── core/
│       ├── security.py     # Rate Limiting، API Keys، Code Vault
│       └── executor.py     # محرك التنفيذ الآمن (Sandboxing)
│
├── tests/
│   ├── sample_script.py    # مثال على سكربت للرفع
│   └── test_core.py        # اختبارات الوحدة
│
├── Dockerfile              # للنشر عبر Docker
├── Procfile                # للنشر على Render/Heroku
├── render.yaml             # إعدادات Render.com
├── deploy_server.py        # سكربت النشر التلقائي
└── requirements.txt
```

---

## الأمان

| الطبقة | الآلية |
|--------|--------|
| **تشفير الكود** | Fernet (AES-128-CBC + HMAC-SHA256) — تشفير من طرف العميل |
| **مصادقة الطلبات** | API Keys بصيغة `cloak_<48 حرف>` في Header |
| **Rate Limiting** | 100 طلب/دقيقة لكل مفتاح (Sliding Window) |
| **بيئة التنفيذ** | Restricted Globals — منع `os`, `open`, `subprocess` |
| **Headers الأمان** | HSTS, X-Frame-Options, X-Content-Type-Options |

---

## حدود الخطة المجانية (MVP)

| الميزة | القيمة |
|--------|--------|
| الطلبات/دقيقة | 100 |
| مهلة التنفيذ | 10 ثواني |
| حجم الكود الأقصى | 1 MB |
| المكتبات المسموحة | math, json, re, datetime, numpy, pandas, ... |

---

## خارطة الطريق

- [x] **v1.0** — النشر الأساسي، التشفير، Rate Limiting
- [ ] **v1.1** — لوحة تحكم ويب، إحصاءات الاستخدام
- [ ] **v1.2** — دعم Docker Containers للعزل الكامل
- [ ] **v2.0** — Marketplace للـ APIs، نظام الاشتراكات
- [ ] **v2.1** — Webhooks، Cron Jobs، Streaming Responses

---

## الترخيص

MIT License — مجاني للاستخدام الشخصي والتجاري.

---

*صُمِّم بعناية من قِبل فريق CloakAPI 🔐*
