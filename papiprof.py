import numpy as np
from functools import wraps
import ctypes as ct
import time
import os
import inspect


libpapi = ct.CDLL(os.path.dirname(__file__) + '/src/libpapi.so')


preset_metrics = {
    'IPC': ['INSTRUCTIONS_RETIRED', 'CPU_CLK_UNHALTED', '/'],
    'CPI': ['CPU_CLK_UNHALTED', 'INSTRUCTIONS_RETIRED', '/'],
    'FRONT_BOUND%': ['IDQ_UOPS_NOT_DELIVERED:CORE',
                     4., 'CPU_CLK_UNHALTED', '*', '/', 100., '*'],
    'BAD_SPECULATION%': ['UOPS_ISSUED:ANY', 'UOPS_RETIRED:RETIRE_SLOTS', '-',
                         4., 'INT_MISC:RECOVERY_CYCLES', '*', '+',
                         4., 'CPU_CLK_UNHALTED', '*', '/', 100., '*'],
    'RETIRING%': ['UOPS_RETIRED:RETIRE_SLOTS',
                  4., 'CPU_CLK_UNHALTED', '*', '/', 100., '*'],
    'BACK_BOUND%': [1.,
                    'FRONTEND_BOUND', 'RETIRING', '+',
                    'BAD_SPECULATION', '+', '-', 100., '*'],
    'BACK_BOUND_AT_EXE%': ['CYCLE_ACTIVITY:CYCLES_NO_EXECUTE',
                           'UOPS_EXECUTED:CYCLES_GE_1_UOP_EXEC', '+',
                           'UOPS_EXECUTED:CYCLES_GE_2_UOPS_EXEC', '-',
                           'CPU_CLK_UNHALTED', '/', 100., '*'],
    'MEMORY_BOUND%': ['CYCLE_ACTIVITY:STALLS_LDM_PENDING', 'CPU_CLK_UNHALTED',
                      '/', 100., '*'],
    'L2_COST%': [12., 'MEM_LOAD_UOPS_RETIRED:L2_HIT', '*',
                 'CPU_CLK_UNHALTED', '/', 100., '*'],
    'L3_COST%': [26., 'MEM_LOAD_UOPS_RETIRED:L3_HIT', '*',
                 'CPU_CLK_UNHALTED', '/', 100., '*'],
    'MEMORY_COST%': [200., 'MEM_LOAD_UOPS_LLC_HIT_RETIRED:XNSP_HIT', '*',
                     'CPU_CLK_UNHALTED', '/', 100., '*'],
    'L1_BOUND%': ['CYCLE_ACTIVITY:STALLS_LDM_PENDING',
                  'CYCLE_ACTIVITY:STALLS_L1D_PENDING', '-',
                  'CPU_CLK_UNHALTED', '/', 100., '*'],
    'L2_BOUND%': ['CYCLE_ACTIVITY:STALLS_L1D_PENDING',
                  'CYCLE_ACTIVITY:STALLS_L2_PENDING', '-',
                  'CPU_CLK_UNHALTED', '/', 100., '*'],
    'L3_BOUND%': ['CYCLE_ACTIVITY:STALLS_L2_PENDING', 'L3_Hit_fraction', '*',
                  'CPU_CLK_UNHALTED', '/', 100., '*'],
    'L3_HIT_FRACTION': ['MEM_LOAD_UOPS_RETIRED:L3_HIT',
                        'MEM_LOAD_UOPS_RETIRED:L3_HIT',
                        'MEM_L3_WEIGHT', 'MEM_LOAD_UOPS_RETIRED:L3_MISS', '*',
                        '+',
                        '/'],
    # MEM_L3_WEIGHT: External memory to L3 cache latency ratio, 7 can be used
    # for 3rd generation intel
    'MEM_L3_WEIGHT': [7.],
    'L3_MISS_FRACTION': ['MEM_LOAD_UOPS_RETIRED:L3_MISS',
                         'MEM_LOAD_UOPS_RETIRED:L3_MISS',
                         'MEM_LOAD_UOPS_RETIRED:L3_HIT',
                         '+',
                         '/'],
    'MEM_BOUND%': ['CYCLE_ACTIVITY:STALLS_L2_PENDING', 'L3_MISS_FRACTION', '*',
                   'CPU_CLK_UNHALTED', '/', 100., '*'],
    'UNCORE_BOUND%': ['CYCLE_ACTIVITY:STALLS_L2_PENDING', 'CPU_CLK_UNHALTED',
                      '/', 100., '*'],
    'CORE_BOUND%': ['BACK_BOUND_AT_EXE', 'MEM_BOUND', '-', 100., '*'],
    'RESOURCE_STALLS_COST%': ['RESOURCE_STALLS:ALL', 'CPU_CLK_UNHALTED', '/'],
    'LOCK_CONTENTION%': ['MEM_LOAD_UOPS_L3_HIT_RETIRED:XSNP_HITM',
                         'MEM_UOPS_RETIRED:LOCK_LOADS', '/', 100., '*'],
    'BR_MISP_COST%': [20., 'BR_MISP_RETIRED:ALL_BRANCHES', '*',
                      'CPU_CLK_UNHALTED', '/', 100., '*']

}


class PAPIProf(object):
    """docstring for PAPIProf"""

    def __init__(self, metrics=[], events=[]):
        self.events = []
        self.counters = {}
        self.eventSet = np.zeros(1, dtype=ct.c_int)
        self.metrics = []
        self.ts = 0
        self.papi_init(self.eventSet)

        if len(metrics):
            self.add_metrics(metrics)

        if len(events):
            self.add_events(events)

    def add_events(self, event_list):
        new_events = list(set(event_list) - set(self.events))
        self.papi_add_events(self.eventSet, new_events)
        self.events += new_events

    def start_counters(self):
        self.ts = time.time()
        parent = inspect.stack()[1]
        self.linestart = str(parent.lineno)
        if(len(self.events) > 0):
            self.papi_start(self.eventSet)

    def stop_counters(self):
        eventValues = np.zeros(len(self.events), dtype=ct.c_longlong)

        if(len(self.events) > 0):
            self.papi_stop(self.eventSet, eventValues)
        te = time.time()
        parent = inspect.stack()[1]
        key = parent.filename+':'+self.linestart+'-'+str(parent.lineno)
        if(key not in self.counters):
            self.counters[key] = {}
            self.counters[key]['time(ms)'] = []

        self.counters[key]['time(ms)'].append((te - self.ts) * 1000)

        for e, c in zip(self.events, eventValues):
            if e not in self.counters[key]:
                self.counters[key][e] = []
            self.counters[key][e].append(c)

    def clear_counters(self):
        pass

    def add_metrics(self, metrics, helper=False):
        new_metrics = list(set(metrics) - set(self.metrics))

        # self.metrics = np.unique(self.metrics + metrics)
        events = []
        for m in new_metrics:
            equation = preset_metrics[m]
            for symbol in equation:
                if symbol in preset_metrics:
                    self.add_metrics([symbol], helper=True)
                elif isinstance(symbol, str) and \
                        (symbol not in ['/', '+', '-', '*']):
                    events.append(symbol)

        if not helper:
            self.metrics = self.metrics + new_metrics

        events = list(set(events) - set(self.events))
        if len(events):
            self.events += events
            self.papi_add_events(self.eventSet, events)

    def decorate(self, filename='', classname='', metrics=[], events=[]):
        if len(metrics):
            self.add_metrics(metrics)
        if len(events):
            self.add_events(events)

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kw):
                eventValues = np.zeros(len(self.events), dtype=ct.c_longlong)

                ts = time.time()
                if(len(self.events) > 0):
                    self.papi_start(self.eventSet)

                result = func(*args, **kw)

                if(len(self.events) > 0):
                    self.papi_stop(self.eventSet, eventValues)
                te = time.time()

                key = func.__name__
                if classname:
                    key = classname + '.' + key
                if filename:
                    key = filename + '.' + key

                if(key not in self.counters):
                    self.counters[key] = {}
                    self.counters[key]['time(ms)'] = []

                self.counters[key]['time(ms)'].append((te - ts) * 1000)

                for e, c in zip(self.events, eventValues):
                    if e not in self.counters[key]:
                        self.counters[key][e] = []
                    self.counters[key][e].append(c)

                return result
            return wrapper
        return decorator

    def report_metrics(self):
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
                # print(stack)
                symbol = equation.pop(0)
                if isinstance(symbol, float) or isinstance(symbol, int):
                    stack.append(float(symbol))
                elif (symbol in ops):
                    operand2 = stack.pop()
                    operand1 = stack.pop()
                    stack.append(ops[symbol](operand1, operand2))
                elif (isinstance(symbol, (str)) or isinstance(symbol, bytes)):
                    if(symbol in counters):
                        stack.append(np.sum(counters[symbol]))
                    elif(symbol in preset_metrics):
                        equation = preset_metrics[symbol] + equation
                        # result = calculate(preset_metrics[symbol], counters)
                        # print('The result was: ', result)
                        # stack.append(result)
                    else:
                        print('Symbol %s is needed but missing' % str(symbol))
                        return float('nan')
            return stack.pop()

        string = '\n' + ''.join(['=']*80) + \
            '\n Metrics Report Start\n' + ''.join(['=']*80)
        print(string)
        print('function\tmetric\taverage_value\tstd(%)\tcalls')
        for func, counters in sorted(self.counters.items()):
            for metric_name in sorted(self.metrics):
                equation = preset_metrics[metric_name]
                result = calculate(equation.copy(), counters)
                print('%s\t%s\t%.3f\t%s\t%s' %
                      (func, metric_name, result, 'na', 'na'))
        string = ''.join(['=']*80) + \
            '\n Metrics  Report End\n' + ''.join(['=']*80)
        print(string+'\n')

    def report_counters(self):
        string = '\n' + ''.join(['=']*80) + \
            '\n Counters Report Start\n' + ''.join(['=']*80)
        print(string)
        print('function\tcounter\taverage_value\tstd(%)\tcalls')
        for func, counters in sorted(self.counters.items()):
            for counter, v in counters.items():
                if 'time' in str(counter):
                    continue
                format_str = '%s\t%s\t%d\t%.2f\t%d'
                format_values = (func, counter, np.sum(v),
                                 100. * len(v) * np.std(v) / np.sum(v), len(v))
                print(format_str % format_values)

        string = ''.join(['=']*80) + \
            '\n Counters Report End\n' + ''.join(['=']*80)
        print(string+'\n')

    def report_timing(self):
        string = '\n' + ''.join(['=']*80) + \
            '\n Timing Report Start\n' + ''.join(['=']*80)
        print(string)
        print('function\tcounter\taverage_value\tstd(%)\tcalls')
        for func, counters in sorted(self.counters.items()):
            for counter, v in counters.items():
                if 'time' in str(counter):
                    format_str = '%s\t%s\t%.3f\t%.2f\t%d'
                    format_values = (func, counter, np.mean(v),
                                     100.0*np.std(v)/np.mean(v), len(v))
                    print(format_str % format_values)

        string = ''.join(['=']*80) + \
            '\n Timing Report End\n' + ''.join(['=']*80)
        print(string+'\n')

    def papi_init(self, eventSet):
        libpapi.init.restype = ct.c_int
        libpapi.init.argtypes = [ct.POINTER(ct.c_int)]
        libpapi.init(eventSet.ctypes.data_as(ct.POINTER(ct.c_int)))

    def papi_add_events(self, eventSet, eventNames):
        libpapi.add_events.restype = ct.c_int
        libpapi.add_events.argtypes = [ct.c_int,
                                       ct.POINTER(ct.c_char_p),
                                       ct.c_int]
        N = len(eventNames)
        strArray = (ct.c_char_p * N)()
        strArray[:] = [x.encode() for x in eventNames]
        libpapi.add_events(eventSet[0], strArray, N)

    def papi_start(self, eventSet):
        libpapi.start.restype = ct.c_int
        libpapi.start.argtypes = [ct.c_int]
        libpapi.start(eventSet[0])

    def papi_reset(self, eventSet):
        libpapi.reset.restype = ct.c_int
        libpapi.reset.argtypes = [ct.c_int]
        libpapi.reset(eventSet[0])

    def papi_stop(self, eventSet, eventValues):
        libpapi.stop.restype = ct.c_int
        libpapi.stop.argtypes = [ct.c_int,
                                 ct.POINTER(ct.c_longlong)]
        libpapi.stop(eventSet[0],
                     eventValues.ctypes.data_as(ct.POINTER(ct.c_longlong)))

    def papi_read(self, eventSet, eventValues):
        libpapi.read.restype = ct.c_int
        libpapi.read.argtypes = [ct.c_int,
                                 ct.POINTER(ct.c_longlong)]
        libpapi.read(eventSet[0],
                     eventValues.ctypes.data_as(ct.POINTER(ct.c_longlong)))

    def papi_destroy(self, eventSet):
        libpapi.destroy.restype = ct.c_int
        libpapi.destroy.argtypes = [ct.POINTER(ct.c_int)]
        libpapi.destroy(eventSet.ctypes.data_as(ct.POINTER(ct.c_int)))


#     prof_type_dict = {
#         'L1-cache': [
#             b'perf::PERF_COUNT_HW_CACHE_L1D:ACCESS',
#             b'perf::PERF_COUNT_HW_CACHE_L1D:MISS'
#         ],
#         'L2-cache': [
#             b'L2_RQSTS:MISS',
#             # b'L2_RQSTS:ALL_DEMAND_MISS',
#             # b'L2_RQSTS:L2_PF_MISS',

#             # b'L2_RQSTS:ALL_PF',
#             # b'L2_RQSTS:ALL_DEMAND_REFERENCES',
#             b'L2_RQSTS:REFERENCES'
#         ],
#         'LLC': [
#             b'perf::CACHE-REFERENCES',
#             b'perf::CACHE-MISSES'
#             # b'perf::LLC-LOAD-MISSES',
#             # b'perf::LLC-STORE-MISSES',
#             # b'perf::LLC-PREFETCHES'
#         ],
#         'mem': [
#             b'PAPI_LD_INS',
#             b'PAPI_SR_INS',
#             b'PAPI_LST_INS'
#             # b'MISALIGN_MEM_REF:LOADS',
#             # b'MISALIGN_MEM_REF:STORES'
#         ],
#         'flops': [
#             # b'FP_ASSIST:ALL',
#             # b'MOVE_ELIMINATION:SIMD_NOT_ELIMINATED',
#             # b'MOVE_ELIMINATION:INT_NOT_ELIMINATED',
#             # b'MOVE_ELIMINATION:SIMD_ELIMINATED',
#             # b'MOVE_ELIMINATION:INT_ELIMINATED',
#             # b'OTHER_ASSISTS:AVX_TO_SSE',
#             # b'AVX:ALL'
#             b'PAPI_FP_INS',
#             b'PAPI_VEC_INS'
#             # b'PAPI_FP_STAL'
#             # b'PAPI_FML_INS'
#         ],
#         'branch': [
#             b'perf::BRANCHES',
#             b'perf::BRANCH-MISSES',
#             b'BACLEARS'
#             # b'BR_INST_EXEC:ALL_BRANCHES',
#             # b'BR_MISP_RETIRED:ALL_BRANCHES',
#             # b'BR_INST_RETIRED:ALL_BRANCHES'
#             # b'MISPREDICTED_BRANCH_RETIRED'
#         ],
#         'cycles': [
#             # b'CYCLE_ACTIVITY:CYCLES_NO_EXECUTE',
#             # b'CYCLE_ACTIVITY:STALLS_LDM_PENDING',
#             # b'CYCLE_ACTIVITY:STALLS_L1D_PENDING',
#             # b'CYCLE_ACTIVITY:STALLS_L2_PENDING',
#             # b'CYCLE_ACTIVITY:CYCLES_LDM_PENDING',
#             # b'UOPS_EXECUTED:STALL_CYCLES',
#             # b'UOPS_ISSUED:STALL_CYCLES',
#             # b'UOPS_RETIRED:STALL_CYCLES',
#             # b'RS_EVENTS:EMPTY_CYCLES',
#             # b'RESOURCE_STALLS:ALL',
#             # b'RESOURCE_STALLS:RS',
#             # b'RESOURCE_STALLS:SB',
#             # b'RESOURCE_STALLS:ROB'
#             b'INSTRUCTIONS_RETIRED',
#             b'CPU_CLK_UNHALTED'
#             # b'CPU_CLK_THREAD_UNHALTED:THREAD_P',
#             # b'perf::INSTRUCTIONS',
#             # b'perf::CYCLES'
#             # b'UOPS_EXECUTED:CORE',
#             # b'UOPS_ISSUED:ALL'
#         ]
#     }
