This repo contains a variety of code snippets demonstrating certain features of Parsl as it runs at NERSC.

     wqTest.py - trivial workflow that demonstrates a (growing) number
     of features, including:
       - workQueue configuration, including work_queue_worker wrapper
       - monitoring, caching, (parsl) checkpointing
       - retry_handler()
       - custom exceptions
       - exeption handling
       - bash_app return codes

     wqWrap.bash - wrapper script for work_queue_worker

     ckptAction.py - custom python exception (ultimately intended to
     handle checkpointing)

     setupWQ - env setup at NERSC for descdm acct

     parslUpdate - commands to update the Parsl ('desc' branch) for user descdm at NERSC; also commnd to update the workQueue code (ndcctools)
     
     
