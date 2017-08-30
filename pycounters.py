import numpy as np
from functools import wraps
import ctypes as ct
import time
import os


libpapi = ct.CDLL(os.path.dirname(__file__) + '/src/libpapi.so')


libpapi.init.restype = ct.c_int
libpapi.init.argtypes = [ct.POINTER(ct.c_int)]


def papi_init(eventSet):

    libpapi.init(eventSet.ctypes.data_as(ct.POINTER(ct.c_int)))


libpapi.add_events.restype = ct.c_int
libpapi.add_events.argtypes = [ct.c_int,
                               ct.POINTER(ct.c_char_p),
                               ct.c_int]


def papi_add_events(eventSet, eventNames):
    N = len(eventNames)
    strArray = (ct.c_char_p * N)()
    strArray[:] = eventNames
    libpapi.add_events(eventSet[0], strArray, N)


libpapi.start.restype = ct.c_int
libpapi.start.argtypes = [ct.c_int]


def papi_start(eventSet):
    libpapi.start(eventSet[0])


libpapi.reset.restype = ct.c_int
libpapi.reset.argtypes = [ct.c_int]


def papi_reset(eventSet):
    libpapi.reset(eventSet[0])


libpapi.stop.restype = ct.c_int
libpapi.stop.argtypes = [ct.c_int,
                         ct.POINTER(ct.c_longlong)]


def papi_stop(eventSet, eventValues):
    libpapi.stop(eventSet[0],
                 eventValues.ctypes.data_as(ct.POINTER(ct.c_longlong)))


libpapi.read.restype = ct.c_int
libpapi.read.argtypes = [ct.c_int,
                         ct.POINTER(ct.c_longlong)]


def papi_read(eventSet, eventValues):
    libpapi.read(eventSet[0],
                 eventValues.ctypes.data_as(ct.POINTER(ct.c_longlong)))


libpapi.destroy.restype = ct.c_int
libpapi.destroy.argtypes = [ct.POINTER(ct.c_int)]


def papi_destroy(eventSet):
    libpapi.destroy(eventSet.ctypes.data_as(ct.POINTER(ct.c_int)))


def papiprof(type='cache', filename='', classname=''):

    # events = []
    if('cache' == type):
        events = [
            b'PAPI_L1_TCM',
            b'PAPI_L2_TCM',
            b'PAPI_L2_TCA',
            # b'PAPI_L3_TCM',
            b'PAPI_L3_TCA'
        ]
        # events += events_list

    # if('flops' in type):
    #     events_list = [
    #         pypapi.Event.SP_OPS,
    #         # pypapi.Event.DP_OPS
    #         pypapi.Event.VEC_SP,
    #         # pypapi.Event.VEC_DP
    #         # pypapi.Event.FP_ARITH
    #     ]
    #     events += events_list

    if('cycles' == type):
        events = [
            b'PAPI_TOT_INS',
            b'PAPI_TOT_CYC'
        ]
        # events += events_list

    if type not in papiprof.eventSet:
        papiprof.eventSet[type] = np.zeros(1, dtype=ct.c_int)
        papi_init(papiprof.eventSet[type])
        papi_add_events(papiprof.eventSet[type], events)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            eventValues = np.zeros(len(events), dtype=ct.c_longlong)
            papi_start(papiprof.eventSet[type])

            ts = time.time()
            result = func(*args, **kw)
            te = time.time()

            papi_stop(papiprof.eventSet[type], eventValues)

            key = func.__name__
            if classname:
                key = classname + '.' + key
            if filename:
                key = filename + '.' + key

            if(key not in papiprof.counters):
                papiprof.counters[key] = {}
                papiprof.times[key] = []

            papiprof.times[key].append((te - ts) * 1000)

            for e, c in zip(events, eventValues):
                if e not in papiprof.counters[key]:
                    papiprof.counters[key][e] = []
                papiprof.counters[key][e].append(c)

            return result
        return wrapper
    return decorator


papiprof.counters = {}
papiprof.times = {}
papiprof.eventSet = {}
