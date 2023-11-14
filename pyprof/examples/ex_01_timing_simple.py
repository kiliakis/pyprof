import numpy as np

from pyprof import timing
num = 10000

# Method 1, function wrapper, profile entire function
@timing.timeit(key='foo')
def foo(num):
    return np.sum(np.random.randn(num))

def bar(num):
    return np.sum(np.random.randn(num))

a = foo(num)
# ----------

# Method 2, profile a code region
with timing.timed_region('code_region') as tr:
    a = np.sum(np.random.randn(num))
# ----------

# Method 3, start/ stop
timing.start_timing('start_stop')
b = np.sum(np.random.randn(num))
timing.stop_timing()
# ----------

# Method 4, overwrite function
bar = timing.timeit(key='bar')(bar)

b = bar(num)

timing.report()