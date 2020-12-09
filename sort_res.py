import json
with open('data/results/all_results.json') as f:
    import json
    all_res = json.load(f)
    
all_res.keys()
for k in all_res.keys():
    for disk in all_res[k].keys():
        for w in all_res[k][disk].keys():
            for p in all_res[k][disk][w].keys():
                all_res[k][disk][w][p]['without_adapter'] = sorted(all_res[k][disk][w][p]['without_adapter'], key=lambda e: e['pool_size'])
                
with open('data/results/all_results.json', 'w') as f:
    json.dump(all_res, f, indent=4)
    
