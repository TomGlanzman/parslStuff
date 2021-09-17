#!/bin/bash

jnum=$1
echo 'X: '`date`' entering sigTest.bash '$jnum

# Set signal traps
echo 'X.'$1': '`date`' setting signal traps in sigTest.bash'
function sigtrap {
    foo=`date`
    echo '%SIGNAL X.'${1}': '$foo' caught signal '$2
}
trap "sigtrap $jnum SIGCONT" SIGCONT
trap "sigtrap $jnum SIGTERM" SIGTERM
trap "sigtrap $jnum SIGUSR1" SIGUSR1

printenv | grep HOST
#printenv | grep SLURM | sort

# echo 'X.'$jnum': '`date`" scontrol show job "$SLURM_JOB_ID
# scontrol show job $SLURM_JOB_ID

echo 'X.'$jnum': '`date`" scontrol show step "$SLURM_JOB_ID
scontrol show step $SLURM_JOB_ID.$jnum



# Run a python test script and wait for it to complete

echo 'X.'$jnum': '`date`' Launch sigTest.py in background&'
python sigTest.py &> py-$jnum.out &
#python sigTest.py > py-$jnum.out 2> py-$jnum.err &   # interesting, but unnecessary
PID=$!

rc=0
until [ $rc -ne 0 ]; do
    echo 'X.'$jnum': '`date`' start new wait in sitTest.bash '$jnum
    wait $PID
    rc=$?
    echo 'X.'$jnum': '`date`' return from wait in sitTest.bash '$jnum
done


## One more in case an ignored signal is received
# echo 'X: '`date`' waiting a 2nd time...'
# wait $PID
# echo `date`' waiting a 3rd time...'
# wait $PID
# echo `date`' waiting a 4th time...'
# wait $PID

echo  'X.'$jnum': '`date`' exiting sigTest.bash '$jnum
