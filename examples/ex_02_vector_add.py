import os
import numpy as np
import sys
import pyprof.timing as timing
import argparse

from scipy.signal import fftconvolve
from pyprof.papiprof import PAPIProf

this_directory = os.path.dirname(os.path.realpath(__file__)) + "/"
this_filename = sys.argv[0].split('/')[-1]

parser = argparse.ArgumentParser(
    description='A simple demo of the papiprof and timing modules.',
    usage='{} -r repetitions -s size -t threads'.format(sys.argv[0]))

parser.add_argument('-r', '--repetitions', type=int, default=5000,
                    help='Times to execute the main loop.')

parser.add_argument('-s', '--size', type=int, default=10000,
                    help='Signal size.')

parser.add_argument('-t', '--threads', type=int, default=1,
                    help='How many threads to use.')

# parser.add_argument('-o', '--outdir', action='store', type=str,
#                     default=None, help='Directory to store the results. Default: Only print.')


if __name__ == "__main__":
    timing.mode = 'timing'

    args = parser.parse_args()
    n_turns = args.repetitions
    size = args.size
    n_threads = args.threads
    os.environ['OMP_NUM_THREADS'] = str(n_threads)

    np.random.seed(0)
    A = np.random.randn(size)
    B = np.random.randn(size)
    result = np.zeros(len(A))

    papiprof = PAPIProf(metrics=['IPC', 'L2_MISS_RATE', 'L3_MISS_RATE', 'LLC_MISS_RATE',
                                 'BRANCH_MISS_RATE'])
    # papiprof.list_events()
    # papiprof.list_metrics()
    # papiprof.list_avail_metrics()

    with timing.timed_region('vector_add') as tr:
        papiprof.start_counters()
        for i in range(n_turns):
            result = A + B
        papiprof.stop_counters()

    # timing.report()
    # papiprof.report_counters()
    papiprof.report_metrics()
