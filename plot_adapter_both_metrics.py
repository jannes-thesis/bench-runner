import json
import sys

from matplotlib.axes import Axes
import matplotlib.pyplot as plt

SMALL_SIZE = 14
MEDIUM_SIZE = 16
BIGGER_SIZE = 18

plt.rc('font', size=20)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=24)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


def plot_adapter_timeseries(name: str, axm1: Axes,
                            psizes: list[tuple[int, int]],
                            m1s: list[tuple[int, float]],
                            metric_name: str):
    ax_m1 = axm1.twinx()

    ts1, psizes = list(zip(*psizes))
    ts2, m1s = list(zip(*m1s))
    m1s = [m1 * 1000 for m1 in m1s]
    ts1 = [t1 / 1000 for t1 in ts1]
    ts2 = [t2 / 1000 for t2 in ts2]
    p2a, = axm1.plot(ts1, psizes, "b-", label="pool size")
    p2b, = ax_m1.plot(ts2, m1s, "r-", label=metric_name)

    axm1.set_xlabel("time in seconds")
    axm1.set_ylabel("pool size")
    ax_m1.set_ylabel(metric_name)
    axm1.yaxis.label.set_color(p2a.get_color())
    ax_m1.yaxis.label.set_color(p2b.get_color())

    axm1.tick_params(axis='y', colors=p2a.get_color())
    ax_m1.tick_params(axis='y', colors=p2b.get_color())
    axm1.tick_params(axis='x')
    lines = [p2a, p2b]
    axm1.legend(lines, [l.get_label() for l in lines])


def generate_adapter_logs_figure(json_path: str, adapter_version: str, workload: str, ax: Axes, metric: str, metric_name: str):
    with open(json_path) as f:
        logs_json = json.load(f)
    for b in logs_json.keys():
        for d in logs_json[b].keys():
            for w in logs_json[b][d].keys():
                if w != workload:
                    continue
                for p in logs_json[b][d][w].keys():
                    for a in logs_json[b][d][w][p].keys():
                        if a != adapter_version:
                            continue
                        adapter_entry = logs_json[b][d][w][p][a]
                        psizes = adapter_entry['pool_size']
                        ms = adapter_entry[metric]
                        plot_adapter_timeseries(a, ax, psizes, ms, metric_name)
                        ax.set_title(f'{workload} {adapter_version}')
                        return
    raise Exception(f'adapter logs for {adapter_version} not found')


if __name__ == '__main__':
    json_path = sys.argv[1]
    adapter_version = sys.argv[2]
    workload = sys.argv[3]
    output_path = sys.argv[4]

    fig, axs = plt.subplots(figsize=(25, 15), nrows=2)

    generate_adapter_logs_figure(json_path, adapter_version, workload, axs[0], 'metric_one', 'rwchar rate')
    generate_adapter_logs_figure(json_path, adapter_version, workload, axs[1], 'metric_two', 'avg syscalltime')

    fig.tight_layout()
    fig.savefig(output_path)
