import dataclasses
import logging
from datetime import datetime
from subprocess import run
import shutil

import submodules
from adapter_log_parser import log_to_avg_pool_size, log_to_total_thread_creates
from definitions import AdapterRunDefinition, StaticRunDefinition, AdapterResult
from checkpointing import checkpoint_results_adaptive, checkpoint_results_static, checkpoint_adapter_logs, \
    is_checkpointed
from post_run import (
    parse_result_json,
    parse_adapter_log,
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
from reports import generate_report, generate_adapter_logs_report

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
        submodules.compile_benchmarks(adaptive=True)
    else:
        logger.info(
            f'already on branch for {run_definition.adapter_config.adapter_version}, no compilation needed'
        )


def prepare_static_runs():
    """ compile all submodules master branches """
    submodules.compile_adapter('master')
    submodules.compile_benchmarks(adaptive=False)


def do_adapter_run(run_definition: AdapterRunDefinition) -> bool:
    prepare_adapter_run(run_definition)
    runner_script = run_definition.workload.benchmark_suite.runner_script
    first_args = run_definition.workload.using_adapter_parameters
    workload_args = [
        str(arg) for arg in run_definition.workload.workload_parameters
    ]
    disk_arg = dataclasses.asdict(
        run_definition.workload.benchmark_suite
    )[f'disk_param_{run_definition.workload.disk}']
    adapter_algorithm_args_string = run_definition.adapter_config.adapter_params_str()
    command_with_args = [
        runner_script,
        *first_args,
        *workload_args,
        disk_arg,
        'adaptive',
        adapter_algorithm_args_string
    ]
    command_str = ' '.join(command_with_args)
    logger.info(f'command: {command_str}')
    result = run(command_with_args, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f'non-zero exit code for adapter run, stderr:')
        logger.error(f'\n{result.stderr}')
        return False
    return True


def do_static_run(run_definition: StaticRunDefinition) -> bool:
    runner_script = run_definition.workload.benchmark_suite.runner_script
    first_args = run_definition.workload.no_adapter_parameters
    workload_args = [
        str(arg) for arg in run_definition.workload.workload_parameters
    ]
    disk_arg = dataclasses.asdict(
        run_definition.workload.benchmark_suite
    )[f'disk_param_{run_definition.workload.disk}']
    size_arg = str(run_definition.static_size)
    command_with_args = [
        runner_script, *first_args, *workload_args, disk_arg, 'static', size_arg
    ]
    command_str = ' '.join(command_with_args)
    logger.info(f'command: {command_str}')
    result = run(command_with_args, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f'non-zero exit code for adapter run, stderr:')
        logger.error(f'\n{result.stderr}')
        return False
    return True


def get_ignored_adapter_versions() -> set[str]:
    with open('configuration/exclude_adapters.txt') as f:
        lines = f.readlines()
    return {line.strip() for line in lines}


def is_root() -> bool:
    output = run(['id', '-u'], capture_output=True, text=True).stdout
    return output.strip() == '0'


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

    # filter out dummy/ignored adapter versions
    ignored_adapter_versions = get_ignored_adapter_versions()
    adapter_runs = [
        run for run in adapter_runs
        if run.adapter_config.adapter_version.startswith(
            "v-") and run.adapter_config.adapter_version not in ignored_adapter_versions
    ]

    n_adapter_runs = len(adapter_runs)
    n_static_runs = len(static_runs)
    # filter already checkpointed results
    # TODO: actually load the results, otherwise they won't be saved
    adapter_runs = [run for run in adapter_runs if not is_checkpointed(run)]
    static_runs = [run for run in static_runs if not is_checkpointed(run)]
    n_adapter_checkpointed = n_adapter_runs - len(adapter_runs)
    n_static_checkpointed = n_static_runs - len(static_runs)
    logger.info(f"adapter run defs: {n_adapter_runs} new - {n_adapter_checkpointed} checkpointed")
    logger.info(f"static run defs: {n_static_runs} new - {n_static_checkpointed} checkpointed")

    # sort adapter runs by version to minimize compilations
    adapter_runs = sorted(
        adapter_runs, key=lambda x: x.adapter_config.adapter_version)
    n_failed_runs = 0

    # ---- ADAPTER RUNS ----
    adapter_run_results = set()
    adapter_run_logs = {}
    amount_adapter_runs = len(adapter_runs)
    for i, adapter_run_def in enumerate(adapter_runs):
        workload_description = adapter_run_def.workload.description()
        adapter_config_description = adapter_run_def.adapter_config.description(
        )
        logger.info(
            f"adapter run {i}/{amount_adapter_runs}: {workload_description} with {adapter_config_description}"
        )
        success = do_adapter_run(adapter_run_def)
        if not success:
            logger.error('ADAPTER_RUN FAIL')
            n_failed_runs += 1
            continue
        # parse log & result
        result = parse_result_json(adapter_run_def)
        run_log = parse_adapter_log()
        if run_log is not None:
            adapter_run_logs[adapter_run_def] = run_log
            checkpoint_adapter_logs(adapter_run_logs)
            avg_pool_size = log_to_avg_pool_size(run_log.log)
            total_thread_creates = log_to_total_thread_creates(run_log.log)
            result = AdapterResult(result.adapter_run, result.runtime_seconds,
                                   result.std_deviation, avg_pool_size, total_thread_creates)
        adapter_run_results.add(result)
        checkpoint_results_adaptive(adapter_run_results)

    # ---- STATIC RUNS ----
    static_run_results = set()
    amount_static_runs = len(static_runs)
    prepare_static_runs()
    for i, static_run_def in enumerate(static_runs):
        workload_description = static_run_def.workload.description()
        pool_size = static_run_def.static_size
        logger.info(
            f"static run {i}/{amount_static_runs}: {workload_description} with size {pool_size}")
        success = do_static_run(static_run_def)
        if not success:
            logger.error('STATIC RUN FAIL')
            n_failed_runs += 1
            continue
        result = parse_result_json(static_run_def)
        static_run_results.add(result)
        checkpoint_results_static(static_run_results)

    if n_failed_runs > 0:
        logger.error(f'{n_failed_runs} runs failed, check the log!')
    logger.info("saving results")
    save_new_results(adapter_run_results, static_run_results, timestamp)
    update_known_adapter_configs(new_adapter_configs)
    update_known_workloads(new_workloads)
    logger.info("generating report")
    generate_report(f'data/results/all_results-{timestamp}.json')
    generate_adapter_logs_report(
        'data/latest-checkpoint-adapter_logs.json', f'data/reports/all_results-{timestamp}')
    shutil.move('data/latest-checkpoint-adapter_logs.json',
                f'data/results/result-{timestamp}-alogs.json')
    # logger.info("commit new data")
    # commit()


if __name__ == "__main__":
    main()
