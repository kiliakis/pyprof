A collection of python profiling utilities. 

## Contents
* mpiprof.py
* papiprof.py
* perf_deluxe.py
* timing.py

## Documentation and Usage Examples: timing.py
```python
import numpy as np

from pyprof import timing
timing.mode = 'timing'  # other modes available: 'disabled', 'line_profiler'
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


## Documentation and Usage Examples: papiprof.py

* Required packages: papi-tools
* try `papi_avail` for a list of all available events
* If none is available, try this fix: https://stackoverflow.com/questions/32308175/papi-avail-no-events-available

```python
import sys
import numpy as np
from pyprof.papiprof import PAPIProf
import random

n_turns = 5
size = 10 * 1024**2

A = np.random.randn(size)
print('Array A size: {:.0f} Mb'.format(sys.getsizeof(A)/ (1024**2)))

papiprof = PAPIProf(metrics=['IPC', 'L2_MISS_RATE', 'L3_MISS_RATE', 'BRANCH_MSP_RATE'])

papiprof.list_metrics()
papiprof.list_avail_metrics()

idx = np.arange(size)
for r in range(n_turns):
    print('seq_access: step {}/{}'.format(r, n_turns))
    result = 0.
    papiprof.start_counters()
    for i in idx:
        if i % 3 == 0:
            result += A[i]
    papiprof.stop_counters()


idx = np.arange(size)
random.shuffle(idx)
papiprof.start_counters()
for r in range(n_turns):
    print('random_access: step {}/{}'.format(r, n_turns))
    result = 0.        
    for i in idx:
        if i % 3 == 0:
            result += A[i]
papiprof.stop_counters()

papiprof.report_timing()
papiprof.report_metrics()


```

## Documentation and Usage Examples: perfdeluxe

* Requires: linux-perf (linux-tools-common)
* Make it executable: `chmod +x perfdeluxe`
* Run as: `./perfdeluxe ls -la /usr/bin`



## Dependencies
papi, linux-perf