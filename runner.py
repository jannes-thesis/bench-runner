from collections import OrderedDict

from definitions import AdapterRunDefinition, StaticRunDefinition, AdapterConfig, Workload, StaticResult, AdapterResult, \
    BenchmarkSuite
from ruamel.yaml import YAML
import json


def get_known_adapter_configs() -> set[AdapterConfig]:
    with open('data/adapter_configs.json') as f:
        configs_json = json.load(f)
    configs = set()
    for config_json in configs_json:
        version = config_json['version']
        param_names: list[str] = config_json['param_names']
        param_values: list = config_json['param_values']
        params = OrderedDict(zip(param_names, param_values))
        configs.add(AdapterConfig(version, params))
    return configs


def get_new_adapter_configs() -> set[AdapterConfig]:
    # update adapter submodule
    # detect new versions & configs
    return set()


def add_adapter_configs(new_configs: set[AdapterConfig]):
    known_configs = get_known_adapter_configs()
    all_configs = known_configs.union(new_configs)
    with open('data/adapter_configs.json', 'w') as f:
        json.dump(all_configs, f)


def get_all_workloads() -> set[Workload]:
    yaml = YAML()
    benchmark_yaml = yaml.load('configuration/benchmarks.yaml')
    benchmarks = set()
    for benchmark in benchmark_yaml['benchmarks']:
        name = benchmark['name']
        runner_script_path = f'helper_scripts/benchmark_runners/{benchmark["runner_script"]}'
        parameter_names = benchmark['parameters']
        disk_params = benchmark['disk_params']
        workloads_definition_path = f'configuration/workloads/{benchmark["workloads_definition"]}'
        benchmarks.add(
            BenchmarkSuite(name, runner_script_path, parameter_names, disk_params, workloads_definition_path))
    workloads = set()
    for benchmark in benchmarks:
        workloads_yaml = yaml.load(benchmark.workloads_definition_file)
        parameter_names = benchmark.parameter_names
        disks = benchmark.disk_params.keys()
        for workload_set in workloads_yaml['workloads']:
            name = workload_set['name']
            adapter_params = workload_set['adapter_params']
            no_adapter_params = workload_set['no_adapter_params']
            param_combos = workload_set['parameter_combos']
            static_sizes = workload_set['static_sizes']
            for disk in disks:
                for combo in param_combos:
                    params = OrderedDict()
                    for i, param_name in enumerate(parameter_names):
                        params[param_name] = combo[i]
                    workload = Workload(benchmark, name, disk,
                                        adapter_params, no_adapter_params,
                                        params, static_sizes)
                    workloads.add(workload)
    return workloads


def get_known_workloads(all_workloads: set[Workload]) -> set[Workload]:
    with open('data/known_workloads.json') as f:
        known_json = json.load(f)
    known_workload_ids = set()
    for workload in known_json:
        workload_name = workload['name']
        bench_name = workload['benchmark_name']
        known_workload_ids.add((bench_name, workload_name))
    return {w for w in all_workloads if (w.benchmark_suite.name, w.name) in known_workload_ids}


def get_new_workloads(all_workloads: set[Workload]) -> set[Workload]:
    """ get all new workloads """
    return all_workloads.difference(get_known_workloads(all_workloads))


def get_new_adapter_run_definitions(known_workloads: set[Workload], new_workloads: set[Workload],
                                    known_adapter_configs: set[AdapterConfig],
                                    new_adapter_configs: set[AdapterConfig]) -> set[AdapterRunDefinition]:
    result = set()
    all_workloads = known_workloads.union(new_workloads)
    all_configs = known_adapter_configs.union(new_adapter_configs)
    for workload in all_workloads:
        for config in new_adapter_configs:
            result.add(AdapterRunDefinition(config, workload))
    for config in all_configs:
        for workload in new_workloads:
            result.add(AdapterRunDefinition(config, workload))
    return result


def get_new_static_run_definitions(new_workloads: set[Workload]) -> list[StaticRunDefinition]:
    result = list()
    for workload in new_workloads:
        for size in workload.static_sizes:
            result.append(StaticRunDefinition(size, workload))
    return result


def prepare_adapter_run(run_definition: AdapterRunDefinition):
    """ if not already on correct adapter branch, compile adapter & benchmark exe """
    return


def do_adapter_run(run_definition: AdapterRunDefinition) -> bool:
    prepare_adapter_run(run_definition)
    return False


def parse_adapter_result(run_definition: AdapterRunDefinition) -> AdapterResult:
    return None


def do_static_run(run_definition: StaticRunDefinition) -> bool:
    return False


def parse_static_result(run_definition: StaticRunDefinition) -> StaticResult:
    return None


def save_new_results(adapter_results: set[AdapterResult], static_results: set[StaticResult]):
    return


if __name__ == '__main__':
    new_adapter_configs = get_new_adapter_configs()
    known_adapter_configs = get_known_adapter_configs()
    new_workloads = get_new_workloads()
    known_workloads = get_known_workloads()

    adapter_runs = get_new_adapter_run_definitions(known_workloads, new_workloads, known_adapter_configs,
                                                   new_adapter_configs)
    static_runs = get_new_static_run_definitions(new_workloads)

    static_run_results = set()
    for static_run_def in static_runs:
        do_static_run(static_run_def)
        result = parse_static_result(static_run_def)
        static_run_results.add(result)

    adapter_run_results = set()
    for adapter_run_def in adapter_runs:
        do_adapter_run(adapter_run_def)
        result = parse_adapter_result(adapter_run_def)
        adapter_run_results.add(result)

    save_new_results(adapter_run_results, static_run_results)
    # generate new reports
    # commit new checkpoint
    print()
