import json

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

from jsonschema import RefResolver
from asynctest import patch, Mock

from async_pluct.resource import Resource, ObjectResource, ArrayResource
from async_pluct.session import Session
from async_pluct.schema import Schema


class BaseTestCase(AioHTTPTestCase):

    async def setUpAsync(self):
        self.session = Session()

    async def get_application(self):
        return web.Application()

    def resource_from_data(self, url, data=None, schema=None, response=None):
        resource = Resource.from_data(
            url=url, data=data, schema=schema, session=self.session,
            response=response)
        return resource

    def resource_from_response(self, response, schema):
        resource = Resource.from_response(
            response, session=self.session, schema=schema)

        return resource


class ResourceInitTestCase(BaseTestCase):

    def test_blocks_init_of_base_class(self):
        with self.assertRaises(NotImplementedError):
            Resource()


class ResourceTestCase(BaseTestCase):

    async def setUpAsync(self):
        await super().setUpAsync()

        self.data = {
            "name": "repos",
            "platform": "js",
        }
        self.raw_schema = {
            'type': "object",
            'required': ["platform"],
            'title': "some title",
            'properties': {
                'name': {'type': 'string'},
                'platform': {'type': 'string'}
            },
            'links': [
                {
                    "href": "/apps/{name}/log",
                    "method": "GET",
                    "rel": "log"
                },
                {
                    "href": "/apps/{name}/env",
                    "method": "GET",
                    "rel": "env"
                }
            ]}
        self.schema = Schema(
            href="url.com", raw_schema=self.raw_schema, session=self.session)

        self.url = "http://app.com/content"

        self.result = self.resource_from_data(
            url=self.url, data=self.data, schema=self.schema)

    def test_get_should_returns_a_resource(self):
        self.assertIsInstance(self.result, Resource)

    def test_missing_attribute(self):
        with self.assertRaises(AttributeError):
            self.result.not_found

    def test_str(self):
        expected = "<Pluct ObjectResource %s>" % self.data
        self.assertEqual(expected, str(self.result))

    def test_data(self):
        self.assertEqual(self.data, self.result.data)

    def test_response(self):
        self.assertEqual(self.result.response, None)

    def test_iter(self):
        iterated = [i for i in self.result]
        self.assertEqual(iterated, list(self.data.keys()))

    def test_schema(self):
        self.assertEqual(self.schema.url, self.result.schema.url)

    @unittest_run_loop
    async def test_is_valid_schema_error(self):
        old = self.result.schema['required']
        try:
            self.result.schema['required'] = ["ble"]
            self.assertFalse(await self.result.is_valid())
        finally:
            self.result.schema.required = old

    @unittest_run_loop
    async def test_is_valid_invalid(self):
        data = {
            'doestnotexists': 'repos',
        }
        result = self.resource_from_data('/url', data=data, schema=self.schema)
        self.assertFalse(await result.is_valid())

    @unittest_run_loop
    async def test_is_valid(self):
        self.assertTrue(await self.result.is_valid())

    def test_resolve_pointer(self):
        self.assertEqual(self.result.resolve_pointer("/name"), "repos")

    def test_resource_should_be_instance_of_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_resource_should_be_instance_of_schema(self):
        self.assertIsInstance(self.result, Resource)

    @patch('async_pluct.resources.validate')
    @unittest_run_loop
    async def test_is_valid_call_validate_with_resolver_instance(self, mock_validate):
        await self.result.is_valid()
        self.assertTrue(mock_validate.called)

        resolver = mock_validate.call_args[-1]['resolver']
        self.assertIsInstance(resolver, RefResolver)

        http_handler, https_handler = list(resolver.handlers.values())
        self.assertEqual(http_handler, self.result.session_request_json)
        self.assertEqual(https_handler, self.result.session_request_json)

    @unittest_run_loop
    async def test_session_request_json(self):
        mock_request_return = Mock()
        mock_request_return.body = json.dumps({'fake': 'json'})
        with patch.object(self.result.session, 'request') as mock_request:
            mock_request.return_value = mock_request_return

            result = await self.result.session_request_json(self.url)
            self.assertTrue(mock_request.called)
            self.assertEqual(result, {'fake': 'json'})


class ParseResourceTestCase(BaseTestCase):

    def setUp(self):
        super(ParseResourceTestCase, self).setUp()

        self.item_schema = {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer'
                }
            },
            'links': [{
                "href": "http://localhost/foos/{id}/",
                "method": "GET",
                "rel": "item",
            }]
        }

        self.raw_schema = {
            'title': "title",
            'type': "object",

            'properties': {
                'objects': {
                    'type': 'array',
                    'items': self.item_schema,
                },
                'values': {
                    'type': 'array'
                }
            }
        }
        self.schema = Schema(
            href="url.com", raw_schema=self.raw_schema, session=self.session)

    def test_wraps_array_objects_as_resources(self):
        data = {
            'objects': [
                {'id': 111}
            ]
        }
        app = self.resource_from_data(
            url="appurl.com", data=data, schema=self.schema)
        item = app['objects'][0]
        self.assertIsInstance(item, ObjectResource)
        self.assertEqual(item.data['id'], 111)
        self.assertEqual(item.schema, self.item_schema)

    def test_eq_operators(self):
        data = {
            'objects': [
                {'id': 111}
            ]
        }
        app = self.resource_from_data(
            url="appurl.com", data=data, schema=self.schema)

        self.assertDictEqual(data, app)

    def test_wraps_array_objects_as_resources_even_without_items_key(self):
        data = {
            'values': [
                {'id': 1}
            ]
        }
        resource = self.resource_from_data(
            url="appurl.com", data=data, schema=self.schema)

        item = resource['values'][0]
        self.assertIsInstance(item, Resource)
        self.assertEqual(item.data['id'], 1)

    @patch('async_pluct.session.http_client')
    def test_doesnt_wrap_non_objects_as_resources(self, get):
        data = {
            'values': [
                1,
                'string',
                ['array']
            ]
        }
        resource_list = self.resource_from_data(
            url="appurl.com", data=data, schema=self.schema)
        values = resource_list['values']

        self.assertEqual(values, data['values'])


class FromResponseTestCase(BaseTestCase):

    def setUp(self):
        super(FromResponseTestCase, self).setUp()

        self._response = Mock()
        self._response.request.url = 'http://example.com'

        content_type = 'application/json; profile=http://example.com/schema'
        self._response.headers = {
            'content-type': content_type
        }
        self.schema = Schema('/', raw_schema={}, session=self.session)

    @unittest_run_loop
    async def test_should_return_resource_from_response(self):
        self._response.body = '{}'.encode('utf-8')
        returned_resource = self.resource_from_response(
            self._response, schema=self.schema)
        self.assertEqual(returned_resource.url, 'http://example.com')
        self.assertEqual(returned_resource.data, {})

    @unittest_run_loop
    async def test_should_return_resource_from_response_with_no_json_data(self):
        self._response.body = b"{-}"
        returned_resource = self.resource_from_response(
            self._response, schema=self.schema)
        self.assertEqual(returned_resource.url, 'http://example.com')
        self.assertEqual(returned_resource.data, {})

    @unittest_run_loop
    async def test_should_return_resource_from_response_with_response_data(self):
        self._response.body = '{}'.encode('utf-8')
        returned_resource = self.resource_from_response(
            self._response, schema=self.schema)
        self.assertEqual(returned_resource.response, self._response)
        self.assertEqual(returned_resource.response.headers,
                         self._response.headers)

    @unittest_run_loop
    async def test_resource_with_an_array_without_schema(self):
        data = {
            'units': [
                {'name': 'someunit'}
            ],
            'name': 'registry',
        }
        s = Schema(
            href='url',
            raw_schema={
                'title': 'app schema',
                'type': 'object',
                'required': ['name'],
                'properties': {'name': {'type': 'string'}}
            },
            session=self.session)
        response = self.resource_from_data("url", data, s)
        self.assertDictEqual(data, response.data)


class ResourceFromDataTestCase(BaseTestCase):

    @unittest_run_loop
    async def test_should_create_array_resource_from_list(self):
        data = []
        resource = self.resource_from_data('/', data=data)
        self.assertIsInstance(resource, ArrayResource)
        self.assertEqual(resource.url, '/')
        self.assertEqual(resource.data, data)
        expected = "<Pluct ArrayResource %s>" % resource.data
        self.assertEqual(expected, str(resource))

    @unittest_run_loop
    async def test_should_create_object_resource_from_dict(self):
        data = {}
        resource = self.resource_from_data('/', data=data)
        self.assertIsInstance(resource, ObjectResource)
        self.assertEqual(resource.url, '/')
        self.assertEqual(resource.data, data)
