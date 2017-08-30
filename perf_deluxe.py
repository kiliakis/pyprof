import subprocess
import sys

event_list = ['cycles', 'instructions', 'task-clock',
              'cache-references', 'cache-misses'
              # 'LLC-loads', 'LLC-load-misses']
              # 'branch-misses', 'branches',
              # 'stalled-cycles-backend', 'stalled-cycles-frontend'
              ]

perf_args = ['perf', 'stat', '-B', '-r5']

final_call = perf_args + ['-e'] + [','.join(event_list)] + sys.argv[1:]

# print final_call
subprocess.call(final_call)
