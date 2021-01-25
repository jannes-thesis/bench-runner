# FOR PLOTTING CH5 figures
from typing import Tuple
from definitions import AdapterResult, StaticResult
import matplotlib.pyplot as plt
import numpy as np
from reports import load_results

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

# adapter_version = 'v-4-1000,0.9'
adapter_version = 'v-6-800,0.97'

# key: workload, value: tuple default/optimal static size
workload_map = {'ssd-rw_sync_10mb-node-2000': (4, 48),
                'ssd-rw_nosync_2mb-node-20000': (4, 48)}


def find_results(workload: str, results) -> Tuple[AdapterResult, StaticResult, StaticResult]:
    """ return adapter, default static, optimal static results """
    for (static_results, adapter_results) in results:
        if len(static_results) > 0:
            if workload == static_results[0].static_run.workload.description():
                default_static_res = next(iter([res for res in static_results if res.static_run.static_size == workload_map[workload][0]]))
                optimal_static_res = next(iter([res for res in static_results if res.static_run.static_size == workload_map[workload][1]]))
                adapter_res = next(iter([res for res in adapter_results if res.adapter_run.adapter_config.short_description() == adapter_version]))
                return adapter_res, default_static_res, optimal_static_res
    raise Exception(f'{workload} not found')


if __name__ == '__main__':
    results = load_results('data/results/all_results.json')
    workload_names = []
    fixed_runtime_means = []
    fixed_runtime_stddevs = []
    fixed_size_means = []
    def_fixed_runtime_means = []
    def_fixed_runtime_stddevs = []
    def_fixed_size_means = []
    adapter_runtime_means = []
    adapter_runtime_stddevs = []
    adapter_size_means = []
    for workload in workload_map.keys():
        workload_names.append(workload)
        adapter_res, def_fixed_res, fixed_res = find_results(workload, results)
        fixed_size_means.append(fixed_res.static_run.static_size)
        def_fixed_size_means.append(def_fixed_res.static_run.static_size)
        adapter_size_means.append(adapter_res.avg_pool_size)
        fixed_runtime_means.append(fixed_res.runtime_seconds)
        def_fixed_runtime_means.append(def_fixed_res.runtime_seconds)
        adapter_runtime_means.append(adapter_res.runtime_seconds)
        fixed_runtime_stddevs.append(fixed_res.std_deviation)
        def_fixed_runtime_stddevs.append(def_fixed_res.std_deviation)
        adapter_runtime_stddevs.append(adapter_res.std_deviation)

    
    x = np.arange(len(workload_names))  # the label locations
    width = 0.25  # the width of the bars
    
    fig, (ax, ax2) = plt.subplots(figsize=(25, 20), nrows=2)
    rects1 = ax.bar(x - width, fixed_runtime_means, width, label='optimal fixed', yerr=fixed_runtime_stddevs)
    rects2 = ax.bar(x, def_fixed_runtime_means, width, label='default fixed', yerr=def_fixed_runtime_stddevs)
    rects3 = ax.bar(x + width, adapter_runtime_means, width, label='adaptive', yerr=adapter_runtime_stddevs)
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Runtime in seconds')
    ax.set_xticks(x)
    ax.set_xticklabels(workload_names)
    ax.legend()
    ax.set_aspect('auto')
    
    max_stddev = max(max(fixed_runtime_stddevs), max(def_fixed_runtime_stddevs), max(adapter_runtime_stddevs))
    min_mean = min(min(fixed_runtime_means), min(def_fixed_runtime_means), min(adapter_runtime_means))
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = round(rect.get_height(), 2)
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, min_mean - max_stddev - 10),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    rects1b = ax2.bar(x - width, fixed_size_means, width, label='optimal fixed')
    rects2b = ax2.bar(x, def_fixed_size_means, width, label='default fixed')
    rects3b = ax2.bar(x + width, adapter_size_means, width, label='adaptive')
    ax2.set_ylabel('Average pool size')
    ax2.set_xticks(x)
    ax2.set_xticklabels(workload_names)
    ax2.legend()
    ax2.set_aspect('auto')

    max_size = max(max(adapter_size_means), max(fixed_size_means), max(def_fixed_runtime_stddevs))
    def autolabel2(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = round(rect.get_height(), 2)
            if height == max_size: 
                y = height - 3
            else:
                y = height + 1
            ax2.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, y),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    autolabel2(rects1b)
    autolabel2(rects2b)
    autolabel2(rects3b)
    fig.tight_layout()
    fig.savefig('ch5b-node-single-phase.png')