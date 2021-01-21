import json
import sys

from matplotlib.axes import Axes
import matplotlib.pyplot as plt


def plot_adapter_timeseries(name: str, axm1: Axes,
                            psizes: list[tuple[int, int]],
                            m1s: list[tuple[int, float]]):
    ax_m1 = axm1.twinx()

    ts1, psizes = list(zip(*psizes))
    ts2, m1s = list(zip(*m1s))
    p2a, = axm1.plot(ts1, psizes, "b-", label="pool size")
    p2b, = ax_m1.plot(ts2, m1s, "r-", label="rwchar rate")

    axm1.set_xlabel("time in millis")
    axm1.set_ylabel("pool size")
    ax_m1.set_ylabel("rwchar rate bytes/ms")
    axm1.yaxis.label.set_color(p2a.get_color())
    ax_m1.yaxis.label.set_color(p2b.get_color())

    axm1.tick_params(axis='y', colors=p2a.get_color())
    ax_m1.tick_params(axis='y', colors=p2b.get_color())
    axm1.tick_params(axis='x')
    lines = [p2a, p2b]
    axm1.legend(lines, [l.get_label() for l in lines])


def generate_adapter_logs_figure(json_path: str, adapter_version: str, workload: str, ax: Axes):
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
                        m1s = adapter_entry['metric_one']
                        plot_adapter_timeseries(a, ax, psizes, m1s)
                        return


if __name__ == '__main__':
    n = int(sys.argv[1])
    if n == 1:
        fig, ax = plt.subplots(figsize=(20, 10))
        axs = [ax]
    elif n == 2:
        fig, axs = plt.subplots(figsize=(25, 10), ncols=2)
    else:
        raise Exception('support only one or two')

    for i in range(n):
        base = i * 3 + 2
        json_path = sys.argv[base]
        adapter_version = sys.argv[base + 1]
        workload = sys.argv[base + 2]
        generate_adapter_logs_figure(json_path, adapter_version, workload, axs[i])
    output_path = sys.argv[n * 3 + 2]

    fig.tight_layout()
    fig.savefig(output_path)
