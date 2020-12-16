import json
import os
from datetime import datetime
from subprocess import run, DEVNULL
from typing import Union

from definitions import AdapterRunDefinition, StaticRunDefinition, StaticResult, AdapterResult, AdapterRunLog, \
    AdapterConfig, Workload
from adapter_log_parser import parse_result


def parse_result_json(run_definition: Union[AdapterRunDefinition, StaticRunDefinition]) -> \
        Union[AdapterResult, StaticResult]:
    with open('data/results/tmp_result.json') as f:
        result_json = json.load(f)
    avg_runtime_seconds = result_json['results'][0]['mean']
    runtime_stddev = result_json['results'][0]['stddev']
    os.remove('data/results/tmp_result.json')
    if type(run_definition) == AdapterRunDefinition:
        return AdapterResult(run_definition, avg_runtime_seconds,
                             runtime_stddev, 0, 0)
    else:
        return StaticResult(run_definition, avg_runtime_seconds,
                            runtime_stddev)


def parse_adapter_log() -> Union[AdapterRunLog, None]:
    log_path = 'data/results/tmp_result.log'
    if os.path.exists(log_path):
        result = parse_result(log_path)
        os.remove(log_path)
        return AdapterRunLog(result)
    else:
        return None


def merge_results(results_a: dict, results_b: dict):
    """ merge all entries of a into b """
    for benchmark in results_a.keys():
        for disk in ['hdd', 'ssd']:
            for workload_name in results_a[benchmark][disk].keys():
                for params_str in results_a[benchmark][disk][
                    workload_name].keys():
                    adapter_results = results_a[benchmark][disk][
                        workload_name][params_str]['with_adapter']
                    static_results = results_a[benchmark][disk][workload_name][
                        params_str]['without_adapter']
                    if benchmark not in results_b:
                        results_b[benchmark] = {}
                    if disk not in results_b[benchmark]:
                        results_b[benchmark][disk] = {}
                    if workload_name not in results_b[benchmark][disk]:
                        results_b[benchmark][disk][workload_name] = {}
                    if params_str not in results_b[benchmark][disk][
                        workload_name]:
                        results_b[benchmark][disk][workload_name][
                            params_str] = {
                            'with_adapter': adapter_results,
                            'without_adapter': static_results
                        }
                    else:
                        results_b[benchmark][disk][workload_name][params_str][
                            'with_adapter'].extend(adapter_results)
                        results_b[benchmark][disk][workload_name][params_str][
                            'without_adapter'].extend(static_results)


def save_new_results(adapter_results: set[AdapterResult],
                     static_results: set[StaticResult], timestamp: str):
    results_dict = {}
    workloads = {res.adapter_run.workload
                 for res in adapter_results
                 }.union({res.static_run.workload
                          for res in static_results})
    benchmark_suites = {workload.benchmark_suite for workload in workloads}
    for benchmark in benchmark_suites:
        benchmark_workloads = {
            workload
            for workload in workloads if workload.benchmark_suite == benchmark
        }
        benchmark_workload_names = {
            workload.name
            for workload in benchmark_workloads
        }
        results_dict[benchmark.name] = {}
        for disk in ['hdd', 'ssd']:
            results_dict[benchmark.name][disk] = {
                w_name: {}
                for w_name in benchmark_workload_names
            }
            for (workload_name, params_str) in {(w.name,
                                                 w.workload_parameters_str())
                                                for w in benchmark_workloads
                                                if w.disk == disk}:
                results_dict[
                    benchmark.name][disk][workload_name][params_str] = {
                    'with_adapter': [],
                    'without_adapter': []
                }

    for res in adapter_results:
        result_entry = {
            'adapter_version': res.adapter_run.adapter_config.adapter_version,
            'adapter_params':
                res.adapter_run.adapter_config.adapter_parameters,
            'avg_runtime_seconds': res.runtime_seconds,
            'runtime_stddev': res.std_deviation
        }
        target_list = results_dict[
            res.adapter_run.workload.benchmark_suite.name][
            res.adapter_run.workload.disk][res.adapter_run.workload.name][
            res.adapter_run.workload.workload_parameters_str(
            )]['with_adapter']
        target_list.append(result_entry)
    static_results = sorted(static_results,
                            key=lambda x: x.static_run.static_size)
    for res in static_results:
        result_entry = {
            'pool_size': res.static_run.static_size,
            'avg_runtime_seconds': res.runtime_seconds,
            'runtime_stddev': res.std_deviation
        }
        target_list = results_dict[
            res.static_run.workload.benchmark_suite.name][
            res.static_run.workload.disk][res.static_run.workload.name][
            res.static_run.workload.workload_parameters_str(
            )]['without_adapter']
        target_list.append(result_entry)

    with open(f'data/results/result-{timestamp}.json', 'w') as f:
        json.dump(results_dict, f, indent=4)
    with open('data/results/all_results.json') as f:
        all_results = json.load(f)
    merge_results(results_dict, all_results)
    with open('data/results/all_results.json', 'w') as f:
        json.dump(all_results, f, indent=4)
    with open(f'data/results/all_results-{timestamp}.json', 'w') as f:
        json.dump(all_results, f, indent=4)


def update_known_adapter_configs(new_configs: set[AdapterConfig]):
    to_add = [{
        'version': conf.adapter_version,
        'param_values': conf.adapter_parameters
    } for conf in new_configs]
    with open('data/adapter_configs.json') as f:
        current = json.load(f)
        current.extend(to_add)
    with open('data/adapter_configs.json', 'w') as f:
        json.dump(current, f, indent=4)


def update_known_workloads(new_workloads: set[Workload]):
    to_add = {w.full_description() for w in new_workloads}
    with open('data/known_workloads.txt') as f:
        current = {line.strip() for line in f.readlines()}
        current = current.union(to_add)
    with open('data/known_workloads.txt', 'w') as f:
        lines = sorted({s + '\n' for s in current})
        f.writelines(lines)


def commit():
    run(['git', 'add', '.'], stdout=DEVNULL, stderr=DEVNULL)
    run(['git', 'commit', '-m', 'Add new results'],
        stdout=DEVNULL,
        stderr=DEVNULL)
