# FOR PLOTTING CH5 figures
from typing import Tuple
from definitions import AdapterResult, StaticResult
import matplotlib.pyplot as plt
import numpy as np
from reports import load_results
from plot_adapter import generate_adapter_logs_figure

plt.rc('font', size=40)          # controls default text sizes
plt.rc('axes', titlesize=40)     # fontsize of the axes title
plt.rc('axes', labelsize=40)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=35)    # fontsize of the tick labels
plt.rc('ytick', labelsize=35)    # fontsize of the tick labels
plt.rc('legend', fontsize=40)    # legend fontsize
plt.rc('figure', titlesize=40)  # fontsize of the figure title
plt.rcParams['lines.linewidth'] = 2

workload = 'ssd-fillseq-50000000'
workload_no_amount = 'fillseq'
adapter_version = 'v-6-1500,0.9'
adapter_version2 = 'v-6-1000,0.9'
adapter_logs = 'data/results/result-2021-02-03-17:06-alogs.json'
static_sizes = [2, 12]

def find_results(workload: str, results) -> Tuple[AdapterResult, AdapterResult, list[StaticResult]]:
    """ return adapter, watermark, optimal static results """
    for (static_results, adapter_results) in results:
        if len(static_results) > 0:
            if workload == static_results[0].static_run.workload.description():
                static_ress = []
                for size in static_sizes:
                    static_res = next(iter([res for res in static_results if res.static_run.static_size == size]))
                    static_ress.append(static_res)
                adapter_res = next(iter([res for res in adapter_results if res.adapter_run.adapter_config.short_description() == adapter_version]))
                adapter_res2 = next(iter([res for res in adapter_results if res.adapter_run.adapter_config.short_description() == adapter_version2]))
                return adapter_res, adapter_res2, static_ress
    raise Exception(f'{workload} not found')


if __name__ == '__main__':
    results = load_results('data/results/all_results.json')
    fixed_runtime_means = []
    fixed_runtime_stddevs = []
    adapter_res, adapter_res2, fixed_ress = find_results(workload, results)
    adapter_runtime_mean = adapter_res.runtime_seconds
    adapter_runtime_stddev = adapter_res.std_deviation
    adapter_runtime_mean2 = adapter_res2.runtime_seconds
    adapter_runtime_stddev2 = adapter_res2.std_deviation

    fixed_runtime_means = [round(m, 1) for m in fixed_runtime_means]
    adapter_runtime_mean = round(adapter_runtime_mean, 1)
    adapter_runtime_mean2 = round(adapter_runtime_mean2, 1)
    
    print(adapter_res.avg_pool_size)
    print(adapter_res2.avg_pool_size)

    for fixed_res in fixed_ress:
        fixed_runtime_means.append(fixed_res.runtime_seconds)
        fixed_runtime_stddevs.append(fixed_res.std_deviation)

    
    x = np.arange(1)  # the label locations
    width = 0.2  # the width of the bars
    
    # fig, (ax, ax2) = plt.subplots(figsize=(25, 10), ncols=2, gridspec_kw={'width_ratios': [2, 3]})
    fig, ax = plt.subplots(figsize=(25, 10))
    if len(static_sizes) != 2:
        raise Exception('adapt script for different amount static results')
    rects1 = ax.bar(x - width * 3 / 2, fixed_runtime_means[0], width, label=f'fixed {static_sizes[0]}', yerr=fixed_runtime_stddevs[0], color='cornflowerblue')
    rects2 = ax.bar(x - width / 2, fixed_runtime_means[1], width, label=f'fixed {static_sizes[1]}', yerr=fixed_runtime_stddevs[1], color='red')
    rects3 = ax.bar(x + width / 2, adapter_runtime_mean, width, label='adaptive-1500,0.9', yerr=adapter_runtime_stddev, color='seagreen')
    rects4 = ax.bar(x + width * 3 /2, adapter_runtime_mean2, width, label='adaptive-1000,0.9', yerr=adapter_runtime_stddev2, color='olive')
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Runtime in seconds')
    ax.set_xticks(x)
    ax.set_xticklabels([''])
    ax.legend(loc='lower center')
    ax.set_aspect('auto')
    
    max_stddev = max(max(fixed_runtime_stddevs), adapter_runtime_stddev, adapter_runtime_stddev2)
    min_mean = min(min(fixed_runtime_means), adapter_runtime_mean, adapter_runtime_mean2)
    max_mean = max(max(fixed_runtime_means), adapter_runtime_mean, adapter_runtime_mean2)
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = round(rect.get_height(), 2)
            if height > 0.9 * max_mean:
                ypos = height - max_stddev - 5
            else:
                ypos = height + max_stddev + 5
            ypos = max_mean - max_stddev - 10
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, ypos),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    autolabel(rects4)

    # generate_adapter_logs_figure(adapter_logs, adapter_version, workload_no_amount, ax2)
    fig.tight_layout()
    fig.savefig('hotos-rocks.png')