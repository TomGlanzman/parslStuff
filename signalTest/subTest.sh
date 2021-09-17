# launch a signal test SLURM job
#   $ . subTest.sh

sbatch slurm.bash


# sbatch options
#   -k    Do not revoke allocation if a node failes
#   --signal=USR1@60   Send all processes sig 10, 60 seconds before end-of-job
