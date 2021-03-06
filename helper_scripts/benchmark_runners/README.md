This directory contains wrapper scripts to run different benchmarks
testing the scaling adapter as a component in some threadpool.

# Script argument structure

## first arguments
Should define the actual workload (job for the pool workers & type of load).
Selection of adapter/static version of pool should be in flag or part of workload definition.

## next arguments
These are the parameters to the workload (e.g number of jobs, file sizes).

## before last arguments
This needs to be the param which determines which disk (ssd/hdd) is used.

## last argument
### for static pool
This needs to be the size of the threadpool if the static version without adapter is used.
### for adaptive pool
These should be the values for the adapter algorithm parameters in the same order as the adapter constructor
all in one string of form: "<arg1>,<arg2>,..<argn>"

## Example
dynamic-io-pool.sh "worker_function" "load_and_pool-variant" "number_jobs" "files_dir" "pool_size"
dynamic-io-pool.sh worker_write_synced static_pool-static_load 100 /hdd/dynamic-io-pool 10

dynamic-io-pool.sh "worker_function" "load_and_pool-variant" "number_jobs" "files_dir" "adapter_update_interval_ms"
dynamic-io-pool.sh worker_write_synced adapt_pool-static_load 100 /hdd/dynamic-io-pool "1000,10"
