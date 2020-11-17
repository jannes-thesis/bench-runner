#!/bin/bash
worker_function=$1
benchmark_name=$2
num_items=$3
output_dir=$4
static_or_adaptive=$5
pool_size_or_algo_params=$6
param_str="${worker_function} ${benchmark_name} ${output_dir} ${num_items} ${static_or_adaptive} ${pool_size_or_algo_params}"

hyperfine --min-runs 3 \
  --style basic \
  --prepare 'sudo /bin/clear_page_cache.sh' \
  "submodules/dynamic-io-pool/build/benchmark ${param_str}" \
  --export-json "data/results/tmp_result.json"
