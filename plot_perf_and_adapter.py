# FOR PLOTTING CH5 figures
from typing import Tuple
from definitions import AdapterResult, StaticResult
import matplotlib.pyplot as plt
import numpy as np
from reports import load_results
from plot_adapter import generate_adapter_logs_figure

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

# workload = 'ssd-rw_rwbuf_rw_2mb_oneshot-15000'
workload = 'ssd-rw2mb_30ms_oneshot-10000'
# workload_no_amount = 'rw_rwbuf_rw_2mb_oneshot'
workload_no_amount = 'rw2mb_30ms_oneshot'
adapter_version = 'v-4-800,0.97'
# adapter_logs = 'data/results/result-2021-01-20-19:47-alogs.json'
adapter_logs = 'data/results/result-2021-01-25-21:48-alogs.json'
# static_sizes = [16, 64, 32]
static_sizes = [10, 16, 24]

def find_results(workload: str, results) -> Tuple[AdapterResult, list[StaticResult]]:
    """ return adapter, watermark, optimal static results """
    for (static_results, adapter_results) in results:
        if len(static_results) > 0:
            if workload == static_results[0].static_run.workload.description():
                static_ress = []
                for size in static_sizes:
                    static_res = next(iter([res for res in static_results if res.static_run.static_size == size]))
                    static_ress.append(static_res)
                adapter_res = next(iter([res for res in adapter_results if res.adapter_run.adapter_config.short_description() == adapter_version]))
                return adapter_res, static_ress
    raise Exception(f'{workload} not found')


if __name__ == '__main__':
    results = load_results('data/results/all_results.json')
    fixed_runtime_means = []
    fixed_runtime_stddevs = []
    adapter_res, fixed_ress = find_results(workload, results)
    adapter_runtime_mean = adapter_res.runtime_seconds
    adapter_runtime_stddev = adapter_res.std_deviation
    
    print(adapter_res.avg_pool_size)

    for fixed_res in fixed_ress:
        fixed_runtime_means.append(fixed_res.runtime_seconds)
        fixed_runtime_stddevs.append(fixed_res.std_deviation)

    
    x = np.arange(1)  # the label locations
    width = 0.25  # the width of the bars
    
    fig, (ax, ax2) = plt.subplots(figsize=(25, 10), ncols=2, gridspec_kw={'width_ratios': [1, 2]})
    if len(static_sizes) != 3:
        raise Exception('adapt script for different amount static results')
    rects1 = ax.bar(x - width/2*3, fixed_runtime_means[0], width, label=f'fixed {static_sizes[0]}', yerr=fixed_runtime_stddevs[0])
    rects2 = ax.bar(x - width/2, fixed_runtime_means[1], width, label=f'fixed {static_sizes[1]}', yerr=fixed_runtime_stddevs[1])
    rects3 = ax.bar(x + width/2, fixed_runtime_means[2], width, label=f'fixed {static_sizes[2]}', yerr=fixed_runtime_stddevs[2])
    rects4 = ax.bar(x + width/2*3, adapter_runtime_mean, width, label='adaptive', yerr=adapter_runtime_stddev)
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Runtime in seconds')
    ax.set_xticks(x)
    ax.set_xticklabels([workload])
    ax.legend(loc='lower center')
    ax.set_aspect('auto')
    
    max_stddev = max(max(fixed_runtime_stddevs), adapter_runtime_stddev)
    min_mean = min(min(fixed_runtime_means), adapter_runtime_mean)
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = round(rect.get_height(), 2)
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, min_mean - max_stddev - 10),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    autolabel(rects4)

    generate_adapter_logs_figure(adapter_logs, adapter_version, workload_no_amount, ax2)
    fig.tight_layout()
    fig.savefig('ch5-rust-multi-phase.png')