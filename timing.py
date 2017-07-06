# Requires pypapi
# Can be used as:
# @papiprof('cache')
# def myfunction():
#    ...
#    ...
#
# myfunction()

from functools import wraps


def timeit(f):
    import time
    @wraps(f)
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print('%s %2.2f ms' % (f.__name__, (te - ts) * 1000))
        return result
    return timed
