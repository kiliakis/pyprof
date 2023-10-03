import os
import numpy as np
import sys
import pyprof.timing as timing
from pyprof.papiprof import PAPIProf
import argparse
import random

this_directory = os.path.dirname(os.path.realpath(__file__)) + "/"
this_filename = sys.argv[0].split('/')[-1]

parser = argparse.ArgumentParser(
    description='A simple demo of the papiprof and timing modules.',
    usage='{} -r repetitions -s size -t threads'.format(sys.argv[0]))

parser.add_argument('-r', '--repetitions', type=int, default=1,
                    help='Times to execute the main loop.')

parser.add_argument('-s', '--size', type=int, default=10*1024**2,
                    help='Array size.')

parser.add_argument('-b', '--block', type=int, default=256,
                    help='Block size.')

parser.add_argument('-t', '--threads', type=int, default=1,
                    help='How many threads to use.')

parser.add_argument('-o', '--outdir', action='store', type=str,
                    default=None, help='Directory to store the results. Default: Only print.')


if __name__ == "__main__":
    timing.mode = 'timing'

    args = parser.parse_args()
    n_turns = args.repetitions
    size = args.size
    block = args.block
    n_threads = args.threads
    os.environ['OMP_NUM_THREADS'] = str(n_threads)

    np.random.seed(0)
    A = np.random.randn(size)
    print('Array A size: {:.0f} Mb'.format(sys.getsizeof(A)/ (1024**2)))
    # B = np.random.randn(size)

    papiprof = PAPIProf(metrics=['IPC', 'L2_MISS_RATE', 'L3_MISS_RATE', 'BRANCH_MSP_RATE'])
    # papiprof.list_events()
    papiprof.list_metrics()
    papiprof.list_avail_metrics()


    idx = np.arange(size)
    for r in range(n_turns):
        print('seq_access: step {}/{}'.format(r, n_turns))
        result = 0.
        papiprof.start_counters()
        for i in idx:
            if i % 3 == 0:
                result += A[i]
        papiprof.stop_counters()


    idx = np.arange(size)
    random.shuffle(idx)
    papiprof.start_counters()
    for r in range(n_turns):
        print('random_access: step {}/{}'.format(r, n_turns))
        result = 0.        
        for i in idx:
            if i % 3 == 0:
                result += A[i]
    papiprof.stop_counters()

    papiprof.report_timing()
    papiprof.report_metrics()
