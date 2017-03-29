from async_pluct.http import http_client

from async_pluct.resource import Resource
from async_pluct.schema import Schema, LazySchema, get_profile_from_header


class Session(object):

    def __init__(self, client=None, timeout=None):
        self.timeout = timeout
        self.store = {}

        if client is None:
            print(http_client)
            self.client = http_client()
        else:
            self.client = client

    async def resource(self, url, **kwargs):
        response = await self.request(url, **kwargs)
        schema = None

        print(response.headers)

        schema_url = get_profile_from_header(response.headers)
        if schema_url is not None:
            schema = LazySchema(href=schema_url, session=self)

        return Resource.from_response(
            response=response, session=self, schema=schema)

    def schema(self, url, **kwargs):
        data = self.request(url, **kwargs).json()
        return Schema(url, raw_schema=data, session=self)

    async def request(self, url, **kwargs):

        if self.timeout is not None:
            kwargs.setdefault('request_timeout', self.timeout)

        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('content-type', 'application/json')

        kwargs.setdefault('method', 'get')

        print('meu ovo 4')

        response = await self.client.fetch(url)
        print('meu ovo 5')
        print('xxx: ',response)

        response.raise_for_status()

        return response
