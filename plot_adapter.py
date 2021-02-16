import json
import sys

from matplotlib.axes import Axes
import matplotlib.pyplot as plt

SMALL_SIZE = 14
MEDIUM_SIZE = 16
BIGGER_SIZE = 18

# plt.rc('font', size=20)          # controls default text sizes
# plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
# plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
# plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
# plt.rc('ytick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
# plt.rc('legend', fontsize=24)    # legend fontsize
# plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

plt.rc('font', size=40)          # controls default text sizes
plt.rc('axes', titlesize=35)     # fontsize of the axes title
plt.rc('axes', labelsize=35)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=40)    # fontsize of the tick labels
plt.rc('ytick', labelsize=40)    # fontsize of the tick labels
plt.rc('legend', fontsize=30)    # legend fontsize
plt.rc('figure', titlesize=40)  # fontsize of the figure title
plt.rcParams['lines.linewidth'] = 2


def plot_adapter_timeseries(name: str, axm1: Axes,
                            psizes: list[tuple[int, int]],
                            m1s: list[tuple[int, float]]):
    ax_m1 = axm1.twinx()

    ts1, psizes = list(zip(*psizes))
    ts2, m1s = list(zip(*m1s))
    m1s = [m1 * 1000 for m1 in m1s]
    ts1 = [t1 / 1000 for t1 in ts1]
    ts2 = [t2 / 1000 for t2 in ts2]
    p2a, = axm1.plot(ts1, psizes, "b-", label="pool size")
    p2b, = ax_m1.plot(ts2, m1s, "r-", label="rwchar rate")

    axm1.set_xlabel("time in seconds")
    axm1.set_ylabel("pool size")
    ax_m1.set_ylabel("rwchar rate bytes/sec")
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
                        # ax.set_title(f'{workload} {adapter_version}')
                        # ax.set_title(f'rw2mb-nosync-sync')
                        return
    raise Exception(f'adapter logs for {adapter_version} not found')


if __name__ == '__main__':
    n = int(sys.argv[1])
    if n == 1:
        fig, ax = plt.subplots(figsize=(20, 10))
        axs = [ax]
    elif n == 2:
        fig, axs = plt.subplots(figsize=(25, 15), nrows=2)
    else:
        raise Exception('support only one or two')

    for i in range(n):
        base = i * 3 + 2
        json_path = sys.argv[base]
        adapter_version = sys.argv[base + 1]
        workload = sys.argv[base + 2]
        generate_adapter_logs_figure(json_path, adapter_version, workload, axs[i])
    output_path = sys.argv[n * 3 + 2]

    axs[0].set_title('Sync 10Mb')
    axs[1].set_title('Nosync 2Mb')
    fig.tight_layout()
    fig.savefig(output_path)
