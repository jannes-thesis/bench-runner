from datetime import datetime
from subprocess import run
import logging

import submodules
from definitions import AdapterRunDefinition, StaticRunDefinition
from post_run import (
    parse_result_json,
    save_new_results,
    update_known_adapter_configs,
    update_known_workloads,
    commit,
)
from pre_run import (
    get_all_workloads,
    get_new_workloads,
    get_known_workloads,
    get_known_adapter_configs,
    get_new_adapter_configs,
    get_new_adapter_run_definitions,
    get_new_static_run_definitions,
)

# timestamp = datetime.today().strftime('%Y-%m-%d-%H:%M')
# logger = logging.getLogger()
# logger.setLevel = logging.DEBUG
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# log_filename = f'data/logs/{timestamp}.log'
# file_handle = logging.FileHandler(filename=log_filename, mode='w', encoding='utf-8')
# file_handle.setLevel(logging.DEBUG)
# file_handle.setFormatter(formatter)
# console_handle = logging.StreamHandler()
# console_handle.setLevel(logging.INFO)
# console_handle.setFormatter(formatter)
# logger.addHandler(file_handle)
# logger.addHandler(console_handle)

timestamp = datetime.today().strftime("%Y-%m-%d-%H:%M")
log_filename = f"data/logs/{timestamp}.log"
console_handle = logging.StreamHandler()
console_handle.setLevel(logging.INFO)
file_handle = logging.FileHandler(log_filename)
file_handle.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[console_handle, file_handle],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging


def prepare_adapter_run(run_definition: AdapterRunDefinition):
    """ if not already on correct adapter branch, compile adapter & benchmark exes """
    if (run_definition.adapter_config.adapter_version !=
            submodules.get_current_adapter_branch()):
        logger.info(
            f'compile adapter version {run_definition.adapter_config.adapter_version}'
        )
        submodules.compile_adapter(
            run_definition.adapter_config.adapter_version)
        logger.info(f"recompile benchmarks")
        submodules.compile_benchmarks()
    else:
        logger.info(
            f'already on branch for {run_definition.adapter_config.adapter_version}, no compilation needed'
        )


def do_adapter_run(run_definition: AdapterRunDefinition) -> bool:
    prepare_adapter_run(run_definition)
    runner_script = run_definition.workload.benchmark_suite.runner_script
    first_args = run_definition.workload.using_adapter_parameters
    workload_args = [
        str(arg) for arg in run_definition.workload.workload_parameters
    ]
    disk_arg = run_definition.workload.disk
    adapter_algorithm_args = run_definition.adapter_config.adapter_parameters
    command_with_args = [
        runner_script,
        *first_args,
        *workload_args,
        disk_arg,
        *adapter_algorithm_args,
    ]
    run(command_with_args)
    return True


def do_static_run(run_definition: StaticRunDefinition) -> bool:
    runner_script = run_definition.workload.benchmark_suite.runner_script
    first_args = run_definition.workload.no_adapter_parameters
    workload_args = [
        str(arg) for arg in run_definition.workload.workload_parameters
    ]
    disk_arg = run_definition.workload.disk
    size_arg = str(run_definition.static_size)
    command_with_args = [
        runner_script, *first_args, *workload_args, disk_arg, size_arg
    ]
    run(command_with_args)
    return True


def main():
    logger.info("get new workload/adapter info")
    all_workloads = get_all_workloads()
    new_workloads = get_new_workloads(all_workloads)
    known_workloads = get_known_workloads(all_workloads)
    known_adapter_configs = get_known_adapter_configs()
    new_adapter_configs = get_new_adapter_configs(known_adapter_configs)

    logger.info("new workloads:")
    for w in new_workloads:
        logger.info(f"--> {w.description()}")

    logger.info("new adapter configs:")
    for c in new_adapter_configs:
        logger.info(f"--> {c.description()}")

    logger.info("calculate new run definitions")
    adapter_runs = get_new_adapter_run_definitions(known_workloads,
                                                   new_workloads,
                                                   known_adapter_configs,
                                                   new_adapter_configs)
    static_runs = get_new_static_run_definitions(new_workloads)

    # filtering dummy configs
    adapter_runs = [
        run for run in adapter_runs
        if run.adapter_config.adapter_version.startswith("v-")
    ]
    # delete later

    logger.info(f"{len(adapter_runs)} new adapter run defs")
    logger.info(f"{len(static_runs)} new static run defs")

    adapter_run_results = set()
    for adapter_run_def in adapter_runs:
        workload_description = adapter_run_def.workload.description()
        adapter_config_description = adapter_run_def.adapter_config.description(
        )
        logger.info(
            f"adapter run: {workload_description} with {adapter_config_description}"
        )
        do_adapter_run(adapter_run_def)
        result = parse_result_json(adapter_run_def)
        adapter_run_results.add(result)

    static_run_results = set()
    for static_run_def in static_runs:
        workload_description = static_run_def.workload.description()
        pool_size = static_run_def.static_size
        logger.info(
            f"static run: {workload_description} with size {pool_size}")
        do_static_run(static_run_def)
        result = parse_result_json(static_run_def)
        static_run_results.add(result)

    logger.info("saving results")
    save_new_results(adapter_run_results, static_run_results, timestamp)
    update_known_adapter_configs(new_adapter_configs)
    update_known_workloads(new_workloads)
    # generate new reports
    logger.info("commit new data")
    commit()


if __name__ == "__main__":
    main()
