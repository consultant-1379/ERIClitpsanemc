from unityapi import UnityApi
import mock
import json
import logging.handlers
import unittest

class MockedRequestsResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.content = None
        self.headers = {
            'EMC-CSRF-TOKEN': 'xxxx'
        }
        if self.json_data is not None:
            self.content = json.dumps(json_data)
            self.headers['Content-type'] = 'application/json'

    def json(self):
        return self.json_data


class TestUnity(unittest.TestCase):
    logging_setup = False

    requests_expected = []
    mocked_responses = []

    def assertIsInstance(self, obj, cls):
        """
        Implementation of assertIsInstance (which is available in 2.7)
        """
        yes = isinstance(obj, cls)
        if not yes:
            self.fail("%s is type %s, should be %s" % (obj, type(obj), cls))


    @staticmethod
    def mocked_requests_request(method, url, **kwargs):
        if 'json' in kwargs:
            json = kwargs['json']
        else:
            json = None

        if len(TestUnity.requests_expected) == 0:
            raise Exception("No more request excepted, got %s %s %s" % (method, url, str(json)))

        request_expected = TestUnity.requests_expected.pop(0)

        if url != request_expected['url'] or method != request_expected['method'] or\
                cmp(json, request_expected['json']) != 0:
            url_same = url == request_expected['url']
            url_msg = "url_same=%s" % url_same
            if not url_same:
                expected_path = request_expected['url'].split('?')[0]
                actual_path = url.split('?')[0]
                path_same = expected_path == actual_path
                url_msg = url_msg + ", path_same=%s" % path_same
                if not path_same:
                    url_msg = url_msg + ", expected_path=%s, actual_path=%s" % (expected_path, actual_path)
                else:
                    expected_args = request_expected['url'].split('?')[1].split('&')
                    actual_args = url.split('?')[1].split('&')
                    if len(expected_args) != len(actual_args):
                        url_msg = url_msg + ", %s != %s" % (actual_args, expected_args)
                    else:
                        for index, expected_arg in enumerate(expected_args, 0):
                            actual_arg = actual_args[index]
                            if expected_arg != actual_arg:
                                url_msg = url_msg + ", %s != %s" % (expected_arg, actual_arg)
            method_same = method == request_expected['method']
            json_same = cmp(json, request_expected['json']) == 0
            raise Exception(
                "Unexpected request url compare=[%s] method_same=%s json_same=%s Got %s %s %s, expected %s %s %s" %\
                (
                    url_msg, method_same, json_same,
                    method, url, str(json),
                    request_expected['method'], request_expected['url'], str(request_expected['json'])
                )
            )

        mocked_response_data = TestUnity.mocked_responses.pop(0)
        return MockedRequestsResponse(mocked_response_data['json_data'], mocked_response_data['status_code'])

    def setUp(self):
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"

        self.logger = logging.getLogger("sanapitest")
        if not TestUnity.logging_setup:
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(ch)
            TestUnity.logging_setup = True

    def setUpUnity(self):
        self.unityapi = UnityApi(self.logger)
        self.unityapi.rest.unity.request = mock.MagicMock(name="request", side_effect=TestUnity.mocked_requests_request)

        # initialise will call login so we need to setup one response

        TestUnity.requests_expected = []
        TestUnity.mocked_responses = []

        self.addRequest(
            'GET',
            '/api/types/loginSessionInfo/instances',
            None,
            200,
            None
        )
        self.unityapi.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        TestUnity.requests_expected = []
        TestUnity.mocked_responses = []

    def addRequest(self, method, endpoint, json_in, status_code, json_out):

        TestUnity.requests_expected.append(
            {
                'method': method,
                'url': "https://%s%s" % (self.spa, endpoint),
                'json': json_in
            }
        )

        TestUnity.mocked_responses.append(
            {
                'status_code': status_code,
                'json_data': json_out
            }
        )


