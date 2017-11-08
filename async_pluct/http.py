try:
    from tornado.httpclient import AsyncHTTPClient

    http_client = AsyncHTTPClient
except ImportError:
    from aiohttp import ClientSession

    class AioHttpClient(ClientSession):
        async def fetch(self, url, **kwargs):
            method = kwargs.pop('method', 'GET')
            timeout = kwargs.pop('request_timeout', None)

            if timeout:
                kwargs['read_timeout'] = timeout

            response = await self.request(method, url, **kwargs)
            async with response:
                response.body = await response.read()
                return response

    http_client = AioHttpClient
