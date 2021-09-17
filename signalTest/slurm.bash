#!/bin/bash
## Simple batch job to test propagation of signals, e.g., at end of job.
#SBATCH --qos=debug
#SBATCH --time=3
#SBATCH --nodes=2
##SBATCH --cpus-per-task=1
##SBATCH --tasks-per-node=5
#SBATCH --ntasks=3
#SBATCH --constraint=knl
#SBATCH --signal=USR1@100
#SBATCH --verbose

    
echo 'B: '`date`' starting slurm.bash batch step'

projdir='/global/homes/d/descdm/tomTest/parslStuff/signalTest'
echo 'B: '`date`' Batch script: projdir = '${projdir}

printenv | sort > ${projdir}/envs.out

echo 'B: '`date`" scontrol show job "$SLURM_JOB_ID
scontrol show job $SLURM_JOB_ID


# Catch certain signals
echo 'B: '`date`' setting signal traps in the batch script'
function sigtrap {
    foo=`date`
    echo '%SIGNAL B: '${foo}' signal '$1' caught'
    }

trap "sigtrap SIGCONT" SIGCONT
trap "sigtrap SIGTERM" SIGTERM
trap "sigtrap SIGUSR1" SIGUSR1

## srun
for i in $(seq 0 5); do
    echo 'B: '`date`' Launching sigTest '$i' using srun'
#    srun --output ${projdir}/bash$i.out bash ${projdir}/sigTest.bash $i &
    srun --exclusive --nodes=1 --ntasks=1 --cpus-per-task=100 --mem-per-cpu=1gb --output ${projdir}/bash$i.out bash ${projdir}/sigTest.bash $i &
    PID[$i]=$!
    echo 'B: '`date`' ----------> PID of created srun process = '${PID[$i]}
done

sleep 10

echo 'B: '`date`" scontrol show step "$SLURM_JOB_ID
scontrol show step $SLURM_JOB_ID

echo
echo "B: "`date`" ps -ju descdm"
ps -ju descdm
echo "---------------------------------------------"
echo
echo "B: "`date`" pstree -g descdm"
pstree -g descdm
echo "---------------------------------------------"
echo

echo "B: "`date`" All the PIDS: ${PID[@]}"

## Wait for all child processes to exit
wait

## Attempt to wait for each srun job separately
# for i in ${!PID[@]};do
#     echo 'B: '`date`' begin wait for PID['$i'] '${PID[$i]}' in slurm.bash...'
#     wait ${PID[$i]}
#     echo 'B: '`date`' return from wait, rc='${rc}
# done


# ## background (job control)
# echo 'Launching sigTest in background'
# bash ${projdir}/sigTest.bash &> ${projdir}/bash.out &
# PID=$!


# echo `date`' 1st wait for sigTest $PID to complete...'
# wait $PID

# # Another wait in case a signal was received and ignored
# echo `date`' starting 2nd wait...'
# wait $PID

echo 'B: '`date`' slurm.bash is ending normally'
