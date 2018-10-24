import urllib
import time
import requests
import json

from pipeline import execution_pipeline

from bullhorn.pipeline_methods import error, post
from bullhorn.api.exceptions import APIAuthError

from bullhorn import settings
from bullhorn import cache


class BullhornAuthClient:

    def __init__(self, username=settings.USERNAME, password=settings.PASSWORD,
                 client_id=settings.CLIENT_ID, client_secret=settings.CLIENT_SECRET,
                 login_url=settings.LOGIN_URL, grant_url=settings.GRANT_URL, rest_login_url=settings.REST_LOGIN_URL,
                 api_version=settings.API_VERSION,
                 default_headers=None, raise_errors=True,
                 use_caching=settings.USE_CACHING, leader=True):
        self.client_id = client_id
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.login_url = f'{login_url.strip("/")}'
        self.grant_url = f'{grant_url.strip("/")}'
        self.rest_login_url = f'{rest_login_url.strip("/")}'
        self.api_version = api_version
        self.raise_errors = raise_errors
        self.use_caching = use_caching
        self.auth_details = dict()
        self.default_headers = default_headers if default_headers else {
            'user-agent': f'python-bullhorn {self.username}',
            # 'Content-Type': 'application/x-www-form-urlencoded',
            # 'Transfer-Encoding': 'gzip',
        }
        self.rest_url = None
        self.leader = leader
        self.global_timeout = 20

    @property
    def auth_details(self):
        """
        getter for auth_details. used for maintaining local and shared state
        :return:
        """
        if not self.use_caching:
            return self.__auth_details
        auth_details = self.__auth_details if self.__auth_details else cache.get('auth_details', default={})
        return auth_details

    @auth_details.setter
    def auth_details(self, arg):
        self.__auth_details = arg
        if self.use_caching and not cache.get('auth_details'):
            cache.set('auth_details', arg, settings.CACHE_LIFETIME)

    @execution_pipeline(error=[{"exception_class": APIAuthError, "handler": error.handle_api_auth_error}])
    def authenticate(self, headers=None):
        """
        Authenticate against their provider for an OAuth token.

        :raise_errors: (kwarg: True) Raise an error on authentication failure
        :return: (dict) {"access_token:" <jwt_access_token>, "token_type": <token_type>, "expires_in": <seconds> }
        """
        headers = headers if headers else self.default_headers
        login_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "username": self.username,
            "password": self.password,
            "action": "Login",
        }
        response = requests.post(self.login_url, params=login_params)
        url_params = requests.utils.urlparse(response.url).query
        code = urllib.parse.parse_qs(url_params).get("code")

        grant_params = {
            "client_secret": self.client_secret,
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "code": code
        }
        response = requests.post(self.grant_url, params=grant_params, timeout=self.global_timeout)
        # contains the token to authenticate against the rest endpoint, as well as the rest endpoint itself
        # print(self.grant_url)
        login_token = json.loads(response.text)
        # print(login_token)
        self.auth_details = self.get_api_token(login_token)
        return response

    @execution_pipeline(post=[post.raise_error_keys])
    def get_api_token(self, login_token):
        params = {
            'access_token': login_token['access_token'],
            'version': self.api_version,
        }
        response = requests.get(self.rest_login_url, params=params)
        rest_token = json.loads(response.text)
        rest_token.update({
            'bh_rest_token': rest_token.get("BhRestToken", None),
            'rest_url': rest_token.get("restUrl", None),
            'expires_in': login_token.get("expires_in", 420),
            'expiration_time': time.time() + login_token.get("expires_in", 420),
        })
        return rest_token
