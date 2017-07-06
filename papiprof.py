# Requires pypapi
# Can be used as:
# @papiprof('cache')
# def myfunction():
#    ...
#    ...
#
# myfunction()

from functools import wraps


def papiprof(type=['cache']):
    import pypapi
    import numpy as np
    events = []

    if('cache' in type):
        events_list = [
            pypapi.Event.L1_DCM,

            # pypapi.Event.L1_DCA,
            pypapi.Event.L2_DCM,
            pypapi.Event.L2_DCA,
            # pypapi.Event.L3_TCM,
            pypapi.Event.L3_DCA
        ]
        events += events_list

    if('flops' in type):
        events_list = [
            pypapi.Event.SP_OPS,
            # pypapi.Event.DP_OPS
            pypapi.Event.VEC_SP,
            # pypapi.Event.VEC_DP
            # pypapi.Event.FP_ARITH
        ]
        events += events_list

    if('cycles' in type):
        events_list = [
            pypapi.Event.STL_ICY,
            pypapi.Event.FUL_ICY,
            pypapi.Event.TOT_CYC,
            pypapi.Event.TOT_INS
            # pypapi.Event.CPU_CLK_UNHALTED
            # pypapi.Event.CYCLE_ACTIVITY
            # pypapi.Event.INST_RETIRED
        ]
        events += events_list

    event_dscr = np.asarray(events, dtype=pypapi.papi.Event)
    events = np.asarray(events, dtype=pypapi.papi.EventType)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            counts = np.empty(len(events), dtype=pypapi.CountType)
            pypapi.start_counters(events)
            result = func(*args, **kw)
            pypapi.stop_counters(counts)
            # print(counts)
            print('\n\nHardware Counters For: %s' % func.__name__)
            for e, c in zip(event_dscr, counts):
                print(e.name, c)
            return result
        return wrapper
    return decorator
