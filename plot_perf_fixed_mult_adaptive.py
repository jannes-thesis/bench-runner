# FOR PLOTTING CH5 figures
from typing import Tuple
from definitions import AdapterResult, StaticResult
import matplotlib.pyplot as plt
import numpy as np
from reports import load_results

SMALL_SIZE = 14
MEDIUM_SIZE = 16
BIGGER_SIZE = 18

plt.rc('font', size=40)          # controls default text sizes
plt.rc('axes', titlesize=35)     # fontsize of the axes title
plt.rc('axes', labelsize=35)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=40)    # fontsize of the tick labels
plt.rc('ytick', labelsize=40)    # fontsize of the tick labels
plt.rc('legend', fontsize=35)    # legend fontsize
plt.rc('figure', titlesize=40)

adapter_version = {
    'ssd-fillseq-50000000': 
                    {'no-manager': {'v': 'v-4-1000,0.9', 'path': 'data/results/all_results-2021-01-29-18:37.json'},
                     'manager': {'v': 'v-4-1000,0.9', 'path': 'data/results/all_results-2021-01-29-15:50.json'}},
    'ssd-bulkload_nocompact-50000000':
                    {'no-manager': {'v': 'v-4-1000,0.9', 'path': 'data/results/all_results-2021-02-02-11:24.json'},
                     'manager': {'v': 'v-4-1000,0.9', 'path': 'data/results/all_results-2021-02-02-14:50.json'}}
}

# key: workload, value: tuple default/optimal static size
workload_map = {'ssd-fillseq-50000000': (2, 12),
                'ssd-bulkload_nocompact-50000000': (2, 20)}


def find_results(workload: str, results) -> Tuple[AdapterResult, AdapterResult, StaticResult, StaticResult]:
    """ return adapter no manager, adapter manager, default static, optimal static results """
    adapter_v = adapter_version[workload]
    no_manager_results = load_results(adapter_v['no-manager']['path'])
    manager_results = load_results(adapter_v['manager']['path'])
    no_manager_res = None
    manager_res = None
    default_static_res = None
    optimal_static_res = None
    for (static_results, ar) in no_manager_results:
        if len(static_results) > 0:
            if workload == static_results[0].static_run.workload.description():
                no_manager_res = next(iter([res for res in ar if res.adapter_run.adapter_config.short_description() == adapter_v['no-manager']['v']]))
    for (static_results, ar) in manager_results:
        if len(static_results) > 0:
            if workload == static_results[0].static_run.workload.description():
                manager_res = next(iter([res for res in ar if res.adapter_run.adapter_config.short_description() == adapter_v['manager']['v']]))
    for (static_results, adapter_results) in results:
        if len(static_results) > 0:
            if workload == static_results[0].static_run.workload.description():
                default_static_res = next(iter([res for res in static_results if res.static_run.static_size == workload_map[workload][0]]))
                optimal_static_res = next(iter([res for res in static_results if res.static_run.static_size == workload_map[workload][1]]))
    if no_manager_res is None or manager_res is None or default_static_res is None or optimal_static_res is None:
        print(no_manager_res)
        print(manager_res)
        print(default_static_res)
        print(optimal_static_res)
        raise Exception('some result not found')
    return no_manager_res, manager_res, default_static_res, optimal_static_res


if __name__ == '__main__':
    results = load_results('data/results/all_results.json')
    workload_names = []
    fixed_runtime_means = []
    fixed_runtime_stddevs = []
    fixed_size_means = []
    def_fixed_runtime_means = []
    def_fixed_runtime_stddevs = []
    def_fixed_size_means = []
    nomanager_runtime_means = []
    nomanager_runtime_stddevs = []
    nomanager_size_means = []
    manager_runtime_means = []
    manager_runtime_stddevs = []
    manager_size_means = []
    for workload in workload_map.keys():
        workload_names.append(workload.split('-')[1])
        nomanager_res, manager_res, def_fixed_res, fixed_res = find_results(workload, results)
        fixed_size_means.append(fixed_res.static_run.static_size)
        def_fixed_size_means.append(def_fixed_res.static_run.static_size)
        nomanager_size_means.append(nomanager_res.avg_pool_size)
        manager_size_means.append(manager_res.avg_pool_size)
        fixed_runtime_means.append(fixed_res.runtime_seconds)
        def_fixed_runtime_means.append(def_fixed_res.runtime_seconds)
        nomanager_runtime_means.append(nomanager_res.runtime_seconds)
        manager_runtime_means.append(manager_res.runtime_seconds)
        fixed_runtime_stddevs.append(fixed_res.std_deviation)
        def_fixed_runtime_stddevs.append(def_fixed_res.std_deviation)
        nomanager_runtime_stddevs.append(nomanager_res.std_deviation)
        manager_runtime_stddevs.append(manager_res.std_deviation)

    
    x = np.arange(len(workload_names))  # the label locations
    width = 0.2  # the width of the bars
    
    fig, (ax, ax2) = plt.subplots(figsize=(25, 20), nrows=2)
    rects1 = ax.bar(x - width * 3 / 2, fixed_runtime_means, width, label='optimal fixed', yerr=fixed_runtime_stddevs)
    rects2 = ax.bar(x - width / 2, def_fixed_runtime_means, width, label='default fixed', yerr=def_fixed_runtime_stddevs)
    rects3 = ax.bar(x + width / 2, nomanager_runtime_means, width, label='adaptive-nomanager', yerr=nomanager_runtime_stddevs)
    rects4 = ax.bar(x + width * 3 / 2, manager_runtime_means, width, label='adaptive-manager', yerr=manager_runtime_stddevs)
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Runtime in seconds')
    ax.set_xticks(x)
    ax.set_xticklabels(workload_names)
    # ax.legend()
    ax.set_aspect('auto')
    
    max_stddev = max(max(fixed_runtime_stddevs), max(def_fixed_runtime_stddevs), max(nomanager_runtime_stddevs), max(manager_runtime_stddevs))
    min_mean = min(min(fixed_runtime_means), min(def_fixed_runtime_means), min(nomanager_runtime_means), min(manager_runtime_means))
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = round(rect.get_height(), 2)
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, min_mean - max_stddev - 10),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    rects1b = ax2.bar(x - width * 3 / 2, fixed_size_means, width, label='optimal fixed')
    rects2b = ax2.bar(x - width / 2, def_fixed_size_means, width, label='default fixed')
    rects3b = ax2.bar(x + width / 2, nomanager_size_means, width, label='adaptive-nomanager')
    rects4b = ax2.bar(x + width * 3 / 2, manager_size_means, width, label='adaptive-manager')
    ax2.set_ylabel('Average pool size')
    ax2.set_xticks(x)
    ax2.set_xticklabels(workload_names)
    ax2.legend()
    ax2.set_aspect('auto')

    max_size = max(max(nomanager_size_means), max(fixed_size_means), max(def_fixed_runtime_stddevs), max(manager_size_means))
    def autolabel2(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = round(rect.get_height(), 2)
            if height > 0.8 * round(max_size, 2): 
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
    autolabel(rects4)
    autolabel2(rects1b)
    autolabel2(rects2b)
    autolabel2(rects3b)
    autolabel2(rects4b)
    fig.tight_layout()
    fig.savefig('ch5-rocks-single-perf.png')