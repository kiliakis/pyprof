from functools import wraps
import time
import inspect


def timeit(classname=''):
    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            ts = time.time()
            result = f(*args, **kw)
            te = time.time()

            filename = inspect.stack()[1].filename
            key = filename + '.' + f.__name__
            if classname:
                key = classname + '.' + key
            if(key not in timeit.times):
                timeit.times[key] = []
            timeit.times[key].append((te - ts) * 1000)
            return result
        return timed
    return decorator


timeit.times = {}


def report(skip=0):
    import numpy as np
    total_time = sum(sum(x[skip:]) for x in timeit.times.values())
    for k, v in sorted(timeit.times.items()):
        print('[%s] Calls: %d, Average time: %.3f ms, Global Percentage: %.2f %%'
              % (k, len(v), np.mean(v[skip:]), 100.0 * np.sum(v[skip:]) / total_time))
