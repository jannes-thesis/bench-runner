#!/bin/bash
worker_function=$1
benchmark_name=$2
num_items=$3
output_dir=$4
fixed_or_adaptive=$5
pool_size_or_algo_params=$6
param_str="${fixed_or_adaptive} ${pool_size_or_algo_params} ${benchmark_name} ${worker_function} ${num_items} ${output_dir}"

hyperfine --min-runs 3 \
  --style basic \
  --prepare 'sudo /bin/clear_page_cache.sh' \
  "submodules/scaling-adapter/target/release/threadpool ${param_str}" \
  --export-json "data/results/tmp_result.json"
