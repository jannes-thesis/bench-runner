from definitions import AdapterRunDefinition, StaticRunsDefinition


def get_new_adapter_run_definitions() -> list[AdapterRunDefinition]:
    return None


def get_new_static_run_definitions() -> list[StaticRunsDefinition]:
    return None


if __name__ == '__main__':
    # update adapter submodule
    # detect new versions & configs
    # detect new workloads
    # for each new run definition
    # -recompile adapter
    # -recompile benchmark with correct adapter
    # -do bench run
    # -parse result
    # generate new reports
    # commit new checkpoint
    print()
