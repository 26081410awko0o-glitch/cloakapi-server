"""

CloakAPI Security — طبقة الأمان الشاملة

تشمل: التحقق من الـ API Keys، Rate Limiting، وإدارة الجلسات.

"""



import time

import hashlib

import hmac

import os

from collections import defaultdict

from threading import Lock

from typing import Optional



class RateLimiter:
  
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
      
        self.max_requests = max_requests
      
        self.window_seconds = window_seconds
      
        self._requests: dict[str, list] = defaultdict(list)
      
        self._lock = Lock()
      


    def is_allowed(self, api_key: str) -> tuple[bool, dict]:
      
        now = time.time()
      
        window_start = now - self.window_seconds
      
        with self._lock:
          
            self._requests[api_key] = [t for t in self._requests[api_key] if t > window_start]
          
            current_count = len(self._requests[api_key])
          
            remaining = self.max_requests - current_count
          
            if current_count >= self.max_requests:
              
                oldest_request = self._requests[api_key][0]
              
                reset_time = int(oldest_request + self.window_seconds - now)
              
                return False, {"limit": self.max_requests, "remaining": 0, "reset_seconds": max(reset_time, 1), "window_seconds": self.window_seconds}
              
            self._requests[api_key].append(now)
          
            return True, {"limit": self.max_requests, "remaining": remaining - 1, "reset_seconds": self.window_seconds, "window_seconds": self.window_seconds}
          


class APIKeyManager:
  
    def __init__(self):
      
        self._keys: dict[str, dict] = {}
      
        self._lock = Lock()
      


    def register(self, api_key: str, endpoint_id: str, metadata: dict = None) -> bool:
      
        with self._lock:
          
            if api_key in self._keys: return False
              
            self._keys[api_key] = {"endpoint_id": endpoint_id, "created_at": time.time(), "is_active": True, "metadata": metadata or {}, "total_calls": 0, "last_used": None}
          
            return True
          


    def validate(self, api_key: str) -> Optional[dict]:
      
        with self._lock:
          
            data = self._keys.get(api_key)
          
            if not data or not data["is_active"]: return None
              
            data["total_calls"] += 1
          
            data["last_used"] = time.time()
          
            return data
          


    def revoke(self, api_key: str) -> bool:
      
        with self._lock:
          
            if api_key in self._keys:
              
                self._keys[api_key]["is_active"] = False
              
                return True
              
            return False
          


    def get_stats(self, api_key: str) -> Optional[dict]:
      
        with self._lock: return self._keys.get(api_key)
          


class CodeVault:
  
    def __init__(self):
      
        self._vault: dict[str, dict] = {}
      
        self._lock = Lock()
      


    def store(self, endpoint_id: str, encrypted_code: str, encryption_key: str, metadata: dict = None) -> bool:
      
        with self._lock:
          
            self._vault[endpoint_id] = {"encrypted_code": encrypted_code, "encryption_key": encryption_key, "stored_at": time.time(), "metadata": metadata or {}, "execution_count": 0}
          
            return True
          


    def retrieve(self, endpoint_id: str) -> Optional[dict]:
      
        with self._lock:
          
            data = self._vault.get(endpoint_id)
          
            if data: data["execution_count"] += 1
              
            return data
          


    def delete(self, endpoint_id: str) -> bool:
      
        with self._lock:
          
            if endpoint_id in self._vault:
              
                del self._vault[endpoint_id]
              
                return True
              
            return False
          


class SecurityHeaders:
  
    @staticmethod
  
    def get() -> dict:
      
        return {
          
            "X-Content-Type-Options": "nosniff",
          
            "X-Frame-Options": "DENY",
          
            "X-XSS-Protection": "1; mode=block",
          
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
          
            "Cache-Control": "no-store, no-cache, must-revalidate",
          
            "Pragma": "no-cache",
          
        }
      









































































