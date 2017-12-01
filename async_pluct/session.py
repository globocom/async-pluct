import json

from async_pluct.http import http_client
from aiohttp import ClientResponse

from async_pluct.resource import Resource
from async_pluct.schema import Schema, LazySchema, get_profile_from_header


class Session(object):

    def __init__(self, client=None, timeout=None, schema_args={}):
        self.timeout = timeout
        self.store = {}
        self.schema_args = schema_args

        if client is None:
            self.client = http_client()
        else:
            self.client = client

    async def close(self):
        await self.client.close()

    async def resource(self, url, **kwargs):
        response = await self.request(url, **kwargs)
        schema = None

        schema_url = get_profile_from_header(response.headers)
        if schema_url is not None:
            schema = LazySchema(href=schema_url, session=self)

        return Resource.from_response(
            response=response, session=self, schema=schema)

    async def schema(self, url, **kwargs):
        response = await self.request(url, **kwargs)
        data = json.loads(response.body)
        return Schema(url, raw_schema=data, session=self)

    async def request(self, url, **kwargs):

        if self.timeout is not None:
            kwargs.setdefault('request_timeout', self.timeout)

        if 'timeout' in kwargs:
            timeout = kwargs.pop('timeout')
            kwargs.setdefault('request_timeout', timeout)

        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('content-type', 'application/json')

        kwargs.setdefault('method', 'GET')

        response = await self.client.fetch(url, **kwargs)

        if isinstance(response, ClientResponse):
            response.raise_for_status()

        return response
