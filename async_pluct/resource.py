import jsonpointer
import json
from collections import UserDict
from collections import UserList

from jsonschema import SchemaError, validate, ValidationError, RefResolver

from async_pluct.schema import Schema


class Resource(object):

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            'Use subclasses or Resource.from_data to initialize resources')

    def init(self, url, data=None, schema=None, session=None, response=None,
             headers=None):
        self.url = url
        self.data = data or self.default_data()
        self.schema = schema
        self.session = session
        self.response = response
        self.headers = headers

    async def session_request_json(self, url):
        response = await self.session.request(url)
        return json.loads(response.body)

    async def is_valid(self):
        handlers = {'https': self.session_request_json,
                    'http': self.session_request_json}
        schema = await self.schema.raw_schema
        resolver = RefResolver.from_schema(schema,
                                           handlers=handlers)
        try:
            validate(self.data, schema, resolver=resolver)
        except (SchemaError, ValidationError):
            return False
        return True

    async def rel(self, link, **kwargs):
        kwargs['url'] = self.url
        kwargs['resource_params'] = self.data
        return await self.schema.rel(link, **kwargs)

    def has_rel(self, name):
        return self.schema.has_rel(name)

    def expand_uri(self, name, **kwargs):
        context = dict(self.data, **kwargs)
        return self.schema.expand_uri(name, context)

    @classmethod
    def from_data(cls, url, data=None, schema=None, session=None,
                  response=None, headers=None):
        if isinstance(data, (list, tuple)):
            klass = ArrayResource
        elif isinstance(data, dict):
            klass = ObjectResource
        else:
            return data

        return klass(
            url, data=data, schema=schema, session=session, response=response,
            headers=headers)

    @classmethod
    def from_response(cls, response, session, schema):
        try:
            data = json.loads(response.body)
        except ValueError:
            data = {}
        return cls.from_data(
            url=response.request.url,
            data=data,
            session=session,
            schema=schema,
            response=response,
            headers=response.headers
        )

    def resolve_pointer(self, *args, **kwargs):
        return jsonpointer.resolve_pointer(self.data, *args, **kwargs)

    def __getitem__(self, item):
        schema = self.item_schema(item)
        return self.from_data(self.url,
                              data=self.data[item],
                              schema=schema,
                              session=self.session)


def get_content_type_for_resource(resource):
    response = resource.response
    if (response and response.headers and
            response.headers.get('content-type')):
        return resource.response.headers['content-type']
    else:
        return 'application/json; profile=' + resource.schema.url


class ObjectResource(UserDict, Resource, dict):

    SCHEMA_PREFIX = 'properties'

    def __init__(self, *args, **kwargs):
        self.init(*args, **kwargs)

    def default_data(self):
        return {}

    def iterate_items(self):
        return iter(self.data.items())

    def item_schema(self, key):
        href = '#/{0}/{1}'.format(self.SCHEMA_PREFIX, key)
        return Schema(href, raw_schema=self.schema, session=self.session)

    def __ne__(self, other):
        return self.data != other

    def __eq__(self, other):
        return self.data == other

    def __getitem__(self, item):
        return Resource.__getitem__(self, item)

    def __repr__(self):
        return "<Pluct ObjectResource %s>" % self.data


class ArrayResource(UserList, Resource, list):

    SCHEMA_PREFIX = 'items'

    def __init__(self, *args, **kwargs):
        self.init(*args, **kwargs)

    def default_data(self):
        return []

    def iterate_items(self):
        return enumerate(self.data)

    def item_schema(self, key):
        href = '#/{0}'.format(self.SCHEMA_PREFIX)
        return Schema(href, raw_schema=self.schema, session=self.session)

    def __getitem__(self, item):
        return Resource.__getitem__(self, item)

    def __repr__(self):
        return "<Pluct ArrayResource %s>" % self.data
