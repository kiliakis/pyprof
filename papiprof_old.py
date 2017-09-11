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


def papiprof(types=[], filename='', classname='',
             custom_event_list=[], metrics=[]):

    events = []
    for m in metrics:
        equation = papiprof.metrics[m]
        for symbol in equation:
            if isinstance(symbol, bytes):
                events.append(symbol)

    prof_type_dict = {
        'L1-cache': [
            b'perf::PERF_COUNT_HW_CACHE_L1D:ACCESS',
            b'perf::PERF_COUNT_HW_CACHE_L1D:MISS'
        ],
        'L2-cache': [
            b'L2_RQSTS:MISS',
            # b'L2_RQSTS:ALL_DEMAND_MISS',
            # b'L2_RQSTS:L2_PF_MISS',

            # b'L2_RQSTS:ALL_PF',
            # b'L2_RQSTS:ALL_DEMAND_REFERENCES',
            b'L2_RQSTS:REFERENCES'
        ],
        'LLC': [
            b'perf::CACHE-REFERENCES',
            b'perf::CACHE-MISSES'
            # b'perf::LLC-LOAD-MISSES',
            # b'perf::LLC-STORE-MISSES',
            # b'perf::LLC-PREFETCHES'
        ],
        'mem': [
            b'PAPI_LD_INS',
            b'PAPI_SR_INS',
            b'PAPI_LST_INS'
            # b'MISALIGN_MEM_REF:LOADS',
            # b'MISALIGN_MEM_REF:STORES'
        ],
        'flops': [
            # b'FP_ASSIST:ALL',
            # b'MOVE_ELIMINATION:SIMD_NOT_ELIMINATED',
            # b'MOVE_ELIMINATION:INT_NOT_ELIMINATED',
            # b'MOVE_ELIMINATION:SIMD_ELIMINATED',
            # b'MOVE_ELIMINATION:INT_ELIMINATED',
            # b'OTHER_ASSISTS:AVX_TO_SSE',
            # b'AVX:ALL'
            b'PAPI_FP_INS',
            b'PAPI_VEC_INS'
            # b'PAPI_FP_STAL'
            # b'PAPI_FML_INS'
        ],
        'branch': [
            b'perf::BRANCHES',
            b'perf::BRANCH-MISSES',
            b'BACLEARS'
            # b'BR_INST_EXEC:ALL_BRANCHES',
            # b'BR_MISP_RETIRED:ALL_BRANCHES',
            # b'BR_INST_RETIRED:ALL_BRANCHES'
            # b'MISPREDICTED_BRANCH_RETIRED'
        ],
        'cycles': [
            # b'CYCLE_ACTIVITY:CYCLES_NO_EXECUTE',
            # b'CYCLE_ACTIVITY:STALLS_LDM_PENDING',
            # b'CYCLE_ACTIVITY:STALLS_L1D_PENDING',
            # b'CYCLE_ACTIVITY:STALLS_L2_PENDING',
            # b'CYCLE_ACTIVITY:CYCLES_LDM_PENDING',
            # b'UOPS_EXECUTED:STALL_CYCLES',
            # b'UOPS_ISSUED:STALL_CYCLES',
            # b'UOPS_RETIRED:STALL_CYCLES',
            # b'RS_EVENTS:EMPTY_CYCLES',
            # b'RESOURCE_STALLS:ALL',
            # b'RESOURCE_STALLS:RS',
            # b'RESOURCE_STALLS:SB',
            # b'RESOURCE_STALLS:ROB'
            b'INSTRUCTIONS_RETIRED',
            b'CPU_CLK_UNHALTED'
            # b'CPU_CLK_THREAD_UNHALTED:THREAD_P',
            # b'perf::INSTRUCTIONS',
            # b'perf::CYCLES'
            # b'UOPS_EXECUTED:CORE',
            # b'UOPS_ISSUED:ALL'
        ]
    }

    for type in types:
        if type in prof_type_dict:
            events += prof_type_dict[type]

    events += custom_event_list
    events = np.unique(events)

    if (len(events) > 0) and (papiprof.eventSet is None):
        papiprof.eventSet = np.zeros(1, dtype=ct.c_int)
        papi_init(papiprof.eventSet)
        papi_add_events(papiprof.eventSet, events)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            eventValues = np.zeros(len(events), dtype=ct.c_longlong)
            if(len(events) > 0):
                papi_start(papiprof.eventSet)

            ts = time.time()
            result = func(*args, **kw)
            te = time.time()
            if(len(events) > 0):
                papi_stop(papiprof.eventSet, eventValues)

            key = func.__name__
            if classname:
                key = classname + '.' + key
            if filename:
                key = filename + '.' + key

            if(key not in papiprof.counters):
                papiprof.counters[key] = {}
                papiprof.counters[key][b'time(ms)'] = []

            papiprof.counters[key][b'time(ms)'].append((te - ts) * 1000)

            for e, c in zip(events, eventValues):
                if e not in papiprof.counters[key]:
                    papiprof.counters[key][e] = []
                papiprof.counters[key][e].append(c)

            return result
        return wrapper
    return decorator


papiprof.counters = {}
papiprof.eventSet = None
papiprof.metrics = {
    'IPC': [b'INSTRUCTIONS_RETIRED', b'CPU_CLK_UNHALTED', '/'],
    'CPI': [b'CPU_CLK_UNHALTED', b'INSTRUCTIONS_RETIRED', '/'],
    'FRONT_BOUND': [b'IDQ_UOPS_NOT_DELIVERED:CORE',
                    4., b'CPU_CLK_UNHALTED', '*', '/'],
    'BAD_SPECULATION': [b'UOPS_ISSUED:ANY', b'UOPS_RETIRED:RETIRE_SLOTS', '-',
                        4., b'INT_MISC:RECOVERY_CYCLES', '*', '+',
                        4., b'CPU_CLK_UNHALTED', '*', '/'],
    'RETIRING': [b'UOPS_RETIRED:RETIRE_SLOTS',
                 4., b'CPU_CLK_UNHALTED', '*', '/'],
    'BACK_BOUND': [1.,
                   'FRONTEND_BOUND', 'RETIRING', '+',
                   'BAD_SPECULATION', '+', '-'],
    'BACK_BOUND_AT_EXE': [b'CYCLE_ACTIVITY:CYCLES_NO_EXECUTE',
                          b'UOPS_EXECUTED:CYCLES_GE_1_UOP_EXEC', '+',
                          b'UOPS_EXECUTED:CYCLES_GE_2_UOPS_EXEC', '-',
                          b'CPU_CLK_UNHALTED', '/'],
    'MEM_BOUND': [b'CYCLE_ACTIVITY:STALLS_LDM_PENDING', b'CPU_CLK_UNHALTED', '/'],
    'CORE_BOUND': ['BACK_BOUND_AT_EXE', 'MEM_BOUND', '-']

}


def papiprof_print():
    string = '\n' + ''.join(['=']*80) + \
        '\n Counters Report Start\n' + ''.join(['=']*80)
    print(string)
    print('function\tcounter\taverage_value\tstd(%)\tcalls')
    for func, counters in sorted(papiprof.counters.items()):
        for counter, v in counters.items():
            if 'time' in str(counter):
                format_str = '%s\t%s\t%.3f\t%.2f\t%d'
                format_values = (func, counter.decode(), np.mean(v),
                                 100.0*np.std(v)/np.mean(v), len(v))
            else:
                format_str = '%s\t%s\t%d\t%.2f\t%d'
                format_values = (func, counter.decode(), np.sum(v), 0, len(v))

            print(format_str % format_values)
    string = ''.join(['=']*80) + \
        '\n Counters Report End\n' + ''.join(['=']*80)
    print(string+'\n')


def papiprof_report_metrics(metrics_names):
    def calculate(equation, counters):
        import operator
        ops = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }
        stack = []
        # for symbol in equation:
        while len(equation) != 0:
            # print(equation)
            symbol = equation.pop(0)
            if isinstance(symbol, float):
                stack.append(float(symbol))
            elif (symbol in ops):
                operand2 = stack.pop()
                operand1 = stack.pop()
                stack.append(ops[symbol](operand1, operand2))
            elif (isinstance(symbol, (str)) or isinstance(symbol, bytes)):
                if(symbol in counters):
                    stack.append(np.sum(counters[symbol]))
                elif(symbol in papiprof.metrics):
                    equation = papiprof.metrics[symbol] + equation
                else:
                    print('Symbol %s is needed but missing' % str(symbol))
                    return float('nan')
        return stack.pop()

    string = '\n' + ''.join(['=']*80) + \
        '\n Metrics Report Start\n' + ''.join(['=']*80)
    print(string)
    print('function\tmetric\taverage_value')
    for func, counters in sorted(papiprof.counters.items()):
        for metric_name in sorted(metrics_names):
            equation = papiprof.metrics[metric_name]
            result = calculate(equation.copy(), counters)
            print('%s\t%s\t%.3f' % (func, metric_name, result))
    string = ''.join(['=']*80) + \
        '\n Metrics  Report End\n' + ''.join(['=']*80)
    print(string+'\n')
