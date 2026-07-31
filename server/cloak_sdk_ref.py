"""

مرجع داخلي لاستيراد CodeEncryptor في سياق الخادم دون circular imports.

"""

import sys

import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



from cloak_sdk.crypto import CodeEncryptor as CodeEncryptorRef



__all__ = ["CodeEncryptorRef"]

