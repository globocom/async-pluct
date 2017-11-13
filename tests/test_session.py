import json

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
from yarl import URL
from aiohttp import ClientResponse, ClientResponseError

from asynctest import patch, Mock, CoroutineMock, ANY
from async_pluct.session import Session


class SessionInitializationTestCase(AioHTTPTestCase):

    async def get_application(self):
        return web.Application()

    @unittest_run_loop
    async def test_keeps_timeout(self):
        session = Session(timeout=999)
        self.assertEqual(session.timeout, 999)

    @unittest_run_loop
    async def test_uses_requests_session_as_default_client(self):
        with patch('async_pluct.session.http_client') as client:
            Session()
            client.assert_called_with()

    @unittest_run_loop
    async def test_allows_custom_client(self):
        custom_client = CoroutineMock()
        session = Session(client=custom_client)
        self.assertEqual(session.client, custom_client)


class SessionRequestsTestCase(AioHTTPTestCase):

    async def get_application(self):
        return web.Application()

    async def setUpAsync(self):
        self.response = ClientResponse('get', URL('/'))
        self.response.status = 200
        self.mock_client = Mock()
        self.mock_client.fetch = CoroutineMock(return_value=self.response)

        self.session = Session()
        self.session.client = self.mock_client

    @unittest_run_loop
    async def test_delegates_request_to_client(self):
        await self.session.request('/')
        self.mock_client.fetch.assert_called_with(
            '/', method='GET', headers=ANY)

    @unittest_run_loop
    async def test_uses_default_timeout(self):
        self.session.timeout = 333
        await self.session.request('/')
        self.mock_client.fetch.assert_called_with(
            '/', method='GET', request_timeout=333, headers=ANY)

    @unittest_run_loop
    async def test_allows_custom_timeout_per_request(self):
        await self.session.request('/', timeout=999)
        self.mock_client.fetch.assert_called_with(
            '/', method='GET', request_timeout=999, headers=ANY)

    @unittest_run_loop
    async def test_applies_json_content_type_header(self):
        await self.session.request('/')
        self.mock_client.fetch.assert_called_with(
            '/', method='GET',
            headers={'content-type': 'application/json'})

    @unittest_run_loop
    async def test_allows_custom_content_type_header(self):
        custom_headers = {'content-type': 'application/yaml'}
        await self.session.request('/', headers=custom_headers)
        self.mock_client.fetch.assert_called_with(
            '/', method='GET', headers=custom_headers)

    @unittest_run_loop
    async def test_returns_response(self):
        response = await self.session.request('/')
        self.assertIs(response, self.response)

    @unittest_run_loop
    async def test_checks_for_bad_response(self):
        self.response.status = 404
        with self.assertRaises(ClientResponseError):
            await self.session.request('/')


class SessionResourceTestCase(AioHTTPTestCase):

    async def get_application(self):
        return web.Application()

    async def setUpAsync(self):
        self.schema_url = '/schema'

        self.response = CoroutineMock()
        self.response.headers = {
            'content-type': 'application/json; profile=%s' % self.schema_url
        }
        self.response.body = json.dumps({
            'fake': 'schema'
        })

        self.session = Session()

        patch.object(self.session, 'request').start()
        self.session.request.return_value = self.response

    async def tearDownAsync(self):
        patch.stopall()

    @patch('async_pluct.session.Resource.from_response')
    @patch('async_pluct.session.LazySchema')
    @unittest_run_loop
    async def test_creates_resource_from_response(self, LazySchema, from_response):  # noqa
        LazySchema.return_value = 'fake schema'

        await self.session.resource('/')

        LazySchema.assert_called_with(
            href=self.schema_url, session=self.session)

        from_response.assert_called_with(
            response=self.response, session=self.session, schema='fake schema')

    @patch('async_pluct.session.Resource.from_response')
    @patch('async_pluct.session.LazySchema')
    @unittest_run_loop
    async def test_creates_resource_from_response_missing_profile(self, LazySchema, from_response):  # noqa
        self.response.headers = {
            'content-type': 'application/json'
        }

        await self.session.resource('/')

        LazySchema.assert_not_called()

        from_response.assert_called_with(
            response=self.response, session=self.session, schema=None)

    @patch('async_pluct.session.Schema')
    @unittest_run_loop
    async def test_creates_schema_from_response(self, Schema):
        await self.session.schema('/')
        Schema.assert_called_with(
            '/',
            raw_schema=json.loads(self.response.body),
            session=self.session)
