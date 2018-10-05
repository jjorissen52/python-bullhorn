import configparser
import os
import logging

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_CONF_FILE = os.environ.get('BULLHORN_CONF_FILE')
ENV_CONF_REGION = os.environ.get('BULLHORN_CONF_REGION')
DEBUG = bool(os.environ.get('BULLHORN_DEBUG'))
if ENV_CONF_FILE:
    CONF_FILE = ENV_CONF_FILE
else:
    CONF_FILE = ''
    logging.warn('Please make sure you set the BULLHORN_CONF_FILE '
                 'environment variable. API will not function without it.')
CONF_REGION = ENV_CONF_REGION if ENV_CONF_REGION else 'bullhorn'
DEFAULTS = {
    'client_id': None,
    'client_secret': None,
    'username': None,
    'password': None,
    'login_url': 'https://auth.bullhornstaffing.com/oauth/authorize',
    'grant_url': 'https://auth.bullhornstaffing.com/oauth/token',
    'rest_login_url': 'https://rest.bullhornstaffing.com/rest-services/login',
    'api_version': '*',
    'cache_backend': None,
    'cache_host': None,
    'cache_port': None,
    'cache_lifetime': 0,
    'debug': DEBUG,
}


def read_config(keys):
    """
    We don't want a failed import for bad config, we just want to set everything that is not in the config file/region
    set to None
    :param keys: (iterable) default keys to set to None
    :return:
    """
    config = configparser.ConfigParser(defaults=DEFAULTS)
    config.read(CONF_FILE)
    if not config.has_section(CONF_REGION):
        config.add_section(CONF_REGION)

    parameters = {key: config.get(CONF_REGION, key) for key in keys}
    parameters.update({'config': config})
    return parameters


config_dict = read_config(DEFAULTS.keys())

CLIENT_ID = config_dict.get('client_id')
CLIENT_SECRET = config_dict.get('client_secret')
USERNAME = config_dict.get('username')
PASSWORD = config_dict.get('password')
LOGIN_URL = config_dict.get('login_url')
GRANT_URL = config_dict.get('grant_url')
REST_LOGIN_URL = config_dict.get('rest_login_url')
API_VERSION = config_dict.get('api_version')
CACHE_BACKEND = config_dict.get('cache_backend')
USE_CACHING = bool(CACHE_BACKEND)
CACHE_HOST = config_dict.get('cache_host')
CACHE_PORT = config_dict.get('cache_port')
CACHE_LIFETIME = int(config_dict.get('cache_lifetime') if config_dict.get('cache_lifetime') else 0)
DEBUG = config_dict.get('debug')
