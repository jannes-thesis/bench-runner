#!/bin/bash
worker_function=$1
benchmark_name=$2
num_items=$3
output_dir=$4
pool_size=$5

hyperfine --min-runs 3 \
  --prepare '/bin/sync; echo 3 | sudo tee /proc/sys/vm/drop_caches' \
  "${HOME}/MasterThesis/dynamic-io-pool/build/benchmark ${worker_function} ${benchmark_name} ${output_dir} ${num_items} ${pool_size}" \
  --export-json "data/results/tmp_result.json"
