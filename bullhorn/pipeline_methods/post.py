from bullhorn.api.exceptions import APIAuthError


def raise_error_keys(response):
    error_dict = None
    if isinstance(response, dict):
        error_dict = {key: response[key] for key in response.keys() if 'error' in key}
    if error_dict:
        raise APIAuthError(error_dict)
    else:
        return response