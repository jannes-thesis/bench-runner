from subprocess import run, DEVNULL

import yaml
import shutil

from definitions import AdapterConfig


def update_submodules():
    # update adapter repo
    print('updating submodules')
    run(['git', '-C', 'submodules/scaling-adapter', 'pull'], stdout=DEVNULL, stderr=DEVNULL)
    adapter_remote_branches_output = run(['git', '-C', 'submodules/scaling-adapter', 'branch', '-r'],
                                         capture_output=True, text=True).stdout
    adapter_remote_branches = {line.strip().split(' ')[0].split('/')[1] for line in
                               adapter_remote_branches_output.splitlines()}
    adapter_versions = {branch for branch in adapter_remote_branches if branch.startswith('v-')}
    adapter_versions_tracked = get_all_adapter_versions()
    adapter_versions_untracked = adapter_versions.difference(adapter_versions_tracked)
    # create local branches for all new remote version branches
    print(f'found {len(adapter_versions_untracked)} untracked adapter versions')
    for branch in adapter_versions_untracked:
        run(['git', '-C', 'submodules/scaling-adapter', 'checkout', '--track', f'origin/{branch}'])
    run(['git', '-C', 'submodules/scaling-adapter', 'checkout', 'master'], stdout=DEVNULL, stderr=DEVNULL)
    run(['git', '-C', 'submodules/dynamic-io-pool', 'pull'], stdout=DEVNULL, stderr=DEVNULL)


def get_all_adapter_configs() -> set[AdapterConfig]:
    result = set()
    for version in get_all_adapter_versions():
        configs = get_version_configs(version)
        result = result.union(configs)
    return result


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
    with open('submodules/scaling-adapter/adapter_info.yaml') as f:
        adapter_yaml = yaml.load(f.read(), Loader=yaml.FullLoader)
    param_value_combos = adapter_yaml['algorithm_parameter_combos']
    result = set()
    for combo in param_value_combos:
        config = AdapterConfig(version_branch, tuple(combo))
        result.add(config)
    return result


def compile_adapter(version: str):
    switch_to_version_branch(version)
    run(['cargo', 'build', '--manifest-path=scaling-adapter/Cargo.toml', '--release'])
    shutil.copyfile('submodules/scaling-adapter/scaling-adapter-clib/bindings.h',
                    'submodules/dynamic-io-pool/adapter.h')
    shutil.copyfile('submodules/scaling-adapter/target/release/libscaling_adapter_clib.a',
                    'submodules/dynamic-io-pool/adapter.a')


def compile_benchmarks():
    command = ('cd submodules/dynamic-io-pool && '
               'cmake --build /home/jannes/MasterThesis/dynamic_io_tpool/build --config Debug --target all; '
               'cd -')
    run(command, shell=True)
