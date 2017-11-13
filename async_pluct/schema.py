import json

from cgi import parse_header
from collections import UserDict
from jsonpointer import resolve_pointer


class ResolveAsyncSchemaError(Exception):
    pass


class Schema(UserDict):

    @staticmethod
    def __new__(cls, href, *args, **kwargs):
        (href, url, pointer) = cls._split_href(href)

        session = kwargs['session']

        if href in session.store:
            return session.store[href]

        instance = super(Schema, cls).__new__(cls)
        session.store[href] = instance

        if pointer:
            # Reuse the constructor to make it register the root schema
            # without a pointer
            cls(url, *args, **kwargs)

        return instance

    def __init__(self, href, raw_schema=None, session=None):
        self._init_href(href)
        self._data = None
        self._raw_schema = raw_schema
        self.session = session

    @property
    def __class__(self):
        return dict

    def _is_simple_dict(self, obj):
        return isinstance(obj, dict) and (not isinstance(obj, Schema))

    def expand_refs(self, item):
        if self._is_simple_dict(item):
            iterator = iter(item.items())
        elif isinstance(item, list):
            iterator = enumerate(item)
        else:
            return

        for key, value in iterator:
            key_ref_in_dict = (
                self._is_simple_dict(value) and ('$ref' in value)
            )

            if key_ref_in_dict:
                item[key] = self.from_href(
                    value['$ref'], raw_schema=self._raw_schema,
                    session=self.session)
                continue
            self.expand_refs(value)

    @property
    def data(self):
        if self._data is None:
            if self._raw_schema is None:
                raise ResolveAsyncSchemaError
            self._data = self.resolve_sync()
        return self._data

    async def resolve_data(self):
        if self._data is None:
            self._data = await self.resolve()

    @property
    async def raw_schema(self):
        return self._raw_schema

    @classmethod
    def from_href(cls, href, raw_schema, session):
        href, url, pointer = cls._split_href(href)
        is_external = url != ''

        if is_external:
            return LazySchema(href, session=session)

        return Schema(href, raw_schema=raw_schema, session=session)

    def resolve_sync(self):
        if self._raw_schema is None:
            raise ResolveAsyncSchemaError("resolve_sync")
        data = resolve_pointer(self._raw_schema, self.pointer)
        self.expand_refs(data)
        return data

    async def resolve(self):
        raw_schema = await self.raw_schema
        data = resolve_pointer(raw_schema, self.pointer)
        self.expand_refs(data)
        return data

    def get_link(self, name):
        data = self.data
        links = data.get('links', [])
        for link in links:
            if link.get('rel') == name:
                return link
        return None

    def _init_href(self, href):
        (self.href, self.url, self.pointer) = self._split_href(href)

    @classmethod
    def _split_href(cls, href):
        parts = href.split('#', 1)
        url = parts[0]

        pointer = ''
        if len(parts) > 1:
            pointer = parts[1] or pointer

        if len(pointer) > 1:
            href = '#'.join((url, pointer))
        else:
            href = url

        return href, url, pointer


class LazySchema(Schema):

    def __init__(self, href, session=None):
        self._init_href(href)
        self.session = session
        self._data = None
        self._raw_schema = None

    @property
    async def raw_schema(self):
        if self._raw_schema is None:
            response = await self.session.request(self.url,
                                                  **self.session.schema_args)
            self._raw_schema = json.loads(response.body)
        return self._raw_schema

    def __repr__(self):
        return repr({'$ref': self.href})


def get_profile_from_header(headers):
    if 'content-type' not in headers:
        return None

    full_content_type = 'content-type: {0}'.format(headers['content-type'])
    header, parameters = parse_header(full_content_type)

    if 'profile' not in parameters:
        return None

    if 'original-profile' in parameters:
        return parameters['original-profile']

    return parameters.get('profile')
