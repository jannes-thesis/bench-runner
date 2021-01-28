# coding: utf-8
import definitions
from adapter_log_parser import parse_result
import checkpointing

adapter_version = 'v-4'
adapter_params = tuple(['1500', '0.9'])
workload_name = 'rw_sync_10mb-node'
amount_files = 2000
log_path = 'submodules/node-io-benchmark/rws10.log'


rundef = definitions.AdapterRunDefinition(definitions.AdapterConfig(adapter_version, adapter_params), 
         definitions.Workload(definitions.BenchmarkSuite('node', '', tuple(), '', '', ''), workload_name, 'ssd', tuple([amount_files]), tuple(), tuple(), tuple()))
log_res = parse_result(log_path)
logs = {rundef: definitions.AdapterRunLog(log_res)}
checkpointing.checkpoint_adapter_logs(logs)
