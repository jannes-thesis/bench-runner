import json

from definitions import AdapterRunDefinition, StaticRunDefinition, StaticResult, AdapterResult, AdapterRunLog, AdapterConfig, Workload


def checkpoint_results_static(static_results: set[StaticResult]):
    results_dict = {}
    workloads = {res.static_run.workload for res in static_results}
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

    with open(f'data/latest-checkpoint-static.json', 'w') as f:
        json.dump(results_dict, f, indent=4)


def checkpoint_results_adaptive(adapter_results: set[AdapterResult]):
    results_dict = {}
    workloads = {res.adapter_run.workload for res in adapter_results}
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

    with open(f'data/latest-checkpoint-adaptive.json', 'w') as f:
        json.dump(results_dict, f, indent=4)


def checkpoint_adapter_logs(logs_map: dict[AdapterRunDefinition,
                                           AdapterRunLog]):
    results_dict = {}
    workloads = {run.workload for run in logs_map.keys()}
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
                    benchmark.name][disk][workload_name][params_str] = {}

    for run in logs_map.keys():
        logs = logs_map[run].log
        results_dict[run.workload.benchmark_suite.name][run.workload.disk][
            run.workload.name][run.workload.workload_parameters_str()][
                run.adapter_config.short_description()] = logs

    with open(f'data/latest-checkpoint-adapter_logs.json', 'w') as f:
        json.dump(results_dict, f, indent=4)
