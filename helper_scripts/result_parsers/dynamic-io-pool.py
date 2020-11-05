import json
import os


def parse_result() -> tuple[float, float]:
    """ 
    :return: runtime in seconds, std deviation
    """
    with open('results/tmp_result.json') as f:
        hyperfine_output = json.load(f)
    avg_runtime = hyperfine_output['results']['mean']
    std_deviation = hyperfine_output['results']['stddev']
    os.remove('results/tmp_result.json')
    return avg_runtime, std_deviation
