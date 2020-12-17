import json
import os
import shutil

from matplotlib import pyplot
from matplotlib.axes import Axes

from definitions import StaticResult, AdapterResult, StaticRunDefinition, \
    AdapterRunDefinition, AdapterConfig
from pre_run import get_all_workloads
from subprocess import run


def generate_report(json_path: str):
    timestamp = json_path.split('.')[0].split('/')[-1]
    report_dir = f'data/reports/{timestamp}'
    if os.path.exists(report_dir):
        shutil.rmtree(report_dir)
    os.makedirs(report_dir)
    results = load_results(json_path)
    md_report_str = ''
    benchmark_header = ''
    disk_header = ''
    workload_header = ''
    workload_params_header = ''
    for (static_results, _) in results:
        benchmark_name = static_results[
            0].static_run.workload.benchmark_suite.name
        disk_name = static_results[0].static_run.workload.disk
        workload_name = static_results[0].static_run.workload.name
        workload_params = static_results[
            0].static_run.workload.workload_params_pretty()
        if benchmark_name != benchmark_header:
            md_report_str += f'# {benchmark_name}\n## {disk_name}\n### {workload_name}\n#### {workload_params}\n'
            benchmark_header = benchmark_name
            disk_header = disk_name
            workload_header = workload_name
            workload_params_header = workload_params
        elif disk_name != disk_header:
            md_report_str += f'## {disk_name}\n### {workload_name}\n#### {workload_params}\n'
            disk_header = disk_name
            workload_header = workload_name
            workload_params_header = workload_params
        elif workload_name != workload_header:
            md_report_str += f'### {workload_name}\n#### {workload_params}\n'
            workload_header = workload_name
            workload_params_header = workload_params
        elif workload_params != workload_params_header:
            md_report_str += f'#### {workload_params}\n'
            workload_params_header = workload_params
        workload_str = static_results[0].static_run.workload.full_description()
        md_report_str += f'![{workload_str} image](figures/{workload_str}.png){{ width=100% }}\n\n'
    with open(f'{report_dir}/report.md', 'w') as f:
        f.write(md_report_str)
    plot_results(results, report_dir)
    pandoc_command = (f'cd {report_dir} && '
                      'pandoc report.md --toc -t html -o report.pdf; '
                      'cd -')
    run(pandoc_command, shell=True)


def plot_results(results: list[tuple[tuple[StaticResult],
                                     tuple[AdapterResult]]], report_dir: str):
    print(f'plotting {len(results)} pairs')
    report_figures_dir = f'{report_dir}/figures'
    if not os.path.exists(report_figures_dir):
        os.makedirs(report_figures_dir)
    for (static_results, adapter_results) in results:
        if len(static_results) > 0:
            workload_str = static_results[0].static_run.workload.full_description()
        elif len(adapter_results) > 0:
            workload_str = adapter_results[0].adapter_run.workload.full_description()
        else:
            continue 
        fig_filename = f'{report_figures_dir}/{workload_str}.png'
        if os.path.exists(fig_filename):
            os.remove(fig_filename)

        fig, (ax1, ax2) = pyplot.subplots(nrows=2, ncols=1, figsize=(20, 20))
        max_runtime = max({
                              res.runtime_seconds + res.std_deviation
                              for res in static_results
                          }.union({res.runtime_seconds
                                   for res in adapter_results}))
        min_runtime = min({
                              res.runtime_seconds - res.std_deviation
                              for res in static_results
                          }.union({res.runtime_seconds
                                   for res in adapter_results}))
        if len(static_results) > 0:
            plot_static(static_results, ax1, max_runtime, min_runtime)
        if len(adapter_results) > 0:
            plot_adaptive(adapter_results, ax2, max_runtime, min_runtime)
        fig.savefig(fig_filename)
        pyplot.close(fig)


def plot_static(results: list[StaticResult], ax: Axes, ylim_top: float,
                ylim_bottom: float):
    assert len({res.static_run.workload for res in results}) == 1
    if not len({res.static_run.static_size for res in results}) == len(results):
        print([(res.static_run.static_size, res.static_run.workload.description()) for res in results])
        assert False
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


def plot_adaptive(results: list[AdapterResult], ax: Axes, ylim_top: float,
                  ylim_bottom: float):
    assert len({res.adapter_run.workload for res in results}) == 1
    if not len({res.adapter_run.adapter_config for res in results}) == len(results):
        print([res.adapter_run.adapter_config for res in results])
        assert False

    xs = []
    ys = []
    y2s = []
    stddvs = []
    results = sorted(results, key=lambda x: x.adapter_run.adapter_config.short_description())
    for res in results:
        xs.append(res.adapter_run.adapter_config.short_description())
        ys.append(res.runtime_seconds)
        y2s.append(res.avg_pool_size)
        stddvs.append(res.std_deviation)

    p1 = ax.errorbar(xs, ys, yerr=stddvs, color='tab:blue', capsize=3, label='runtime')
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.set_xlabel('adapter config')
    ax.set_ylabel('runtime in seconds')
    ax.set_ylim(top=ylim_top, bottom=ylim_bottom)
    ax.grid(color='grey', linestyle='-', linewidth=0.25, alpha=0.5)

    ax2 = ax.twinx()
    p2 = ax2.plot(xs, y2s, 'r-', label='avg pool size')
    ax2.set_ylabel('avg pool size')

    # lines = [p1, p2]
    # ax.legend(lines, [l.get_label() for l in lines])


def load_results(
        json_path: str
) -> list[tuple[tuple[StaticResult], tuple[AdapterResult]]]:
    """
    :param json_path: path to result file
    :return: for each bench-disk-workload-params set a tuple of static & adaptive results
    """
    with open(json_path) as f:
        r_json = json.load(f)
    all_workloads = get_all_workloads()

    static_results_list = list()
    adapter_results_list = list()
    for bench in r_json.keys():
        for disk in r_json[bench].keys():
            for wload in r_json[bench][disk].keys():
                for w_params in r_json[bench][disk][wload].keys():
                    static_result_dicts = r_json[bench][disk][wload][w_params][
                        'without_adapter']
                    adapter_result_dicts = r_json[bench][disk][wload][
                        w_params]['with_adapter']
                    workload_matches = [
                        w for w in all_workloads
                        if w.benchmark_suite.name == bench and w.disk == disk
                           and w.name == wload
                           and w.workload_parameters_str() == w_params
                    ]
                    # if workload from result json is ignored/commented out, skip it
                    if len(workload_matches) == 0:
                        continue
                    elif len(workload_matches) > 1:
                        raise Exception(
                            f'more than one workload matches: {bench}, {disk}, {wload}, {w_params}'
                        )
                    workload = workload_matches[0]
                    static_results = tuple([
                        StaticResult(
                            StaticRunDefinition(res['pool_size'], workload),
                            res['avg_runtime_seconds'], res['runtime_stddev'])
                        for res in static_result_dicts
                    ])
                    adapter_results = tuple([
                        AdapterResult(
                            AdapterRunDefinition(
                                AdapterConfig(res['adapter_version'],
                                              tuple(res['adapter_params'])),
                                workload), res['avg_runtime_seconds'],
                            res['runtime_stddev'], res['avg_pool_size'], res['total_thread_creates'])
                        for res in adapter_result_dicts
                    ])
                    static_results_list.append(static_results)
                    adapter_results_list.append(adapter_results)

    def sort_key_static(results: tuple[StaticResult]) -> str:
        if len(results) > 0:
            return results[0].static_run.workload.full_description()
        else:
            return 'Z'

    def sort_key_adaptive(results: tuple[AdapterResult]) -> str:
        if len(results) > 0:
            return results[0].adapter_run.workload.full_description()
        else:
            return 'Z'

    static_results_sorted = sorted(static_results_list,
                                   key=lambda x: sort_key_static(x))
    adapter_results_sorted = sorted(adapter_results_list,
                                    key=lambda x: sort_key_adaptive(x))
    return list(zip(static_results_sorted, adapter_results_sorted))


def make_patch_spines_invisible(ax: Axes):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


# https://matplotlib.org/3.1.1/gallery/ticks_and_spines/multiple_yaxis_with_spines.html
def plot_adapter_timeseries(name: str, axq: Axes, axm1: Axes, axm2: Axes,
                            psizes: list[tuple[int, int]],
                            qsizes: list[tuple[int, int]],
                            m1s: list[tuple[int, float]],
                            m2s: list[tuple[int, float]]):
    ax_q = axq.twinx()
    ax_m1 = axm1.twinx()
    ax_m2 = axm2.twinx()

    ts1, psizes = list(zip(*psizes))
    ts2, qsizes = list(zip(*qsizes))
    ts3, m1s = list(zip(*m1s))
    ts4, m2s = list(zip(*m2s))

    # Plot 1
    p1a, = axq.plot(ts1, psizes, "b-", label="pool size")
    p1b, = ax_q.plot(ts2, qsizes, "r-", label="queue size")

    axq.set_xlabel("time in millis")
    axq.set_ylabel("pool size")
    ax_q.set_ylabel("queue size")
    axq.yaxis.label.set_color(p1a.get_color())
    ax_q.yaxis.label.set_color(p1b.get_color())

    axq.tick_params(axis='y', colors=p1a.get_color())
    ax_q.tick_params(axis='y', colors=p1b.get_color())
    axq.tick_params(axis='x')
    lines = [p1a, p1b]
    axq.legend(lines, [l.get_label() for l in lines])

    # Plot 2
    p2a, = axm1.plot(ts1, psizes, "b-", label="pool size")
    p2b, = ax_m1.plot(ts3, m1s, "r-", label="disk throughput")

    axm1.set_xlabel("time in millis")
    axm1.set_ylabel("pool size")
    ax_m1.set_ylabel("disk throughput bytes/ms")
    axm1.yaxis.label.set_color(p2a.get_color())
    ax_m1.yaxis.label.set_color(p2b.get_color())

    axm1.tick_params(axis='y', colors=p2a.get_color())
    ax_m1.tick_params(axis='y', colors=p2b.get_color())
    axm1.tick_params(axis='x')
    lines = [p2a, p2b]
    axm1.legend(lines, [l.get_label() for l in lines])

    # Plot 3
    p3a, = axm2.plot(ts1, psizes, "b-", label="pool size")
    p3b, = ax_m2.plot(ts4, m2s, "r-", label="metric two")

    axm2.set_xlabel("time in millis")
    axm2.set_ylabel("pool size")
    ax_m2.set_ylabel("metric two")
    axm2.yaxis.label.set_color(p3a.get_color())
    ax_m2.yaxis.label.set_color(p3b.get_color())

    axm2.tick_params(axis='y', colors=p3a.get_color())
    ax_m2.tick_params(axis='y', colors=p3b.get_color())
    axm2.tick_params(axis='x')
    lines = [p3a, p3b]
    axm2.legend(lines, [l.get_label() for l in lines])


def generate_adapter_logs_report(json_path: str, report_dir: str):
    report_figures_dir = f'{report_dir}/figures'
    with open(json_path) as f:
        logs_json = json.load(f)
    md_str = ''
    for b in logs_json.keys():
        md_str += f'# {b}\n'
        for d in logs_json[b].keys():
            md_str += f'## {d}\n'
            for w in logs_json[b][d].keys():
                for p in logs_json[b][d][w].keys():
                    md_str += f'### {w}-{p}\n'
                    for a in logs_json[b][d][w][p].keys():
                        md_str += f'#### {a}\n'
                        adapter_entry = logs_json[b][d][w][p][a]
                        psizes = adapter_entry['pool_size']
                        avg_psize = sum([tpl[1] for tpl in psizes]) / len(psizes)
                        qsizes = adapter_entry['queue_size']
                        m1s = adapter_entry['metric_one']
                        m2s = adapter_entry['metric_two']
                        fig, (ax1, ax2, ax3) = pyplot.subplots(nrows=3, ncols=1, figsize=(20, 30))
                        fig.subplots_adjust(right=0.75)
                        plot_adapter_timeseries(a, ax1, ax2, ax3, psizes, qsizes, m1s, m2s)
                        fig_id = f'{b}-{d}-{w}-{p}-{a}'
                        fig_filename = f'{report_figures_dir}/{fig_id}.png'
                        if os.path.exists(fig_filename):
                            os.remove(fig_filename)
                        fig.savefig(fig_filename)
                        pyplot.close(fig)
                        md_str += f'![{fig_id} image](figures/{fig_id}.png){{ width=100% }}\n'
                        md_str += f'avg pool size: {avg_psize}\n\n'
    with open(f'{report_dir}/report-adapter.md', 'w') as f:
        f.write(md_str)
    pandoc_command = (f'cd {report_dir} && '
                      'pandoc report-adapter.md --toc -t html -o report-adapter.pdf; '
                      'cd -')
    run(pandoc_command, shell=True)
