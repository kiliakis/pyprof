import numpy as np
import time
from pyprof import timing
num = 10000

# Method 1, function wrapper, profile entire function
@timing.timeit(key='foo')
def foo(num):
    return np.sum(np.random.randn(num))

start_t = time.time()

for _ in range(10):
    a = foo(num)

    # Method 2, profile a code region
    with timing.timed_region('code_region') as tr:
        b = np.sum(np.random.randn(num))

    # Method 3, start/ stop
    timing.start_timing('start_stop')
    c = np.sum(np.random.randn(num))
    timing.stop_timing()

    d = a+b+c

end_t = time.time()
total_t = end_t - start_t

# Prints report to stdout
timing.report()

# Write report to file
timing.report(out_file='timing-report.txt')

# Pass total time (in ms), in order to see contribution of non-profiled regions
timing.report(total_time=total_t*1e3)

# Sometimes the first call might take longer than the remaining, so it can be excluded
timing.report(skip=1)