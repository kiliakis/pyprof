from functools import wraps
try:
    from time import perf_counter as timer
except ImportError:
    from time import time as timer
    # from time import clock as timer
import inspect
import numpy as np
import sys
import os
import pickle

times = {}
start_time_stack = []
func_stack = []
excluded = ['lib_time']
mode = 'disabled'
lp = None
# Modes available:
# 'line_profiler'
# 'disabled'
# 'timing'


def init(*args, **kw):
    return


def finalize(*args, **kw):
    return


def timeit(filename='', classname='', key='', exclude=False, cupy=False):
    global times, excluded, disabled, mode
    if cupy:
        import cupy
        start_gpu = cupy.cuda.Event()
        end_gpu = cupy.cuda.Event()

    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            if mode == 'disabled':
                return f(*args, **kw)
            elif mode == 'timing':
                ts = timer()
                if cupy:
                    start_gpu.record()
                result = f(*args, **kw)
                if cupy:
                    end_gpu.record()
                    end_gpu.synchronize()

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
                if cupy:
                    elapsed_time = cupy.cuda.get_elapsed_time(start_gpu, end_gpu)
                else:
                    elapsed_time = (te-ts) * 1000
                times[_key].append(elapsed_time)
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

    def __init__(self, region_name='', is_child_function=False, cupy=False):
        global mode
        if mode == 'disabled':
            return
        elif mode == 'timing':
            ls = timer()
            if cupy:
                import cupy
                self.start_gpu = cupy.cuda.Event()
                self.end_gpu = cupy.cuda.Event()
                self.cupy = True
            else:
                self.cupy = False
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
            if self.cupy:
                self.start_gpu.record()

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
            if self.cupy:
                import cupy
                self.end_gpu.record()
                self.end_gpu.synchronize()
                elapsed_time = cupy.cuda.get_elapsed_time(self.start_gpu, self.end_gpu)
            else:
                elapsed_time = (te-self.ts)*1000
            times[self.key].append(elapsed_time)

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


def report(skip=0, total_time=None, out_file=None, out_dir='./',
           save_pickle=False):
    global times, excluded, mode

    if mode == 'disabled':
        return
    elif mode == 'timing':
        if out_file:
            if not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            out = open(os.path.join(out_dir, out_file), 'w')
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
        if save_pickle and out_file:
            times['total_time'] = _total_time
            times['Other'] = otherTime
            out_file = os.path.splitext(out_file)[0] + '.p'
            with open(os.path.join(out_dir, out_file), 'wb') as picklefile:
                pickle.dump(times, picklefile)


        if out_file:
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
    # mode = 'timing'
    lp = None


def get(lst, exclude_lst=[]):
    global times, mode, excluded
    total = 0
    if mode != 'disabled':
        for k, v in times.items():
            if (k in excluded) or (k in exclude_lst):
                continue
            if np.any([l in k for l in lst]):
                total += np.sum(v)
    return total
