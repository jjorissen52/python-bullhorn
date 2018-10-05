class HTTPError(BaseException):
    pass


class APICallError(BaseException):
    pass


class APIErrorResponse(BaseException):
    pass


class APIAuthError(BaseException):
    pass


class ImproperlyConfigured(BaseException):
    pass