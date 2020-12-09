#!/bin/bash
workload=$1
num_items=$2
output_dir=$3
if [ "$4" = "static" ]; then
  fixed_or_adaptive="fixed"
else
  fixed_or_adaptive=$4
fi
pool_size_or_algo_params=$5
param_str="multi ${fixed_or_adaptive} ${pool_size_or_algo_params} ${workload} ${num_items} ${output_dir}"

hyperfine --min-runs 3 \
  --style basic \
  --prepare 'sudo /bin/clear_page_cache.sh' \
  "submodules/scaling-adapter/target/release/threadpool ${param_str}" \
  --export-json "data/results/tmp_result.json"

if [ "$fixed_or_adaptive" = "adaptive" ]; then
  sudo /bin/clear_page_cache.sh
  RUST_LOG=info "submodules/scaling-adapter/target/release/threadpool ${param_str}" 2> data/results/tmp_result.log
fi