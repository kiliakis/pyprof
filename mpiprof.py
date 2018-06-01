from functools import wraps
# try:
#     from time import perf_counter as timer
# except ImportError:
#     from time import time as timer
import inspect
# import numpy as np
# import sys
# import os
from cycler import cycle

import mpi4py
from mpi4py import MPE

# __initialized = False
# start_time_stack = []
# func_stack = []
# lp = None
# Modes available:
# 'disabled'
# 'tracking'
mode = 'disabled'
states = {}
__logfile = 'mpelog'
colors = cycle(['blue', 'orange', 'red', 'green',
                'pink', 'yellow', 'purple', 'black'])

colors = cycle(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                '11', '12', '15', '16', '17', '18', '19', '20'])


def init(logfile=__logfile):
    # if __initialized == False:
        # __initialized = True
    mpi4py.profile(name='mpe', logfile=logfile)
    mpi4py.MPI.Pcontrol(1)
    MPE.initLog(logfile=logfile)
    MPE.setLogFileName(logfile)


def finalize():
    MPE.finishLog()


def trackit(key=''):
    global states, mode, colors

    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            if mode == 'disabled':
                return f(*args, **kw)
            elif mode == 'tracking':
                nonlocal key
                if key == '':
                    _filename = inspect.stack()[1].filename.split('/')[-1]
                    key = _filename + '.' + f.__name__
                if key not in states:
                    states[key] = MPE.newLogState(key, next(colors))
                with states[key]:
                    result = f(*args, **kw)
                return result
            else:
                raise RuntimeError(
                    '[mpiprof.py:trackit] mode: %s not available' % mode)
        return timed
    return decorator


class tracked_region:

    def __init__(self, region_name=''):
        global mode, states, colors

        if mode == 'disabled':
            return
        elif mode == 'tracking':
            if region_name:
                key = region_name
            else:
                parent = inspect.stack()[1]
                key = parent.filename.split('/')[-1]
                key = key + ':' + parent.lineno
            # print('Adding new key:', key)
            # print(states)
            if (key not in states):
                states[key] = MPE.newLogState(key, next(colors))

            self.key = key

        else:
            raise RuntimeError(
                '[mpiprof:tracked_region] mode: %s not available' % mode)

    def __enter__(self):
        global mode, states

        if mode == 'disabled':
            return self
        elif mode == 'tracking':
            # return states[self.key]
            states[self.key].__enter__()
        else:
            raise RuntimeError(
                '[mpiprof:tracked_region] mode: %s not available' % mode)

    def __exit__(self, type, value, traceback):
        global mode, states

        if mode == 'disabled':
            return self
        elif mode == 'tracking':
            # return states[self.key]
            states[self.key].__exit__(type, value, traceback)
        else:
            raise RuntimeError(
                '[mpiprof:tracked_region] mode: %s not available' % mode)
        

        return


# def report(skip=0, total_time=None, out_file=None, out_dir='./'):
#     global states, excluded, mode

#     if mode == 'disabled':
#         return
#     elif mode == 'tracking':
#         if out_file:
#             # parent_dir = os.path.dirname(out_dir+'/'+out_file)
#             # if not os.path.exists(parent_dir):
#             #     os.mkdir(parent_dir)
#             out = open(out_dir+'/'+out_file, 'w')
#         else:
#             out = sys.stdout

#         if isinstance(total_time, str):
#             _total_time = sum(states[total_time][skip:])
#             excluded.append(total_time)
#             _total_time -= sum(states['lib_time'])
#         elif isinstance(total_time, float):
#             _total_time = total_time
#             _total_time -= sum(states['lib_time'])
#         else:
#             _total_time = sum(sum(x[skip:])
#                               for k, x in states.items() if k not in excluded)

#         otherPercent = 100.0
#         otherTime = _total_time

#         out.write(
#             'function\ttotal_time(sec)\ttime_per_call(ms)\tstd(%)\tcalls\tglobal_percentage\n')
#         for k, v in sorted(states.items()):

#             if k == 'lib_time':
#                 continue

#             vSum = np.sum(v[skip:])
#             vMean = vSum / len(v[skip:])
#             vStd = np.std(v[skip:])
#             vGPercent = 100 * vSum / _total_time

#             if k not in excluded:
#                 otherPercent -= vGPercent
#                 otherTime -= vSum

#             out.write('%s\t%.3lf\t%.3lf\t%.2lf\t%d\t%.2lf\n'
#                       % (k, vSum/1000., vMean, 100.0 * vStd / vMean,
#                          len(v), vGPercent))

#         out.write('%s\t%.3lf\t%.3lf\t%.2lf\t%d\t%.2lf\n'
#                   % ('Other', otherTime/1000., otherTime, 0.0, 1, otherPercent))

#         out.write('%s\t%.3lf\t%.3lf\t%.2lf\t%d\t%.2lf\n'
#                   % ('total_time', (_total_time/1e3), _total_time, 0.0, 1, 100))
#         out.close()
#     elif mode == 'line_profiler':
#         lp.print_stats()
#     else:
#         raise RuntimeError('[timing:report] mode: %s not available' % mode)


# def reset():
#     global states, start_time_stack, func_stack, excluded, mode, lp
#     states = {}
#     start_time_stack = []
#     func_stack = []
#     excluded = ['lib_time']
#     mode = 'timing'
#     lp = None
