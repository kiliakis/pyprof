A collection of python profiling utilities. 

## Contents
* timing.py

## Documentation and Usage Examples: timing.py
```python
import numpy as np

from pyprof import timing
num = 100

# Method 1, wrapper
@timing.timeit(filename='example.py', classname='', key='foo')
def foo(num):
    return np.sum(np.random.randn(num))
a = foo(num)
# ----------

# Method 2, code region
with timing.timed_region(key='code_region') as tr:
    a = np.sum(np.random.randn(num))
# ----------

# Method 3, start/ stop
timing.start_timing('start_stop')
b = np.sum(np.random.randn(num))
timing.stop_timing()
# ----------

timing.report()

''' Example Output
function    total_time(sec) time_per_call(ms)   std(%)  calls   global_percentage
code_region 0.000           0.355               0.00    1       31.38
foo         0.000           0.416               0.00    1       36.81
start_stop  0.000           0.360               0.00    1       31.82
Other       0.000           0.000               0.00    1       0.00
total_time  0.001           1.132               0.00    1       100.00
'''

```

## Examples
See the examples for more details.

