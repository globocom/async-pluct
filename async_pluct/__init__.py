from .resource import Resource
from .session import Session as AsyncPluct

# Used to mock validate method on tests
from async_pluct import resource
resources = resource

_pluct = AsyncPluct()
resource = _pluct.resource
__version__ = '0.1.0'
