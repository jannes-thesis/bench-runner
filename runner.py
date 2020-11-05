from definitions import AdapterRunDefinition, StaticRunDefinition, AdapterConfig, Workload, StaticResult, AdapterResult


def get_known_adapter_configs() -> set[AdapterConfig]:
    return set()


def get_new_adapter_configs() -> set[AdapterConfig]:
    # update adapter submodule
    # detect new versions & configs
    return set()


def add_adapter_configs(new_configs: set[AdapterConfig]):
    return


def get_known_workloads() -> set[Workload]:
    return set()


def get_new_workloads() -> set[Workload]:
    """ get all new workloads + workloads with changed pool size options """
    return None


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
