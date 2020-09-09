from api_tests.config_files import config
import pytest
import random


@pytest.mark.usefixtures("setup")
class TestOauthErrorConditionsSuite:
    """ A Simple test suit to generate error conditions and ensure the responses are as expected """

    @pytest.mark.apm_801
    @pytest.mark.errors
    @pytest.mark.authorize_endpoint
    @pytest.mark.parametrize('request_data', [
        # condition 1: invalid redirect uri
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'redirect_uri is invalid'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'redirect_uri': f'{config.REDIRECT_URI}/invalid',  # invalid redirect uri
                'response_type': 'code',
                'state': random.getrandbits(32)
            },
        },

        # condition 2: missing redirect uri
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'redirect_uri is missing'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'response_type': 'code',
                'state': random.getrandbits(32)
            },
        },

        # condition 3: invalid client id
        {
            'expected_status_code': 401,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': "client_id is invalid"
            },
            'params': {
                'client_id': 'THISisANinvalidCLIENTid12345678',  # invalid client id
                'redirect_uri': config.REDIRECT_URI,
                'response_type': 'code',
                'state': random.getrandbits(32)
            },
        },

        # condition 4: missing client id
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'client_id is missing'
            },
            'params': {
                'redirect_uri': config.REDIRECT_URI,
                'response_type': 'code',
                'state': random.getrandbits(32)
            },
        },

        # condition 5: invalid response type
        {
            'expected_status_code': 400,
            'expected_response': {
                'ErrorCode': 'invalid_request',
                'Error': 'response_type is invalid'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'redirect_uri': config.REDIRECT_URI,
                'response_type': 'invalid',  # invalid response type
                'state': random.getrandbits(32)
            },
        },

        # condition 6: missing response type
        {
            'expected_status_code': 400,
            'expected_response': {
                'ErrorCode': 'invalid_request',
                'Error': 'response_type is missing'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'redirect_uri': config.REDIRECT_URI,
                'state': random.getrandbits(32)
            },
        }
    ])
    def test_authorization_error_conditions(self, request_data: dict):
        assert self.oauth.check_endpoint('GET', 'authorize', **request_data)

    @pytest.mark.apm_801
    @pytest.mark.errors
    @pytest.mark.token_endpoint
    @pytest.mark.parametrize('request_data', [
        # condition 1: invalid grant type
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'invalid grant_type'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'client_secret': config.CLIENT_SECRET,
                'redirect_uri': config.REDIRECT_URI,
                'grant_type': 'invalid',
            },
        },

        # condition 2: missing grant_type
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'The request is missing a required parameter : grant_type'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'client_secret': config.CLIENT_SECRET,
                'redirect_uri': config.REDIRECT_URI,
            },
        },

        # condition 3: invalid client id
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'invalid client_id'
            },
            'params': {
                'client_id': 'THISisANinvalidCLIENTid12345678',
                'client_secret': config.CLIENT_SECRET,
                'redirect_uri': config.REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
        },

        # condition 4: missing client_id
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'The request is missing a required parameter : client_id'
            },
            'params': {
                'client_secret': config.CLIENT_SECRET,
                'redirect_uri': config.REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
        },

        # condition 5: invalid redirect uri
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'invalid redirect_uri'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'client_secret': config.CLIENT_SECRET,
                'redirect_uri': f'{config.REDIRECT_URI}/invalid',
                'grant_type': 'authorization_code',
            },
        },

        # condition 6: missing redirect_uri
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'The request is missing a required parameter : redirect_uri'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'client_secret': config.CLIENT_SECRET,
                'grant_type': 'authorization_code',
            },
        },

        # condition 7: invalid client secret
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'invalid secret_id'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'client_secret': 'ThisSecretIsInvalid',
                'redirect_uri': config.REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
        },

        # condition 8: missing client secret
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'The request is missing a required parameter : secret_id'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'redirect_uri': config.REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
        },
    ])
    def test_token_error_conditions(self, request_data: dict):
        request_data['params']['code'] = self.oauth.get_authenticated()
        assert self.oauth.check_endpoint('POST', 'token', **request_data)

    @pytest.mark.errors
    @pytest.mark.parametrize('request_data', [
        # condition 1: invalid code
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'invalid code'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'client_secret': config.CLIENT_SECRET,
                'redirect_uri': config.REDIRECT_URI,
                'grant_type': 'authorization_code',
                'code': 'ThisIsAnInvalidCode'
            },
        },

        # condition 2: missing code
        {
            'expected_status_code': 400,
            'expected_response': {
                'error': 'invalid_request',
                'error_description': 'The request is missing a required parameter : code'
            },
            'params': {
                'client_id': config.CLIENT_ID,
                'client_secret': config.CLIENT_SECRET,
                'redirect_uri': config.REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
        },
    ])
    def test_token_endpoint_with_invalid_authorization_code(self, request_data: dict):
        assert self.oauth.check_endpoint('POST', 'token', **request_data)
