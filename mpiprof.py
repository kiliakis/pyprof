from functools import wraps
import inspect
from cycler import cycle

import mpi4py
try:
    from mpi4py import MPE
except ImportError:
    pass
# Modes available:
# 'disabled'
# 'tracing'
mode = 'disabled'
times = {}
__logfile = 'mpelog'
colors = cycle(['blue', 'red', 'green', 'orange', 'magenta',
                'gray', 'pink', 'yellow',  'cyan',
                'brown', 'aquamarine', 'maroon',
                'ivory', 'coral', 'dark olive green', 'lavender',
                'rose', 'white', 'black'])


def init(logfile=__logfile):
    if mode != 'tracing':
        return
    mpi4py.profile(name='mpe', logfile=logfile)
    mpi4py.MPI.Pcontrol(1)
    MPE.initLog(logfile=logfile)
    MPE.setLogFileName(logfile)


def finalize():
    if mode != 'tracing':
        return
    MPE.finishLog()


def traceit(key=''):
    global times

    def decorator(f):
        @wraps(f)
        def timed(*args, **kw):
            if mode == 'disabled':
                return f(*args, **kw)
            elif mode == 'tracing':
                if key not in times:
                    times[key] = MPE.newLogState(key, next(colors))
                with times[key]:
                    result = f(*args, **kw)
                return result
            else:
                raise RuntimeError(
                    '[mpiprof.py:traceit] mode: %s not available' % mode)
        return timed
    return decorator


class traced_region:

    def __init__(self, region_name=''):
        global times

        if mode == 'disabled':
            return
        elif mode == 'tracing':
            if region_name:
                key = region_name
            else:
                parent = inspect.stack()[1]
                key = parent.filename.split('/')[-1]
                key = key + ':' + parent.lineno
            if (key not in times):
                times[key] = MPE.newLogState(key, next(colors))

            self.key = key

        else:
            raise RuntimeError(
                '[mpiprof:traced_region] mode: %s not available' % mode)

    def __enter__(self):
        global times

        if mode == 'disabled':
            return self
        elif mode == 'tracing':
            # return times[self.key]
            times[self.key].__enter__()
        else:
            raise RuntimeError(
                '[mpiprof:traced_region] mode: %s not available' % mode)

    def __exit__(self, type, value, traceback):
        global times

        if mode == 'disabled':
            return self
        elif mode == 'tracing':
            # return times[self.key]
            times[self.key].__exit__(type, value, traceback)
        else:
            raise RuntimeError(
                '[mpiprof:traced_region] mode: %s not available' % mode)

        return
