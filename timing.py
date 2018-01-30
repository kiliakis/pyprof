from functools import wraps
import time
import inspect
import numpy as np

times = {}
start_time_stack = []
func_stack = []
excluded = ['lib_time']
disabled = False


def timeit(filename='', classname='', exclude=False):
    global times, excluded, disabled

    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            if disabled == True:
                return f(*args, **kw)
            else:
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
        return timed
    return decorator


# timeit.times = {}


class timed_region:

    def __init__(self, region_name='', is_child_function=False):

        ls = time.time()
        global times, excluded, disabled

        if disabled == True:
            return self

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

    def __enter__(self):
        ls = time.time()
        global times, excluded, disabled

        if disabled == True:
            return self

        times['lib_time'].append((time.time() - ls) * 1000)

        self.ts = time.time()

        return self

    def __exit__(self, type, value, traceback):
        te = time.time()
        global times, excluded, disabled

        if disabled == True:
            return

        times[self.key].append((te - self.ts) * 1000)

        times['lib_time'].append((time.time() - te) * 1000)

        return


def start_timing(funcname=''):
    global func_stack, start_time_stack, disabled, times
    if disabled == True:
        return
    else:
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


def stop_timing(exclude=False):
    global times, start_time_stack, func_stack, excluded, disabled
    if disabled == True:
        return
    else:
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


def report(skip=0, total_time=None):
    global times, excluded
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

    # if total_time is not None:
    #     # other = _total_time
    #     # for k, x in times.items():
    #     #     if k not in excluded:
    #     #         print('Substracting:', k, sum(x[skip:]))
    #     #         other -= sum(x[skip:])

    #     other = _total_time - sum([sum(x[skip:])
    #                                for k, x in times.items() if k not in excluded])
    #     print('%s\t%s\t%.3lf\t%.2lf\t%d\t%.2lf'
    #           % ('Other', 'times(ms)', other,
    #              0.0, 1, 100.0 * other / _total_time))
    #     # print('[%s] Calls: %d, Average time: %.3f ms, Global Percentage: %.2f %%'
    #     #       % ('Other', 1, other, 100.0 * other / _total_time))

# class PyTimer(object):
#     """docstring for PyTimer"""

#     def __init__(self):
#         self.times = {}
#         self.start_time_stack = []
#         self.func_stack = []

#     def timeit(self, filename='', classname=''):
#         def decorator(f):
#             @wraps(f)
#             def timed(*args, **kw):
#                 ts = time.time()
#                 result = f(*args, **kw)
#                 te = time.time()
#                 if not filename:
#                     _filename = inspect.stack()[1].filename.split('/')[-1]
#                 else:
#                     _filename = filename
#                 key = _filename + '.' + f.__name__
#                 if classname:
#                     key = classname + '.' + key
#                 if(key not in self.times):
#                     self.times[key] = []
#                 self.times[key].append((te - ts) * 1000)
#                 return result
#             return timed
#         return decorator

    # def start_timing(self, funcname=''):
    #     if funcname:
    #         key = funcname
    #     else:
    #         parent = inspect.stack()[1]
    #         key = parent.filename.split('/')[-1]
    #         key = key + ':' + parent.lineno
    #     self.func_stack.append(key)
    #     self.start_time_stack.append(time.time())

    # def stop_timing(self):
    #     elapsed = (time.time() - self.start_time_stack.pop()) * 1000
    #     key = self.func_stack.pop()
    #     if(key not in self.times):
    #         self.times[key] = []
    #     self.times[key].append(elapsed)

    # def report(self, skip=0):
    #     total_time = sum(sum(x[skip:]) for x in self.times.values())
    #     for k, v in sorted(self.times.items()):
    #         print('[%s] Calls: %d, Average time: %.3f ms, Global Percentage: %.2f %%'
    #               % (k, len(v), np.mean(v[skip:]), 100.0 * np.sum(v[skip:]) / total_time))
