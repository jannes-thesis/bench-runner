from subprocess import run

import submodules
from definitions import AdapterRunDefinition, StaticRunDefinition
from post_run import parse_result_json, save_new_results, update_known_adapter_configs, update_known_workloads
from pre_run import get_all_workloads, get_new_workloads, get_known_workloads, get_known_adapter_configs, \
    get_new_adapter_configs, get_new_adapter_run_definitions, get_new_static_run_definitions


def prepare_adapter_run(run_definition: AdapterRunDefinition):
    """ if not already on correct adapter branch, compile adapter & benchmark exes """
    if run_definition.adapter_config.adapter_version != submodules.get_current_adapter_branch():
        submodules.compile_adapter(run_definition.adapter_config.adapter_version)
        submodules.compile_benchmarks()


def do_adapter_run(run_definition: AdapterRunDefinition) -> bool:
    prepare_adapter_run(run_definition)
    runner_script = run_definition.workload.benchmark_suite.runner_script
    first_args = run_definition.workload.using_adapter_parameters
    workload_args = [str(arg) for arg in run_definition.workload.workload_parameters]
    disk_arg = run_definition.workload.disk
    adapter_algorithm_args = run_definition.adapter_config.adapter_parameters
    command_with_args = [runner_script, *first_args, *workload_args, disk_arg, *adapter_algorithm_args]
    run(command_with_args)
    return True


def do_static_run(run_definition: StaticRunDefinition) -> bool:
    runner_script = run_definition.workload.benchmark_suite.runner_script
    first_args = run_definition.workload.no_adapter_parameters
    workload_args = [str(arg) for arg in run_definition.workload.workload_parameters]
    disk_arg = run_definition.workload.disk
    size_arg = str(run_definition.static_size)
    command_with_args = [runner_script, *first_args, *workload_args, disk_arg, size_arg]
    run(command_with_args)
    return True


if __name__ == '__main__':
    all_workloads = get_all_workloads()
    new_workloads = get_new_workloads(all_workloads)
    known_workloads = get_known_workloads(all_workloads)
    known_adapter_configs = get_known_adapter_configs()
    new_adapter_configs = get_new_adapter_configs(known_adapter_configs)

    adapter_runs = get_new_adapter_run_definitions(known_workloads, new_workloads, known_adapter_configs,
                                                   new_adapter_configs)
    static_runs = get_new_static_run_definitions(new_workloads)

    static_run_results = set()
    for static_run_def in static_runs:
        do_static_run(static_run_def)
        result = parse_result_json(static_run_def)
        static_run_results.add(result)

    adapter_run_results = set()
    for adapter_run_def in adapter_runs:
        do_adapter_run(adapter_run_def)
        result = parse_result_json(adapter_run_def)
        adapter_run_results.add(result)

    save_new_results(adapter_run_results, static_run_results)
    update_known_adapter_configs(new_adapter_configs)
    update_known_workloads(new_workloads)
    # generate new reports
    # commit new checkpoint
    print()
