from functools import wraps
import time
import inspect
import numpy as np


times = {}
start_time_stack = []
func_stack = []
excluded = ['lib_time']
mode = 'timing'
lp = None
# Modes available:
# 'line_profiler'
# 'disabled'
# 'timing'


def timeit(filename='', classname='', exclude=False):
    global times, excluded, disabled, mode

    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            if mode == 'disabled':
                return f(*args, **kw)
            elif mode == 'timing':
                ts = time.time()
                result = f(*args, **kw)
                te = time.time()

                if not filename:
                    _filename = inspect.stack()[1].filename.split('/')[-1]
                else:
                    _filename = filename
                key = _filename + '.' + f.__name__
                if classname:
                    key = classname + '.' + key

                # key = filename
                if(key not in times):
                    times[key] = []
                    if exclude:
                        excluded.append(key)

                times[key].append((te - ts) * 1000)

                if 'lib_time' not in times:
                    times['lib_time'] = []
                times['lib_time'].append((time.time() - te) * 1000)

                return result
            elif mode == 'line_profiler':
                from line_profiler import LineProfiler
                global lp
                if not lp:
                    lp = LineProfiler()
                lp_wrapper = lp(f)
                result = lp_wrapper(*args, **kw)
                return result
            else:
                raise RuntimeError('[timing.py:timeit] mode: %s not available' % mode)
        return timed
    return decorator


# timeit.times = {}


class timed_region:

    def __init__(self, region_name='', is_child_function=False):

        ls = time.time()
        global times, excluded, mode

        if mode == 'disabled':
            return
        elif mode == 'timing':
            if region_name:
                self.key = region_name
            else:
                parent = inspect.stack()[1]
                self.key = parent.filename.split('/')[-1]
                self.key = self.key + ':' + parent.lineno

            if (self.key not in times):
                times[self.key] = []

            if is_child_function == True:
                excluded.append(self.key)

            if 'lib_time' not in times:
                times['lib_time'] = []
            times['lib_time'].append((time.time() - ls) * 1000)
        else:
            raise RuntimeError('[timing:timed_region] mode: %s not available' % mode)

    def __enter__(self):
        ls = time.time()
        global times, excluded, mode

        if mode == 'disabled':
            return self
        elif mode == 'timing':

            times['lib_time'].append((time.time() - ls) * 1000)

            self.ts = time.time()

            return self
        else:
            raise RuntimeError('[timing:timed_region] mode: %s not available' % mode)

    def __exit__(self, type, value, traceback):
        te = time.time()
        global times, excluded, mode

        if mode == 'disabled':
            return
        elif mode == 'timing':
            times[self.key].append((te - self.ts) * 1000)

            times['lib_time'].append((time.time() - te) * 1000)
            return
        else:
            raise RuntimeError('[timing:timed_region] mode: %s not available' % mode)

def start_timing(funcname=''):
    global func_stack, start_time_stack, disabled, times, mode
    if mode == 'disabled':
        return
    elif mode == 'timing':
        ts = time.time()
        if funcname:
            key = funcname
        else:
            parent = inspect.stack()[1]
            key = parent.filename.split('/')[-1]
            key = key + ':' + parent.lineno
        func_stack.append(key)
        start_time_stack.append(time.time())
        if 'lib_time' not in times:
            times['lib_time'] = []
        times['lib_time'].append((time.time() - ts) * 1000)
    else:
        raise RuntimeError('[timing:timed_region] mode: %s not available' % mode)

def stop_timing(exclude=False):
    global times, start_time_stack, func_stack, excluded, mode
    if mode == 'disabled':
        return
    elif mode == 'timing':
        ts = time.time()

        elapsed = (time.time() - start_time_stack.pop()) * 1000
        key = func_stack.pop()
        if(key not in times):
            times[key] = []
            if exclude == True:
                excluded.append(key)
        times[key].append(elapsed)
        if 'lib_time' not in times:
            times['lib_time'] = []
        times['lib_time'].append((time.time() - ts) * 1000)
    else:
        raise RuntimeError('[timing:timed_region] mode: %s not available' % mode)

def report(skip=0, total_time=None):
    global times, excluded, mode

    if mode == 'disabled':
        return
    elif mode == 'timing':

        if isinstance(total_time, str):
            _total_time = sum(times[total_time][skip:])
            excluded.append(total_time)
        elif isinstance(total_time, float):
            _total_time = total_time
        else:
            _total_time = sum(sum(x[skip:])
                              for k, x in times.items() if k not in excluded)

        _total_time -= sum(times['lib_time'])

        otherPercent = 100.0
        otherTime = _total_time

        print('function\tcounter\taverage_value\tstd(%)\tcalls\tglobal_percentage')
        for k, v in sorted(times.items()):

            if k == 'lib_time':
                continue

            vSum = np.sum(v[skip:])
            vMean = vSum / len(v[skip:])
            vStd = np.std(v[skip:])
            vGPercent = 100 * vSum / _total_time

            if k not in excluded:
                otherPercent -= vGPercent
                otherTime -= vSum

            print('%s\t%s\t%.3lf\t%.2lf\t%d\t%.2lf'
                  % (k, 'times(ms)', vMean, 100.0 * vStd / vMean,
                     len(v), vGPercent))

        print('%s\t%s\t%.3lf\t%.2lf\t%d\t%.2lf'
              % ('Other', 'times(ms)', otherTime, 0.0, 1, otherPercent))
    elif mode == 'line_profiler':
        lp.print_stats()
    else:
        raise RuntimeError('[timing:report] mode: %s not available' % mode)