#!/bin/bash
## wqWrap.bash - wrapper for 'work_queue_worker'
##
##   Add the SLURM-specific "TimeLeft" as option to work_queue_worker
##

dhms2s () {
    ## This function processes the [[[dd-]hh:]mm:]ss provided by slurm and
    ## converts to decimal seconds
    ## Usage:  dhms2s $timeLeft
    ## Return: $seconds

    ## Split off days
    IFS='-'
    read -a ddd <<< "$1"
    local dd=0
    local hms=0
    if [[ ${#ddd[@]} -eq 1 ]] ;
    then
	hms=${ddd[0]}
    else
	dd=${ddd[0]}
	hms=${ddd[1]}
    fi
    unset IFS
    
    ## Split off hh mm ss
    IFS=':'
    read -a hhh <<< "${hms}"
    local hh=0
    local mm=0
    local ss=0
    if [[ ${#hhh[@]} -eq 1 ]] ;
    then
	ss=${hhh[0]}
    fi

    if [[ ${#hhh[@]} -eq 2 ]] ;
    then
	mm=${hhh[0]}
	ss=${hhh[1]}
    fi
    if [[ ${#hhh[@]} -eq 3 ]] ;
    then
	hh=${hhh[0]}
	mm=${hhh[1]}
	ss=${hhh[2]}
    fi
    dhms=(${dd} ${hh} ${mm} ${ss})
    unset IFS
    
    ## Calculate total seconds
    ##  Note: the "10#" prefix prevents bash from interpreting a leading zero to mean "octal"
    seconds=$(( 10#${dd}*86400+10#${hh}*3600+10#${mm}*60+10#${ss} ))
}



## Check if this script is running within a SLURM job

if [[ -z $SLURM_JOB_ID ]]
then
    echo NON-BATCH
    echo work_queue_worker $@
else
    echo SLURM JobID = ${SLURM_JOB_ID}
    ## determine time left in this job (in seconds)
    timeLeft=`squeue -j ${SLURM_JOB_ID} --noheader --Format=TimeLeft`
    echo "Time left in this job: ${timeLeft}"
    dhms2s ${timeLeft}
    
    ## The following are test cases
    # timeLeft="09-09:09:08"
    # echo timeLeft = ${timeLeft}
    # dhms2s ${timeLeft}
    # echo seconds = ${seconds}
    # echo =============================================
    # timeLeft="12:00:00"
    # echo timeLeft = ${timeLeft}
    # dhms2s ${timeLeft}
    # echo seconds = ${seconds}
    # echo =============================================
    # timeLeft="4:08"
    # echo timeLeft = ${timeLeft}
    # dhms2s ${timeLeft}
    # echo seconds = ${seconds}
    # echo =============================================
    # timeLeft="13"
    # echo timeLeft = ${timeLeft}
    # dhms2s ${timeLeft}
    # echo seconds = ${seconds}
    # echo =============================================

    
    ## How much time to allow workQueue to use?
    ##   Initially, reserve one minute
    limit=$(( ${seconds}-60 ))
    echo "Wall time limit = ${limit}"

    ## Start the worker
    echo work_queue_worker $@ --wall-time=${limit}
fi
