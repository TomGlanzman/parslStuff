import parsl
from parsl.tests.configs.htex_local_alternate import fresh_config
def exiting_retry_handler(*args):
    print("In exiting_retry_handler - forcing main thread to exit")
    # this is horrifying.
    import threading
    import ctypes
    ctypes.pythonapi.PyThreadState_SetAsyncExc(
           ctypes.c_long(threading.main_thread().ident),
           ctypes.py_object(RuntimeError)
           )
    print("In exiting_retry_handler - passed internal block")
    return 100
config = fresh_config()
config.retries = 0
config.retry_handler = exiting_retry_handler
@parsl.python_app
def my_app(succeed):
    if succeed:
        return None
    else:
        raise RuntimeError("my_app deliberate fail")
parsl.load(config)
print("App 1")
f1 = my_app(True)
f1.result()
print("App 2")
f2 = my_app(False)
f2.exception()
print("App 3")
f3 = my_app(True)
f3.result()
