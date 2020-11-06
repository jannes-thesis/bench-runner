from collections import OrderedDict
from subprocess import run, DEVNULL

from ruamel.yaml import YAML

from definitions import AdapterConfig


def update_submodules():
    # update adapter repo
    run(['git', '-C', 'submodules/scaling-adapter', 'pull'], stdout=DEVNULL, stderr=DEVNULL)
    adapter_remote_branches_output = run(['git', '-C', 'submodules/scaling-adapter', 'branch', '-r'],
                                         capture_output=True, text=True).stdout
    adapter_remote_branches = {line.strip().split(' ')[0].split('/')[1] for line in
                               adapter_remote_branches_output.splitlines()}
    adapter_versions = {branch for branch in adapter_remote_branches if branch.startswith('v-')}
    adapter_versions_tracked = get_all_adapter_versions()
    adapter_versions_untracked = adapter_versions.difference(adapter_versions_tracked)
    # create local branches for all new remote version branches
    for branch in adapter_versions_untracked:
        run(['git', '-C', 'submodules/scaling-adapter', 'checkout', '--track', f'origin/{branch}'])
    run(['git', '-C', 'submodules/scaling-adapter', 'checkout', 'master'])
    run(['git', '-C', 'submodules/dynamic-io-pool', 'pull'], stdout=DEVNULL, stderr=DEVNULL)


def get_all_adapter_versions() -> set[str]:
    git_branch_output = run(['git', '-C', 'submodules/scaling-adapter', 'branch'], capture_output=True,
                            text=True)
    branches = set()
    for line in git_branch_output.stdout.splitlines():
        if line.startswith('*'):
            line = line[1:]
        branch = line.strip()
        branches.add(branch)

    versions = {branch for branch in branches if branch.startswith('v-')}
    return versions


def switch_to_adapter_master():
    run(['git', '-C', 'submodules/scaling-adapter', 'checkout', 'master'])


def switch_to_version_branch(version_branch: str):
    run(['git', '-C', 'submodules/scaling-adapter', 'checkout', version_branch])


def get_version_configs(version_branch: str) -> set[AdapterConfig]:
    switch_to_version_branch(version_branch)
    yaml = YAML()
    adapter_yaml = yaml.load('submodules/scaling-adapter/adapter_info.yaml')
    param_names = [param.name for param in adapter_yaml['algorithm_parameters']]
    param_value_combos = adapter_yaml['algorithm_parameter_combos']
    result = set()
    for combo in param_value_combos:
        param_dict = OrderedDict(zip(param_names, combo))
        config = AdapterConfig(version_branch, param_dict)
        result.add(config)
    return result
