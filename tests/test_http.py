from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp.client_reqrep import ClientResponse
from aiohttp import web
from asynctest import patch, CoroutineMock
from asyncio import Future

from async_pluct.http import http_client


async def hello_get_handler(request):
    return web.Response(text="GET Hello, world!")


async def hello_put_handler(request):
    return web.Response(text="PUT Hello, world!")


class BaseTestCase(AioHTTPTestCase):

    async def get_application(self):
        app = web.Application()
        app.router.add_get('/', hello_get_handler)
        app.router.add_put('/', hello_put_handler)
        return app

    async def setUpAsync(self):
        self.my_client = http_client()

    @unittest_run_loop
    async def test_http_client_get(self):
        result = await self.my_client.fetch(self.server.make_url('/'))
        self.assertEqual(result.body, b'GET Hello, world!')

    @unittest_run_loop
    async def test_http_client_put(self):
        args = {
            'method': 'put'
        }
        result = await self.my_client.fetch(self.server.make_url('/'), **args)
        self.assertEqual(result.body, b'PUT Hello, world!')

    @patch('async_pluct.http.AioHttpClient.request')
    @unittest_run_loop
    async def test_http_client_get_timeout(self, request_mock):
        args = {
            'request_timeout': '1000'
        }

        url = self.server.make_url('/')
        resp = ClientResponse('GET', url)
        resp._content = b'mock content'
        future = Future()
        future.set_result(resp)
        request_mock.return_value = future

        result = await self.my_client.fetch(url, **args)
        request_mock.assert_called_with('GET', url, read_timeout='1000')
        self.assertEqual(result.body, b'mock content')

    @patch('async_pluct.http.AioHttpClient.request')
    @unittest_run_loop
    async def test_http_client_get_with_headers(self, request_mock):
        args = {
            'headers': {
                'X-Request-ID': 20
            }
        }

        url = self.server.make_url('/')
        resp = ClientResponse('GET', url)
        resp._content = b'mock content'
        future = Future()
        future.set_result(resp)
        request_mock.return_value = future

        result = await self.my_client.fetch(url, **args)
        request_mock.assert_called_with('GET', url, headers={'X-Request-ID': 20})
        self.assertEqual(result.body, b'mock content')
