# wqTest.py - a simple test of parsl's new workqueue executor
#             This test uses SLURM batch to execute apps


####################################################################################
###  MODULES
####################################################################################

import sys,os

## Import needed (or anticipated) bits of Parsl 
import parsl
from parsl.config     import  Config
from parsl.app.app    import  python_app, bash_app, join_app
from parsl.monitoring import  MonitoringHub
from parsl.addresses  import  address_by_hostname
from parsl.providers  import  SlurmProvider
from parsl.providers  import  LocalProvider
from parsl.channels   import  LocalChannel
from parsl.launchers  import  SingleNodeLauncher
from parsl.launchers  import  SrunLauncher
from parsl.executors  import  HighThroughputExecutor
from parsl.executors  import  WorkQueueExecutor
from parsl.executors  import  ThreadPoolExecutor
from parsl.utils      import  get_all_checkpoints

import concurrent.futures
#from functools        import  partial
#from typing           import  Callable, List, Optional
from tabulate         import  tabulate
import code
import logging


####################################################################################
##  SETUP AND INITIALIZATION
####################################################################################

# Establish logging
logger = logging.getLogger("parsl.wqTest")
parsl.set_stream_logger(level=logging.INFO)
logger.info(f'Starting out...')


####################################################################################
###  GLOBALS
####################################################################################

thisDir = os.getcwd()


####################################################################################
###  RETRY HANDLER
####################################################################################


def myRetryHandler(exception, taskRecord):
    # import the specific python exceptions of interest
    #import parsl # for the 'cleanup()' function
    from parsl.executors.workqueue.errors import WorkQueueTaskFailure
    from parsl.app.errors import BashExitFailure
    from ckptAction import ckptAction    #custom exception

    import logging
    logger = logging.getLogger("parsl.wqTest")

    logger.info(f'v==========v==========v==========v==========v==========v==========v==========v==========v')
    logger.info(f'%RETRY: '
          f'{str(taskRecord["try_time_returned"])[:-7]} - '
          f'Exception= {sys.exc_info()[0].__name__}{exception.args}'
    )
    logger.info(f'%RETRY: '
          f'taskID {taskRecord["id"]}: '
          f'{taskRecord["func_name"]} '
          f'[retry {taskRecord["try_id"]}] '
          f'executor {taskRecord["executor"]}, '
          f'incoming #fails/failcost={taskRecord["fail_count"]}/{taskRecord["fail_cost"]}'
    )

    ## return value is "retries" increment or "cost"; 0 => retry forever
    if isinstance(exception,WorkQueueTaskFailure):   # batch job time-out or worker lost
        cost = 0.3
    elif isinstance(exception,ckptAction):  # custom exception
        cost = 0.77
    elif isinstance(exception,BashExitFailure):   # bash_app script returned non-zero RC
        cost = 0.001
        rc = int(exception.exitcode)
        app = taskRecord['func_name']
        if rc==126 or rc==127:   # command not founds or not executable
            cost = 100
        elif app=='random_bash1' and rc==76: # special handling for this rc (app specific)
            cost = 200
            #logger.info(f'rc=76  --  Abandon ship!')
            #sys.exit(200)      ## Kill the entire workflow [THIS DOES NOT WORK!]
            #parsl.cleanup()    ## Has no obvious effect
            # # this is horrifying.
            # import threading
            # import ctypes
            # ctypes.pythonapi.PyThreadState_SetAsyncExc(
            #     ctypes.c_long(threading.main_thread().ident),
            #     ctypes.py_object(RuntimeError)
            # )
            # logger.info("In exiting_retry_handler - passed internal block")
            # return 100
            pass
    else:
        cost=1
        pass

    logger.info(f'%RETRY: cost of this exception = {cost}')
    logger.info(f'^==========^==========^==========^==========^==========^==========^==========^==========^')
    return cost
    


####################################################################################
###  PARSL CONFIGURATION
####################################################################################

## Configure Parsl with two executors: htex and wq
workflow_cwd = os.getcwd()
workflow_src_dir = os.path.dirname(os.path.abspath(__file__))

worker_init = (f'echo "Starting batch job on "`date`\n'
               f'echo "Submitted from "$HOST\n'
               f'export PYTHONPATH={workflow_src_dir}\n'
               f'export OMP_NUM_THREADS=1\n'
               f'cd {workflow_cwd}\n'
               f'source setupWQ\n'
               )
logger.info(f'worker_init = \n{worker_init}')


config = Config(
    strategy='simple',                       # are there other choices?
    garbage_collect=False,                   # False = keep task records in dfk().tasks
    app_cache=True,                          # needed to enable task_hashsum generation
    checkpoint_mode='task_exit',             # produce checkpointing data for this run
    checkpoint_files=get_all_checkpoints(),  # process all previous checkpointing data
    retries=5,                               # in addition to original attempt
    retry_handler=myRetryHandler,            # determine failure cause and adjust #retries accordingly
    executors=[
        ThreadPoolExecutor(
                    label='cori-login',
                    max_threads=2
                    ),
        WorkQueueExecutor(
            label='WQxtr',
            port=9000,
            shared_fs=True,
            max_retries=1,               ## 1 => let Parsl handle retries
            worker_executable=os.path.join(thisDir,'wqWrap.bash'),
            provider=SlurmProvider(
               "None",                   ## cori queue/partition/qos
               nodes_per_block=1,        ## nodes per batch job
               exclusive=True,
               init_blocks=0,            ## blocks (batch jobs) to start with (on spec)
               min_blocks=0,
               max_blocks=1,             ## max # of batch jobs
               parallelism=0,            ## >0 causes multiple batch jobs, even for simple WFs
               scheduler_options="""#SBATCH --constraint=knl\n#SBATCH --qos=debug""",  ## cori queue
               launcher=SrunLauncher(overrides='-K0 -k --slurmd-debug=error'), # srun opts
               cmd_timeout=300,          ## timeout (sec) for slurm commands (NERSC can be slow)
               walltime="00:03:00",      ## SLURM batch job time
               worker_init=worker_init
            ))
        # HighThroughputExecutor(
        #     label='HTEX1',
        #     cores_per_worker=1,
        #     max_workers=2,
        #     poll_period=30,
        #     provider=LocalProvider(
        #         init_blocks=0,
        #         min_blocks=0,
        #         max_blocks=1))
        ],
    monitoring=MonitoringHub(
        hub_address="localhost",
        hub_port=55055,
        monitoring_debug=True,
        resource_monitoring_interval=1,
    )
)


####################################################################################
###    Define Parsl apps - those apps/functions that will be executed
###    directly under Parsl control
####################################################################################

@python_app(executors=['WQxtr'],
            cache=True,
            ignore_for_cache=["stdout", "stderr", "parsl_resource_specification"])
def random_py(i, stdout=None, stderr=None, parsl_resource_specification={}):
   import random,time
   import logging
   logger = logging.getLogger("parsl.random_py")
   
   rn = random.random()
   #if rn > 0.9: j=2./0.
   #else:  sys.exit(99)
   st = (rn*i+1)*60.
   logger.info(f'random_py: i={i},rn={rn},st={st}')
   time.sleep(st)
   foo="Some random1 returned stuff"
   return foo

@bash_app(executors=['WQxtr'],
          cache=True,
          ignore_for_cache=["stdout", "stderr", "parsl_resource_specification"])
def random_bash1(i, stdout=None, stderr=None, parsl_resource_specification={}):
   import random,time,sys,os
   import logging
   logger = logging.getLogger("parsl.random_bash1")
   logger.info('random_bash1: entering app...')

   rn = random.random()
   st = 20.+(rn*i+1)*10.
   logger.info(f'random_bash1: i={i},rn={rn},st={st}')
   time.sleep(st)
   if rn > 0.6: j=2./0.
   #else:  sys.exit(99)
   return '/global/homes/d/descdm/tomTest/parslStuff/testApp1.bash'
   

@bash_app(executors=['WQxtr'],
          cache=True,
          ignore_for_cache=["stdout", "stderr", "parsl_resource_specification"])
def random_bash2(i, stdout=None, stderr=None, parsl_resource_specification={}):
   import random,time,sys,os
   from ckptAction import ckptAction
   import logging

   logger = logging.getLogger("parsl.random_bash2")

   logger.info('random_bash2: entering app...')
   rn = random.random()
   st = 30.+(rn*i+1)*10.
   logger.info(f'random_bash2: i={i},rn={rn},st={st}')
   time.sleep(st)
   if rn > 0.8: raise ckptAction("Gotterdammerung",st)
   #if rn > 0.2: j=2./0.
   #if rn > 0.9: sys.exit(93)
   return f'echo {st}'


@join_app()
def many1(loops):
   ## Submit Parsl apps for execution
   myFutures1 = []
   logger.info(f'many1 preparing for {loops} loops.')
   for i in range(0,loops):
      logger.info(f'many1: Starting many loop {i}')
      x = random_bash1(i,
                      stdout=f'{logdir}/random1_{i}.stdout',
                      stderr=f'{logdir}/random1_{i}.stderr',
                      parsl_resource_specification={'cores':2, 'memory':2000, 'disk':0, 'running_time_min':60})
      myFutures1.append(x)
      pass
   logger.info(f'many1: About to return...')
   return myFutures1


@join_app()
def many2(loops):
   ## Submit Parsl apps for execution
   myFutures2 = []
   logger.info(f'many2 preparing for {loops} loops.')
   for i in range(0,loops):
      logger.info(f'many2: Starting many loop {i}')
      x = random_bash2(i,
                      stdout=f'{logdir}/random2_{i}.stdout',
                      stderr=f'{logdir}/random2_{i}.stderr',
                      parsl_resource_specification={'cores':1, 'memory':2000, 'disk':0, 'running_time_min':60})
      myFutures2.append(x)
      pass
   logger.info(f'many2: About to return...')
   return myFutures2



####################################################################################
###   TOP-LEVEL WORKFLOW SCRIPT
####################################################################################


## Start Parsl
parsl.load(config)
#logger.info("Contents of the Parsl Config():\n",Config)

## Organize app logs by run in the Parsl runinfo tree
logdir = parsl.dfk().run_dir + "/appLogs/"
if not os.path.isdir(logdir):
   logger.info(f'creating {logdir}')
   os.mkdir(logdir)
logger.info(f'logdir = {logdir}')

## Submit Parsl apps for execution
myFutures = []

fut = many1(10)
myFutures.append(fut)

fut = many2(10)
myFutures.append(fut)

## Wait for apps to finish
logger.info('main: waiting for myFutures to complete...')
sys.stdout.flush()
n=0
##   Forcing a timeout in the 'wait' allows any exceptions to leak through.
while True:
    n += 1
    (fdone,fundone) = concurrent.futures.wait(myFutures, timeout=10)
    logger.info(f'concurrent.futures.wait return {n}, len(fdone)={len(fdone)}, len(fundone)={len(fundone)}')
    parsl.dfk().log_task_states()   # Few-line summary of all defined Parsl tasks
    if len(fundone) == 0: break
    pass

logger.info('main: myFutures complete!')

# print out summary table of all tasks for this run
# (based on the content of the Parsl task list; note
#  that garbage_collection must be disabled for this to work)
logger.info('main: print out parsl.dfk().tasks')
tasks = parsl.dfk().tasks

## Drop into interactive mode
#code.interact(local=locals())

rw = []
for taskNum in tasks:
    task = tasks[taskNum]
    fut = task['app_fu']       # app future
    result = ''
    exception = fut.exception()
    if exception == None: result=fut.result()

    rw.append([
        task['id'],
        task['status'].name,
        task['func_name'],
        task['args'],
        task['kwargs'],
        result,
        exception
        ])
    pass

titles = ['taskID','status','function','args','kwargs','result','exception']
tblfmt='psql'
logger.info(f'main: Task list (with {len(tasks)} entries):')
print('\n'+tabulate(rw,headers=titles,tablefmt=tblfmt))
logger.info("main: END")

