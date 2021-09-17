#!/usr/bin/env python

## This script stands in for a top-level parsl workflow script.  This
## is where parsl.init() and parsl.dfk.cleanup() are called.

import signal, os, sys, time, datetime

print(f'{datetime.datetime.now()} entering sigTest.py')

def sigHandler(signum, frame):
    ## Generic signal handler
    now = datetime.datetime.now()
    print(f'PY: {now} Signal handler called with signal {signum} ({signal.strsignal(signum)})')
    ## In real life, here is we put something to shut down Parsl, such
    ## as "Parsl.dfk().cleanup()"
    sys.tracebacklimit=0    # disable sending traceback to stderr
    if signum == 10:
        print(f'PY:  User shutdown requested.  Calling parsl.dfk.cleanup()...')
        sys.stdout.flush()
        #time.sleep(90)
        print(f'PY:  User shutdown complete.  Exiting...')
        sys.stdout.flush()
        sys.exit()
    elif signum == 12:
        print(f'PY: SIGUSR2 ignored')
    else:
        return
    
#    raise OSError(f'OSError: exiting due to signal {signum}')

# Define handler for certain signals
signal.signal(signal.SIGTERM, sigHandler)
signal.signal(signal.SIGUSR1, sigHandler)
signal.signal(signal.SIGUSR2, sigHandler)

# And spend time doing nothing...
for i in range(0,300):
    time.sleep(3)
    print(f'PY: {datetime.datetime.now()} Waking after sleep {i}')
    sys.stdout.flush()
    pass

print(f'PY: {datetime.datetime.now()} exiting sigTest.py')
sys.stdout.flush()
