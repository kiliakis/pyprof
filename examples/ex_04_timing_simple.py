import numpy as np

from pyprof import timing
timing.mode = 'timing'  # other modes available: 'disabled', 'line_profiler'
num = 10000

# Method 1, wrapper


@timing.timeit(filename='example.py', classname='', key='foo')
def foo(num):
    return np.sum(np.random.randn(num))


a = foo(num)
# ----------

# Method 2, code region
with timing.timed_region('code_region') as tr:
    a = np.sum(np.random.randn(num))
# ----------

# Method 3, start/ stop
timing.start_timing('start_stop')
b = np.sum(np.random.randn(num))
timing.stop_timing()
# ----------

timing.report()