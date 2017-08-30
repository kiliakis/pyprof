# Requires pypapi
# Can be used as:
# @papiprof('cache')
# def myfunction():
#    ...
#    ...
#
# myfunction()

from functools import wraps
import time


def timeit(filename='', classname=''):
    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            ts = time.time()
            result = f(*args, **kw)
            te = time.time()
            key = f.__name__
            if classname:
                key = classname + '.' + key
            if filename:
                key = filename + '.' + key
            # key = filename + '.' + classname + '.' + f.__name__
            if(key not in timeit.times):
                timeit.times[key] = []
            timeit.times[key].append((te - ts) * 1000)
            # print('%s %2.2f ms' % (key, (te - ts) * 1000))
            return result
        return timed
    return decorator


timeit.times = {}
