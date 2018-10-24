import logging


def handle_api_auth_error(e, response):
    logging.error(str(e))
    return response