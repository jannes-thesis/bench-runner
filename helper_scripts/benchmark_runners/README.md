This directory contains wrapper scripts to run different benchmarks
testing the scaling adapter as a component in some threadpool.

# Script argument structure

## first arguments
Should define the actual workload (job for the pool workers & type of load).
Selection of adapter/static version of pool should be in flag or part of workload definition.

## next arguments
These are the parameters to the workload (e.g number of jobs, file sizes).

## second to last argument
This needs to be the param which determines which disk (ssd/hdd) is used.

## last argument
This needs to be the size of the threadpool if the static version without adapter is used.

## Example
dynamic-io-pool.sh "worker_function" "load_and_pool-variant" "number_jobs" "files_dir" "pool_size"
dynamic-io-pool.sh worker_write_synced static_pool-static_load 100 /hdd/dynamic-io-pool 10