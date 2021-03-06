#!/bin/bash
load_type=$1
worker_function=$2
num_items=$3
output_dir=$4
if [ "$5" = "static" ]; then
  fixed_or_adaptive="fixed"
else
  fixed_or_adaptive=$5
fi
pool_size_or_algo_params=$6
param_str="single ${fixed_or_adaptive} ${pool_size_or_algo_params} ${load_type} ${worker_function} ${num_items} ${output_dir}"

hyperfine --min-runs 3 \
  --style basic \
  --prepare 'sudo /bin/clear_page_cache.sh' \
  "submodules/scaling-adapter/target/release/threadpool ${param_str}" \
  --export-json "data/results/tmp_result.json"

if [ "$fixed_or_adaptive" = "adaptive" ]; then
  sudo /bin/clear_page_cache.sh
  RUST_LOG=info submodules/scaling-adapter/target/release/threadpool $param_str 2> data/results/tmp_result.log
fi