# Used to mock validate method on tests
try:
    from async_pluct import resource
    resources = resource
except ImportError:
    pass

__version__ = '0.3.4'
