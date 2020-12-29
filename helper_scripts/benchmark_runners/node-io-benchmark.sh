#!/bin/bash
workload_script=$1
amount_files=$2
output_dir=$3
pool_size_or_algo_params=$5
if [ "$4" = "static" ]; then
  export UV_THREADPOOL_SIZE="${pool_size_or_algo_params}"
  cmd="submodules/node-io-benchmark/node_original submodules/node-io-benchmark/node_scripts/${workload_script} ${output_dir} ${amount_files}"
else
  export ALGO_PARAMS="${pool_size_or_algo_params}"
  cmd="submodules/node-io-benchmark/node_adaptive submodules/node-io-benchmark/node_scripts/${workload_script} ${output_dir} ${amount_files}"
fi

hyperfine --min-runs 3 \
  --style basic \
  --prepare 'sudo /bin/clear_page_cache' \
  "${cmd}" \
  --export-json "data/results/tmp_result.json"

if [ "$4" = "adaptive" ]; then
  sudo /bin/clear_page_cache
  export RUST_LOG=info
  $cmd 2> data/results/tmp_result.log
fi