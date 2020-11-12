import json
import os

from matplotlib import pyplot
from matplotlib.axes import Axes

from definitions import StaticResult, AdapterResult, StaticRunDefinition, \
    AdapterRunDefinition, AdapterConfig
from pre_run import get_all_workloads


def generate_report(json_path: str):
    timestamp = json_path.split('.')[0].split('/')[-1]
    report_dir = f'data/reports/{timestamp}'
    os.makedirs(report_dir)
    results = load_results(json_path)
    md_report_str = ''
    for (static_results, _) in results:
        workload_str = static_results[0].static_run.workload.full_description()
        md_report_str += f'# {workload_str}\n'
        md_report_str += f'![{workload_str} image](figures/{workload_str}.png)\n\n'
    with open(f'{report_dir}/report.md', 'w') as f:
        f.write(md_report_str)
    plot_results(results, report_dir)


def plot_results(results: set[tuple[tuple[StaticResult], tuple[AdapterResult]]], report_dir: str):
    report_figures_dir = f'{report_dir}/figures'
    os.makedirs(report_figures_dir)
    for (static_results, adapter_results) in results:
        fig, (ax1, ax2) = pyplot.subplots(nrows=1, ncols=2, figsize=(20, 10))
        max_runtime = max(
            {res.runtime_seconds + res.std_deviation for res in static_results}.union(
                {res.runtime_seconds for res in adapter_results}))
        min_runtime = min(
            {res.runtime_seconds - res.std_deviation for res in static_results}.union(
                {res.runtime_seconds for res in adapter_results}))
        plot_static(static_results, ax1, max_runtime, min_runtime)
        plot_adaptive(adapter_results, ax2, max_runtime, min_runtime)
        workload_str = static_results[0].static_run.workload.full_description()
        fig.savefig(f'{report_figures_dir}/{workload_str}.png')
        pyplot.close(fig)


def plot_static(results: list[StaticResult], ax: Axes, ylim_top: float, ylim_bottom: float):
    assert len({res.static_run.workload for res in results}) == 1
    assert len({res.static_run.static_size for res in results}) == len(results)
    xs = []
    ys = []
    stddvs = []
    for res in results:
        xs.append(res.static_run.static_size)
        ys.append(res.runtime_seconds)
        stddvs.append(res.std_deviation)

    ax.errorbar(xs, ys, yerr=stddvs, color='tab:blue', capsize=3)
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.set_xlabel('pool size')
    ax.set_ylabel('runtime in seconds')
    ax.set_ylim(top=ylim_top, bottom=ylim_bottom)
    ax.grid(color='grey', linestyle='-', linewidth=0.25, alpha=0.5)


def plot_adaptive(results: list[AdapterResult], ax: Axes, ylim_top: float, ylim_bottom: float):
    assert len({res.adapter_run.workload for res in results}) == 1
    assert len({res.adapter_run.adapter_config for res in results}) == len(results)
    xs = []
    ys = []
    stddvs = []
    for res in results:
        xs.append(res.adapter_run.adapter_config.short_description())
        ys.append(res.runtime_seconds)
        stddvs.append(res.std_deviation)

    ax.errorbar(xs, ys, yerr=stddvs, color='tab:blue', capsize=3)
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.set_xlabel('adapter config')
    ax.set_ylabel('runtime in seconds')
    ax.set_ylim(top=ylim_top, bottom=ylim_bottom)
    ax.grid(color='grey', linestyle='-', linewidth=0.25, alpha=0.5)


def load_results(json_path: str) -> set[tuple[tuple[StaticResult], tuple[AdapterResult]]]:
    """
    :param json_path: path to result file
    :return: for each bench-disk-workload-params set a tuple of static & adaptive results
    """
    with open(json_path) as f:
        r_json = json.load(f)
    all_workloads = get_all_workloads()

    tuples = set()
    for bench in r_json.keys():
        for disk in r_json[bench].keys():
            for wload in r_json[bench][disk].keys():
                for w_params in r_json[bench][disk][wload].keys():
                    static_result_dicts = r_json[bench][disk][wload][w_params]['without_adapter']
                    adapter_result_dicts = r_json[bench][disk][wload][w_params]['with_adapter']
                    workload = next(w for w in all_workloads if w.benchmark_suite.name == bench and w.disk == disk and
                                    w.name == wload and w.workload_parameters_str() == w_params)
                    static_results = tuple([StaticResult(StaticRunDefinition(res['pool_size'], workload),
                                                         res['avg_runtime_seconds'], res['runtime_stddev']) for res in
                                            static_result_dicts])
                    adapter_results = tuple([AdapterResult(
                        AdapterRunDefinition(AdapterConfig(res['adapter_version'], tuple(res['adapter_params'])),
                                             workload), res['avg_runtime_seconds'], res['runtime_stddev']) for res in
                        adapter_result_dicts])
                    tuples.add((static_results, adapter_results))
    return tuples
