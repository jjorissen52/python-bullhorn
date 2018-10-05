import functools
import sys

from bullhorn import helpers


class PipelineSetupError(BaseException):
    pass


class execution_pipeline:

    def __init__(self, pre=None, post=None, error=None, cache=None, cache_lifetime=600):
        """
        :param pre: function modifying the input of a method,
            should return a modifed set of the original *args and **kwargs
        :param post: function modifying the output of a method, should return a modified response object
        :param error: [{"exception_class": <ExceptionClass>, "handler": <HandlerFunc>,}, ]
        :param cache: {"cache": , "cache_lifetime":,}
        """
        self.pre = pre
        self.post = post
        if error:
            for e in error:
                if not isinstance(e, dict) and all(('exception_class' in e.keys(), 'handler' in e.keys(), )):
                    raise PipelineSetupError('execution_pipeline error kwarg must be a list of dicts: '
                                                 '[{"exception_class": <ExceptionClass>, "handler": <HandlerFunc>,}, ]')
        self.error = error
        self.cache = cache
        self.cache_lifetime = cache_lifetime

    def __call__(self, method):
        @functools.wraps(method)
        def decorated(*args, **kwargs):
            params = helpers.named_method_params(method, args, kwargs)
            cache_key = {key: params[key] for key in params if key != 'self'}  # params before pre
            local_cache_keys = [f'{method.__name__}:{cache_key}'.replace(' ', '_')]
            if self.pre:
                # we will check the cache for any key in cache_keys
                for func in self.pre:
                    modified_params = func(params)
                    params.update(modified_params)
                post_pre_key_params = {key: params[key] for key in params if key != 'self'}  # params after pre
                local_cache_keys.append(f'{method.__name__}:{post_pre_key_params}'.replace(' ', '_'))

            if self.cache:
                for key in local_cache_keys:
                    cached_obj = self.cache.get(key)
                    if cached_obj is not None:
                        return cached_obj

            if self.error:
                return self.error_handling(method, params)
            else:
                response = method(**params)

            if self.post:
                for func in self.post:
                    response = func(response)

            if self.cache:
                for key in local_cache_keys:
                    self.cache.set(key, response, self.cache_lifetime)

            return response
        return decorated

    def error_handling(self, method, params):
        """
        Check to see if the pipeline includes a handler for the exception we run into. If not, we raise the original
        exception.
        """
        try:
            response = method(**params)
        except (Exception, BaseException) as e:
            response = None
            for error_handler in self.error:
                if isinstance(e, error_handler["exception_class"]):
                    response = error_handler["handler"](e, response)
            if response is None:
                raise e
        return response
