#!/bin/bash
worker_function=$1
benchmark_name=$2
num_items=$3
output_dir=$4
pool_size_or_algo_params=$5

hyperfine --min-runs 3 \
  --style basic \
  --prepare 'sudo /bin/clear_page_cache.sh' \
  "submodules/dynamic-io-pool/build/benchmark ${worker_function} ${benchmark_name} ${output_dir} ${num_items} ${pool_size_or_algo_params}" \
  --export-json "data/results/tmp_result.json"
