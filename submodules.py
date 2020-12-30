from subprocess import run, DEVNULL

import logging
import yaml
import shutil

from definitions import AdapterConfig

logger = logging.getLogger(__name__)


def run_silent(command_list: list[str]):
    if run(command_list, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        raise Exception(f'command failed: {command_list}')


def run_silent_extra_shell(command: str):
    if run(command, shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
        raise Exception(f'command failed: {command}')


def run_chatty(command_list: list[str]):
    if run(command_list).returncode != 0:
        raise Exception(f'command failed: {command_list}')


def update_submodules():
    # update adapter repo
    logger.info('updating submodules')
    switch_to_adapter_master()
    run_silent(['git', '-C', 'submodules/scaling-adapter', 'fetch', '--all'])
    run_silent(['git', '-C', 'submodules/scaling-adapter', 'pull', 'origin', 'master'])
    adapter_remote_branches_output = run(
        ['git', '-C', 'submodules/scaling-adapter', 'branch', '-r'],
        capture_output=True,
        text=True).stdout
    adapter_remote_branches = {
        line.strip().split(' ')[0].split('/')[1]
        for line in adapter_remote_branches_output.splitlines()
    }
    adapter_versions = {
        branch
        for branch in adapter_remote_branches if branch.startswith('v-')
    }
    adapter_versions_tracked = get_all_adapter_versions()
    adapter_versions_untracked = adapter_versions.difference(
        adapter_versions_tracked)
    # create local branches for all new remote version branches
    logger.info(
        f'found {len(adapter_versions_untracked)} untracked adapter versions')
    for branch in adapter_versions_untracked:
        run_silent([
            'git', '-C', 'submodules/scaling-adapter', 'checkout', '--track',
            f'origin/{branch}'
        ])
    # update already tracked version branches
    for branch in adapter_versions_tracked:
        switch_to_adapter_version_branch(branch)
        run_silent(['git', '-C', 'submodules/scaling-adapter', 'reset', '--hard', f'origin/{branch}'])
    switch_to_adapter_master()
    run_silent(['git', '-C', 'submodules/dynamic-io-pool', 'pull', 'origin', 'master'])
    # run_silent(['git', '-C', 'submodules/node-io-benchmark', 'fetch', 'origin', 'master:master'])
    # run_silent(['git', '-C', 'submodules/node-io-benchmark', 'fetch', 'origin', 'adaptive:adaptive'])
    # run_silent(['git', '-C', 'submodules/rocks-io-benchmark', 'fetch', 'origin', 'master:master'])
    # run_silent(['git', '-C', 'submodules/rocks-io-benchmark', 'fetch', 'origin', 'adaptive:adaptive'])


def get_all_adapter_configs() -> set[AdapterConfig]:
    result = set()
    for version in get_all_adapter_versions():
        configs = get_version_configs(version)
        result = result.union(configs)
    return result


def get_all_adapter_versions() -> set[str]:
    git_branch_output = run(
        ['git', '-C', 'submodules/scaling-adapter', 'branch'],
        capture_output=True,
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
    run_silent(['git', '-C', 'submodules/scaling-adapter', 'checkout', 'master'])


def switch_to_adapter_version_branch(version_branch: str):
    run_silent([
        'git', '-C', 'submodules/scaling-adapter', 'checkout', version_branch
    ])


def get_current_adapter_branch() -> str:
    git_branch_output = run(
        ['git', '-C', 'submodules/scaling-adapter', 'branch'],
        capture_output=True,
        text=True)
    current_branch = None
    for line in git_branch_output.stdout.splitlines():
        if line.startswith('*'):
            line = line[1:]
            current_branch = line.strip()
    return current_branch


def get_version_configs(version_branch: str) -> set[AdapterConfig]:
    switch_to_adapter_version_branch(version_branch)
    with open('submodules/scaling-adapter/adapter_info.yaml') as f:
        adapter_yaml = yaml.load(f.read(), Loader=yaml.FullLoader)
    param_value_combos = adapter_yaml['algorithm_parameter_combos']
    switch_to_adapter_master()
    result = set()
    for combo in param_value_combos:
        config = AdapterConfig(version_branch,
                               tuple([str(val) for val in combo]))
        result.add(config)
    return result


def compile_adapter(version: str):
    switch_to_adapter_version_branch(version)
    run_silent([
        'cargo', 'build',
        '--manifest-path=submodules/scaling-adapter/Cargo.toml', '--release'
    ])
    if version == 'master':
        return
    shutil.copyfile(
        'submodules/scaling-adapter/scaling-adapter-clib/bindings.h',
        'submodules/dynamic-io-pool/adapter.h')
    shutil.copyfile(
        'submodules/scaling-adapter/target/release/libscaling_adapter_clib.a',
        'submodules/dynamic-io-pool/adapter.a')
    shutil.copyfile(
        'submodules/scaling-adapter/target/release/libscaling_adapter_clib.a',
        'submodules/rocks-io-benchmark/rocksdb-6.7.3/adapter.a')
    shutil.copyfile(
        'submodules/scaling-adapter/target/release/libscaling_adapter_clib.a',
        'submodules/node-io-benchmark/node-14.15.1/deps/uv/libadapter.a')


def compile_benchmarks(adaptive: bool):
    if adaptive:
        run_silent(['git', '-C', 'submodules/node-io-benchmark', 'checkout', 'adaptive'])
        run_silent(['git', '-C', 'submodules/rocks-io-benchmark', 'checkout', 'adaptive'])
    else:
        run_silent(['git', '-C', 'submodules/node-io-benchmark', 'checkout', 'master'])
        run_silent(['git', '-C', 'submodules/rocks-io-benchmark', 'checkout', 'master'])
    command = (
        'cd submodules/dynamic-io-pool && '
        'cmake --build build --config Debug --target all; '
        'cd ../..')
    run_silent_extra_shell(command)
    command = (
        'cd submodules/node-io-benchmark && '
        'bash make_node.sh; '
        'cd ../..')
    run_silent_extra_shell(command)
    command = (
        'cd submodules/rocks-io-benchmark && '
        'bash make_rocks.sh; '
        'cd ../..')
    run_silent_extra_shell(command)
    run_silent(['git', '-C', 'submodules/node-io-benchmark', 'checkout', 'master'])
    run_silent(['git', '-C', 'submodules/rocks-io-benchmark', 'checkout', 'master'])
