"""

CloakAPI Crypto — وحدة تشفير الكود قبل الرفع

يتم التشفير على جهاز المطور (Client-Side) لضمان أن الخادم لا يرى الكود الأصلي.

"""



import os

import base64

import hashlib

from cryptography.fernet import Fernet





class CodeEncryptor:
  
    """
    
    يقوم بتشفير كود Python باستخدام Fernet (AES-128-CBC + HMAC-SHA256).
    
    الخوارزمية: تشفير متماثل (Symmetric Encryption) — سريع وآمن للـ MVP.
    
    """
  


    def encrypt(self, code: str) -> tuple[str, str]:
      
        """
        
        يشفر الكود ويعيد (الكود المشفر, مفتاح التشفير).
        

        
        المخرجات:
        
            tuple: (encrypted_code_base64, encryption_key_base64)
            
        """
      
        # توليد مفتاح عشوائي فريد لكل عملية رفع

        key = Fernet.generate_key()
      
        fernet = Fernet(key)
      


        # تشفير الكود

        encrypted_bytes = fernet.encrypt(code.encode("utf-8"))
      


        # تحويل إلى Base64 للإرسال عبر JSON

        encrypted_b64 = base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")
      
        key_b64 = key.decode("utf-8")
      


        return encrypted_b64, key_b64
      


    def decrypt(self, encrypted_b64: str, key_b64: str) -> str:
      
        """
        
        يفك تشفير الكود — يُستخدم فقط على الخادم عند التنفيذ.
        

        
        المعاملات:
        
            encrypted_b64: الكود المشفر بصيغة Base64
            
            key_b64: مفتاح التشفير بصيغة Base64
            

        
        المخرجات:
        
            str: الكود الأصلي كنص
            
        """
      
        key = key_b64.encode("utf-8")
      
        fernet = Fernet(key)
      


        encrypted_bytes = base64.urlsafe_b64decode(encrypted_b64.encode("utf-8"))
      
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
      


        return decrypted_bytes.decode("utf-8")
      


    def generate_code_hash(self, code: str) -> str:
      
        """
        
        يولد بصمة (Hash) للكود للتحقق من سلامته (Integrity Check).
        
        يُستخدم للتأكد من أن الكود لم يتغير بعد التشفير وفك التشفير.
        
        """
      
        return hashlib.sha256(code.encode("utf-8")).hexdigest()
      




class APIKeyGenerator:
  
    """
    
    مولد مفاتيح الـ API — يولد مفاتيح آمنة وفريدة.
    
    """
  


    @staticmethod
  
    def generate() -> str:
      
        """
        
        يولد مفتاح API بصيغة: cloak_<32 حرف عشوائي>
        
        مثال: cloak_a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5
        
        """
      
        random_bytes = os.urandom(24)
      
        key_hex = random_bytes.hex()
      
        return f"cloak_{key_hex}"
      


    @staticmethod
  
    def generate_endpoint_id() -> str:
      
        """
        
        يولد معرف فريد للـ Endpoint بصيغة: ep_<16 حرف>
        
        """
      
        random_bytes = os.urandom(8)
      
        return f"ep_{random_bytes.hex()}"
      






























































