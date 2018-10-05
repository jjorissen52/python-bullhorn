import unittest
from .pipeline import execution_pipeline
from bullhorn.cache import cache
from bullhorn import settings


def do_thing_before(params):
    params['arg1'] = 'this argument is always changed'
    return params


def do_thing_after(response):
    response['added'] = 'yup'
    return response


def handle_error(e):
    print(f"oh no, Bob! {e}")
    return False


class MyException(BaseException):
    pass


class TestPipeline(unittest.TestCase):

    @classmethod
    def setUp(cls):
        error_handlers = [
            {"exception_class": MyException, "handler": handle_error},
            {"exception_class": TypeError, "handler": handle_error},
        ]

        class A:

            @execution_pipeline(pre=[do_thing_before])
            def __init__(self, arg1='okay'):
                self.stored = arg1

            @execution_pipeline(pre=[do_thing_before], post=[do_thing_after])
            def fun_boys(self, arg1, arg4, arg2, arg3, thing=None):
                print(arg1, arg2, arg3, thing)
                return dict()

            @execution_pipeline(pre=[do_thing_before], post=[do_thing_after], error=error_handlers)
            def fun_boys2(self, arg1, arg4, arg2, arg3, thing=None):
                raise MyException('Something went wrong!')

            @execution_pipeline(error=error_handlers, cache=cache)
            def fun_boys3(self, arg1, arg4, arg2, arg3, thing=None):
                return 400

        cls.A = A

    def test_pre_execution_pipeline(self):
        a = self.A('sup')
        self.assertFalse(a.stored == 'sup')
        self.assertTrue(a.stored == 'this argument is always changed')

    def test_post_execution_pipeline(self):
        a = self.A()
        self.assertTrue(a.fun_boys(1, 2, 3, 4, 5)['added'] == 'yup')

    def test_error_pipeline(self):
        a = self.A()
        self.assertFalse(a.fun_boys2())  # handles TypeError
        self.assertFalse(a.fun_boys2(1, 2, 3, 4, 5))  # handles MyException

    def test_cache_pipeline(self):
        a = self.A()
        if settings.USE_CACHING:
            cache.set("fun_boys3:{'thing':_5,_'arg1':_1,_'arg4':_2,_'arg2':_3,_'arg3':_4}", 200, 5)
            self.assertEqual(a.fun_boys3(1, 2, 3, 4, 5), 200)
        else:
            self.assertEqual(a.fun_boys3(1, 2, 3, 4, 5), 400)



