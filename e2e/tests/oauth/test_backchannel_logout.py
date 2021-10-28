import os

from selenium.webdriver.chrome import options
import pytest
import aiohttp
from selenium.webdriver.chrome.options import Options
from time import time
from typing import Dict, Optional
from uuid import UUID, uuid4
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from api_test_utils.oauth_helper import OauthHelper
from api_test_utils.apigee_api_trace import ApigeeApiTraceDebug
from api_test_utils.apigee_api_apps import ApigeeApiDeveloperApps
from api_test_utils.apigee_api_products import ApigeeApiProducts
from e2e.scripts import config

def get_env(variable_name: str) -> str:
    """Returns a environment variable"""
    try:
        var = os.environ[variable_name]
        if not var:
            raise RuntimeError(f"Variable is null, Check {variable_name}.")
        return var
    except KeyError:
        raise RuntimeError(f"Variable is not set, Check {variable_name}.")

@pytest.fixture
def webdriver():
    return webdriver.Remote(command_executor='http://127.0.0.1:4444/wd/hub', desired_capabilities=[DesiredCapabilities.CHROME, DesiredCapabilities.EDGE, DesiredCapabilities.FIREFOX])

def create_logout_token(
    test_app: ApigeeApiDeveloperApps,
    override_claims: Optional[Dict[str, str]] = None,
    override_kid: Optional[str] = None,
    ) -> Dict[str, str]:
    """Creates logout token. To be replaced with Mock OIDC"""
    logout_token_claims = {
        "aud": "9999999999",
        "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
        "sub": "9999999999",
        "iat": int(time()) - 10,
        "jti": str(uuid4()),
        "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
        "events": { "http://schemas.openid.net/event/backchannel-logout": {} }
    }

    if override_claims is not None:
        logout_token_claims = override_claims

    logout_token_kid = override_kid if override_kid is not None else "identity-service-tests-1" 

    logout_token_headers = {
        "kid": logout_token_kid,
        "typ": "JWT",
        "alg": "RS512",
    }
    
    id_token_private_key_path = get_env("ID_TOKEN_PRIVATE_KEY_ABSOLUTE_PATH")

    with open(id_token_private_key_path, "r") as f:
        contents = f.read()

    logout_token_jwt = test_app.oauth.create_id_token_jwt(
        algorithm="RS512",
        claims=logout_token_claims,
        headers=logout_token_headers,
        signing_key=contents,
    )

    return logout_token_jwt


@pytest.fixture(scope="function")
async def test_app():
    """Programmitcally create and destroy test app for each test"""
    apigee_product = ApigeeApiProducts()
    await apigee_product.create_new_product()
    await apigee_product.update_proxies([config.SERVICE_NAME])

    apigee_app = ApigeeApiDeveloperApps()

    await apigee_product.update_ratelimits(
        quota=60000,
        quota_interval="1",
        quota_time_unit="minute",
        rate_limit="1000ps",
    )

    await apigee_app.setup_app(
        api_products=[apigee_product.name],
        custom_attributes={
            "jwks-resource-url": "https://raw.githubusercontent.com/NHSDigital/identity-service-jwks/main/jwks/internal-dev/9baed6f4-1361-4a8e-8531-1f8426e3aba8.json"
        },
    )

    apigee_app.oauth = OauthHelper(apigee_app.client_id, apigee_app.client_secret, apigee_app.callback_url)

    api_service_name = get_env("SERVICE_NAME")

    await apigee_product.update_scopes(
        [f"urn:nhsd:apim:user-nhs-login:P9:{api_service_name}"]
    )

    yield apigee_app

    await apigee_app.destroy_app()


@pytest.mark.asyncio
class TestBackChannelLogout:
    """ A test suite for back-channel logout functionality"""
    async def get_access_token(self, webdriver):
        webdriver.get("google.com")

        #code = await self.oauth.get_authenticated_with_simulated_auth() 
        #print(code)
        #pytest.set_trace()
        # /oauth2-pr-251/authorize?client_id=Y2GdHRFXn3AzgOkSWWWgEIfuBZQ9rQAc&redirect_uri=https%3A%2F%2Fnhsd-apim-testing-internal-dev.herokuapp.com%2Fcallback&response_type=code&state=22c9b600-1d58-4556-9461-856e9d555121 
        auth_resp = await self.oauth.hit_oauth_endpoint(
            method="GET",
            endpoint="authorize",
            params={
                'client_id': self.oauth.client_id,
                'redirect_uri': 'https://identity.ptl.api.platform.nhs.uk/auth/realms/cis2-mock/protocol/openid-connect/auth',
                'response_type': 'code',
                'state': str(uuid4())
            }
        )

        body=BeautifulSoup(auth_resp["body"])
        action = body.form["action"]
        async with aiohttp.ClientSession() as session:

            async with session.post(action, skip_auto_headers=["User-Agent"],
                        headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0", "Content-Type": "application/x-www-form-urlencoded"}, 
                        data={"username": "aal1"}) as resp:
                print('body.form')
                print(body.form)
                print('resp.text')
                print(await resp.text())

        token_resp = await self.oauth.hit_oauth_endpoint(
            method="POST",
            endpoint="token",
            data={
                'client_id': self.oauth.client_id,
                'client_secret': self.oauth.client_secret,
                'grant_type': "authorization_code",
                'redirect_uri': self.oauth.redirect_uri,
                'code': code,
                '_access_token_expiry_ms': 5000
            }
        )

        return token_resp["body"]["access_token"]
    
    async def call_user_info(self, app, access_token):
        user_info_resp = await app.oauth.hit_oauth_endpoint(
            method="GET",
            endpoint="userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        return user_info_resp["status_code"]

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_backchannel_logout_happy_path(self, test_app):
        access_token = await self.get_access_token()

        # Test token can be used to access identity service
        assert await self.call_user_info(test_app, access_token) == 200

        # Mock back channel logout notification and test succesful logout response
        logout_token = create_logout_token(test_app)

        back_channel_resp = await test_app.oauth.hit_oauth_endpoint(
            method="POST",
            endpoint="backchannel_logout",
            data={"logout_token": logout_token}
        )

        assert back_channel_resp["status_code"] == 200

        # Test access token has been revoked
        user_info_resp = await test_app.oauth.hit_oauth_endpoint(
            method="GET",
            endpoint="userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert user_info_resp["status_code"] == 401

    #Request sends a JWT has missing or invalid claims of the following problems, returns a 400
    @pytest.mark.asyncio
    @pytest.mark.parametrize("claims,status_code,error_message", [
        ( # invalid aud claim
            {
                "aud": "invalid_aud_claim",
                "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
                "events": { "http://schemas.openid.net/event/backchannel-logout": {} }
            },
            400,
            "Invalid aud claim in JWT"
        ),
        ( # missing aud claim
            {
                "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
                "events": { "http://schemas.openid.net/event/backchannel-logout": {} }
            },
            400,
            "Invalid aud claim in JWT"
        ),
        ( # invalid iss claim
            {
                "aud": "9999999999",
                "iss": "invalid_iss_claim",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
                "events": { "http://schemas.openid.net/event/backchannel-logout": {} }
            },
            400,
            "Invalid iss claim in JWT"
        ),
        ( # missing iss claim
            {
                "aud": "9999999999",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
                "events": { "http://schemas.openid.net/event/backchannel-logout": {} }
            },
            400,
            "Invalid iss claim in JWT"
        ),
        ( # missing sid claim
            {
                "aud": "9999999999",
                "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "events": { "http://schemas.openid.net/event/backchannel-logout": {} }
            },
            400,
            "Invalid sid claim in JWT"
        ),
        ( # invalid events claim
            {
                "aud": "9999999999",
                "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
                "events": { "invalid_event_url": {} }
            },
            400,
            "Invalid events claim in JWT"
        ),
        ( # missing events claim
            {
                "aud": "9999999999",
                "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "sid": "08a5019c-17e1-4977-8f42-65a12843ea02"
            },
            400,
            "Invalid events claim in JWT"
        ),
        ( # present nonce claim
            {
                "aud": "9999999999",
                "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
                "sub": "9999999999",
                "iat": int(time()) - 10,
                "jti": str(uuid4()),
                "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
                "events": { "http://schemas.openid.net/event/backchannel-logout": {} },
                "nonce":"valid_nonce"
            },
            400,
            "Prohibited nonce claim in JWT"
        )
    ])
    async def test_claims(self, test_app, claims, status_code, error_message):
        access_token = await self.get_access_token()

        # Test token can be used to access identity service
        assert await self.call_user_info(test_app, access_token) == 200

        # Mock back channel logout notification with overridden claims
        logout_token = create_logout_token(test_app, override_claims=claims)

        # Submit logout token to back-channel logout endpoint
        back_channel_resp = await test_app.oauth.hit_oauth_endpoint(
            method="POST",
            endpoint="backchannel_logout",
            data={"logout_token": logout_token}
        )
    
        assert back_channel_resp["status_code"] == status_code
        assert back_channel_resp["body"]["error_description"] == error_message

    #Request sends JWT that cannot be verified returns a  400
    @pytest.mark.asyncio
    async def test_invalid_jwt(self, test_app):
        access_token = await self.get_access_token()

        # Test token can be used to access identity service
        assert await self.call_user_info(test_app, access_token) == 200

        # Mock back channel logout notification and test with invalid kid
        logout_token = create_logout_token(test_app, override_kid="invalid_kid")

        back_channel_resp = await test_app.oauth.hit_oauth_endpoint(
            method="POST",
            endpoint="backchannel_logout",
            data={"logout_token": logout_token}
        )

        assert back_channel_resp["status_code"] == 400
        assert back_channel_resp["body"]["error_description"] == "Unable to verify JWT"

    #Requests sends an logout token that does not exist in the session-id cache returns a 501
    @pytest.mark.asyncio
    async def test_sid_not_cached(self, test_app):
        logout_token = create_logout_token(test_app)

        back_channel_resp = await test_app.oauth.hit_oauth_endpoint(
            method="POST",
            endpoint="backchannel_logout",
            data={"logout_token": logout_token}
        )

        assert back_channel_resp["status_code"] == 501

    #Requests sends an logout token that does not match the session-id cache returns a 501
    @pytest.mark.asyncio
    async def test_cached_sid_does_not_match(self, test_app):
        claims_non_matching_sid = {
            "aud": "9999999999",
            "iss": "https://am.nhsdev.auth-ptl.cis2.spineservices.nhs.uk:443/openam/oauth2/realms/root/realms/oidc",
            "sub": "9999999999",
            "iat": int(time()) - 10,
            "jti": str(uuid4()),
            "sid": "12a5019c-17e1-4977-8f42-65a12843ea02",
            "events": { "http://schemas.openid.net/event/backchannel-logout": {} }
        }

        # Mock back channel logout notification and test with different sid
        logout_token = create_logout_token(test_app, override_claims=claims_non_matching_sid)

        back_channel_resp = await test_app.oauth.hit_oauth_endpoint(
            method="POST",
            endpoint="backchannel_logout",
            data={"logout_token": logout_token}
        )

        assert back_channel_resp["status_code"] == 501
