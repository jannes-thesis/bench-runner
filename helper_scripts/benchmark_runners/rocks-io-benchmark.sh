#!/bin/bash
workload_name=$1
amount_keys=$2
output_dir=$3
if [ "$4" = "static" ]; then
  run_script="run_fixed.sh"
  executable="db_bench_original"
else
  run_script="run_adaptive.sh"
  executable="db_bench_adaptive"
fi
pool_size_or_algo_params=$5
param_str="${pool_size_or_algo_params} ${workload_name} ${num_keys} ${output_dir}"

cd submodules/rocks-io-benchmark/benchmarking
ln "../${executable}" db_bench

hyperfine --min-runs 3 \
  --style basic \
  --prepare 'sudo /bin/clear_page_cache' \
  --cleanup "rm -rf ${output_dir}/benchmark-data" \
  "${run_script} ${param_str}" \
  --export-json "../../../data/results/tmp_result.json"

if [ "$fixed_or_adaptive" = "adaptive" ]; then
  sudo /bin/clear_page_cache
  export RUST_LOG=info
  $run_script $param_str 2> ../../../data/results/tmp_result.log
fi
rm -rf "${output_dir}/benchmark-data"
cd ../../..