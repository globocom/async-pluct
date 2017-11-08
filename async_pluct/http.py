try:
    from tornado.httpclient import AsyncHTTPClient

    http_client = AsyncHTTPClient
except:
    from aiohttp import ClientSession

    class AioHttpClient(ClientSession):
        async def fetch(self, url, **kwargs):
            method = kwargs.pop('method', 'GET')
            timeout = kwargs.pop('request_timeout')

            if timeout:
                kwargs['read_timeout'] = timeout

            async with self.request(method, url, **kwargs) as request:
                response = await request
                response.body = response.content
                return response

    http_client = AioHttpClient
