import sys
from reports import load_results

def print_adapter_res(workload: str, adapter_version: str, results):
    for (static_results, adapter_results) in results:
        if workload == static_results[0].static_run.workload.name:
            result = next(iter([res for res in adapter_results if res.adapter_run.adapter_config.short_description() == adapter_version]))
    print(f'runtime: {result.runtime_seconds}, stddev: {result.std_deviation}, psize: {result.avg_pool_size}')


def print_fixed_res(workload: str, psize: int, results):
    for (static_results, adapter_results) in results:
        if workload == static_results[0].static_run.workload.name:
            result = next(iter([res for res in static_results if res.static_run.static_size == psize]))
    print(f'runtime: {result.runtime_seconds}, stddev: {result.std_deviation}, psize: {psize}')


if __name__ == '__main__':
    workload = sys.argv[1]
    config = sys.argv[2]
    if len(sys.argv) == 4:
        results = load_results(sys.argv[3])
    else:
        results = load_results('data/results/all_results.json')
    if 'v-' in config:
        print_adapter_res(workload, config, results)
    else:
        psize = int(config)
        print_fixed_res(workload, psize, results)