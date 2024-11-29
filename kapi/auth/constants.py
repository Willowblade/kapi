import os
from uuid import uuid4

KAPI_PRIVATE_KEY = os.getenv("KAPI_PRIVATE_KEY", str(uuid4()))
API_KEY = os.getenv("KAPI_API_KEY", str(uuid4()))
