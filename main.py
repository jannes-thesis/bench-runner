from datetime import datetime
from subprocess import run
import logging

import submodules
from definitions import AdapterRunDefinition, StaticRunDefinition
from post_run import parse_result_json, save_new_results, update_known_adapter_configs, update_known_workloads, commit
from pre_run import get_all_workloads, get_new_workloads, get_known_workloads, get_known_adapter_configs, \
    get_new_adapter_configs, get_new_adapter_run_definitions, get_new_static_run_definitions

timestamp = datetime.today().strftime('%Y-%m-%d-%H:%M')
logger = logging.getLogger()
file_handle = logging.FileHandler(filename=f'data/logs/{timestamp}.log', encoding='utf-8')
file_handle.level = logging.DEBUG
console_handle = logging.StreamHandler()
console_handle.level = logging.INFO
logger.addHandler(file_handle)
logger.addHandler(console_handle)


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


def main():
    logger.info('get new workload/adapter info')
    all_workloads = get_all_workloads()
    new_workloads = get_new_workloads(all_workloads)
    known_workloads = get_known_workloads(all_workloads)
    known_adapter_configs = get_known_adapter_configs()
    new_adapter_configs = get_new_adapter_configs(known_adapter_configs)

    logger.info('calculate new run definitions')
    adapter_runs = get_new_adapter_run_definitions(known_workloads, new_workloads, known_adapter_configs,
                                                   new_adapter_configs)
    static_runs = get_new_static_run_definitions(new_workloads)

    static_run_results = set()
    for static_run_def in static_runs:
        logger.info(f'static run: {static_run_def.workload.description()} with size {static_run_def.static_size}')
        do_static_run(static_run_def)
        result = parse_result_json(static_run_def)
        static_run_results.add(result)

    adapter_run_results = set()
    for adapter_run_def in adapter_runs:
        logger.info(
            f'adapter run: {adapter_run_def.workload.description()} with {adapter_run_def.adapter_config.description()}')
        do_adapter_run(adapter_run_def)
        result = parse_result_json(adapter_run_def)
        adapter_run_results.add(result)

    logger.info('saving results')
    save_new_results(adapter_run_results, static_run_results, timestamp)
    update_known_adapter_configs(new_adapter_configs)
    update_known_workloads(new_workloads)
    # generate new reports
    logger.info('commit new data')
    commit()


if __name__ == '__main__':
    main()
