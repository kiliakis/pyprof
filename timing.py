from functools import wraps
try:
    from time import perf_counter as timer
except ImportError:
    from time import time as timer
    # from time import clock as timer
import inspect
import numpy as np
import sys

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


def timeit(filename='', classname='', key='', exclude=False):
    global times, excluded, disabled, mode

    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            if mode == 'disabled':
                return f(*args, **kw)
            elif mode == 'timing':
                ts = timer()
                result = f(*args, **kw)
                te = timer()

                if key == '':
                    if not filename:
                        _filename = inspect.stack()[1].filename.split('/')[-1]
                    else:
                        _filename = filename
                    _key = _filename + '.' + f.__name__
                    if classname:
                        _key = classname + '.' + _key
                else:
                    _key = key
                # key = filename
                if(_key not in times):
                    times[_key] = []
                    if exclude:
                        excluded.append(_key)

                times[_key].append((te - ts) * 1000)

                if 'lib_time' not in times:
                    times['lib_time'] = []
                times['lib_time'].append((timer() - te) * 1000)

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
                raise RuntimeError(
                    '[timing.py:timeit] mode: %s not available' % mode)
        return timed
    return decorator


# timeit.times = {}


class timed_region:

    def __init__(self, region_name='', is_child_function=False):
        global mode

        if mode == 'disabled':
            return
        elif mode == 'timing':
            ls = timer()
            global times, excluded
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
            times['lib_time'].append((timer() - ls) * 1000)
        else:
            raise RuntimeError(
                '[timing:timed_region] mode: %s not available' % mode)

    def __enter__(self):
        global mode

        if mode == 'disabled':
            return self
        elif mode == 'timing':
            ls = timer()
            global times, excluded

            times['lib_time'].append((timer() - ls) * 1000)

            self.ts = timer()

            return self
        else:
            raise RuntimeError(
                '[timing:timed_region] mode: %s not available' % mode)

    def __exit__(self, type, value, traceback):
        global mode

        if mode == 'disabled':
            return
        elif mode == 'timing':
            te = timer()
            global times, excluded
            times[self.key].append((te - self.ts) * 1000)

            times['lib_time'].append((timer() - te) * 1000)
            return
        else:
            raise RuntimeError(
                '[timing:timed_region] mode: %s not available' % mode)


def start_timing(funcname=''):
    global func_stack, start_time_stack, disabled, times, mode
    if mode == 'disabled':
        return
    elif mode == 'timing':
        ts = timer()
        if funcname:
            key = funcname
        else:
            parent = inspect.stack()[1]
            key = parent.filename.split('/')[-1]
            key = key + ':' + parent.lineno
        func_stack.append(key)
        start_time_stack.append(timer())
        if 'lib_time' not in times:
            times['lib_time'] = []
        times['lib_time'].append((timer() - ts) * 1000)
    else:
        raise RuntimeError(
            '[timing:timed_region] mode: %s not available' % mode)


def stop_timing(exclude=False):
    global times, start_time_stack, func_stack, excluded, mode
    if mode == 'disabled':
        return
    elif mode == 'timing':
        ts = timer()

        elapsed = (timer() - start_time_stack.pop()) * 1000
        key = func_stack.pop()
        if(key not in times):
            times[key] = []
            if exclude == True:
                excluded.append(key)
        times[key].append(elapsed)
        if 'lib_time' not in times:
            times['lib_time'] = []
        times['lib_time'].append((timer() - ts) * 1000)
    else:
        raise RuntimeError(
            '[timing:timed_region] mode: %s not available' % mode)


def report(skip=0, total_time=None, out_file=None):
    global times, excluded, mode

    if mode == 'disabled':
        return
    elif mode == 'timing':
        if out_file:
            out = open(out_file, 'w')
        else:
            out = sys.stdout

        if isinstance(total_time, str):
            _total_time = sum(times[total_time][skip:])
            excluded.append(total_time)
            _total_time -= sum(times['lib_time'])
        elif isinstance(total_time, float):
            _total_time = total_time
            _total_time -= sum(times['lib_time'])
        else:
            _total_time = sum(sum(x[skip:])
                              for k, x in times.items() if k not in excluded)

        otherPercent = 100.0
        otherTime = _total_time

        out.write(
            'function\ttotal_time(sec)\ttime_per_call(ms)\tstd(%)\tcalls\tglobal_percentage\n')
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

            out.write('%s\t%.3lf\t%.3lf\t%.2lf\t%d\t%.2lf\n'
                  % (k, vSum/1000., vMean, 100.0 * vStd / vMean,
                     len(v), vGPercent))

        out.write('%s\t%.3lf\t%.3lf\t%.2lf\t%d\t%.2lf\n'
              % ('Other', otherTime/1000., otherTime, 0.0, 1, otherPercent))

        out.write('%s\t%.3lf\t%.3lf\t%.2lf\t%d\t%.2lf\n'
              % ('total_time', (_total_time/1e3), _total_time, 0.0, 1, 100))
        out.close()
    elif mode == 'line_profiler':
        lp.print_stats()
    else:
        raise RuntimeError('[timing:report] mode: %s not available' % mode)


def reset():
    global times, start_time_stack, func_stack, excluded, mode, lp
    times = {}
    start_time_stack = []
    func_stack = []
    excluded = ['lib_time']
    mode = 'timing'
    lp = None
