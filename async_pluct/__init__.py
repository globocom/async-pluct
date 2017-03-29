from .resource import Resource
from .session import Session as AsyncPluct

_pluct = AsyncPluct()
resource = _pluct.resource
__version__ = '0.1.0'
