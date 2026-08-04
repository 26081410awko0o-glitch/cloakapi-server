"""

CloakAPI SDK — تحويل الكود إلى API محمي ومستضاف فورياً

"""



from .client import CloakClient



# الواجهة الرئيسية للمستخدم

_default_client = CloakClient()



def deploy(file_path: str, endpoint_name: str = None, description: str = "") -> dict:
  
    """
    
    يرفع ملف Python كـ API محمي ومستضاف.
    


    المعاملات:
    
        file_path (str): المسار الكامل أو النسبي لملف Python.
        
        endpoint_name (str): اسم مخصص للـ endpoint (اختياري).
        
        description (str): وصف مختصر للـ API (اختياري).
        


    المخرجات:
    
        dict: يحتوي على رابط الـ API ومفتاح المصادقة.
        


    مثال:
    
        >>> import cloakapi as cloak
        
        >>> result = cloak.deploy("my_script.py")
        
        >>> print(result['api_url'])
        
        https://cloakapi-server.koyeb.app/run/abc123
        
    """
  
    return _default_client.deploy(file_path, endpoint_name=endpoint_name, description=description)
  




def call(endpoint_id: str, api_key: str, **kwargs) -> dict:
  
    """
    
    يستدعي API محمي مسبقاً.
    


    مثال:
    
        >>> result = cloak.call("abc123", "cloak_key_xxx", x=5, y=10)
        
    """
  
    return _default_client.call(endpoint_id, api_key, **kwargs)
  




def list_endpoints() -> list:
  
    """يعرض قائمة الـ APIs المرفوعة."""
  
    return _default_client.list_endpoints()
  




def delete(endpoint_id: str, api_key: str) -> dict:
  
    """يحذف API مرفوع."""
  
    return _default_client.delete(endpoint_id, api_key)
  




__version__ = "1.0.0"

__all__ = ["deploy", "call", "list_endpoints", "delete", "CloakClient"]
































