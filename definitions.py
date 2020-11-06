from collections import OrderedDict
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkSuite:
    name: str
    runner_script: str
    parameter_names: list[str]
    disk_params: dict[str, str]
    workloads_definition_file: str


@dataclass(frozen=True)
class Workload:
    benchmark_suite: BenchmarkSuite
    name: str
    disk: str
    use_adapter_param_names: list[str]
    no_adapter_param_names: list[str]
    params: OrderedDict[str, int]
    static_sizes: list[int]


@dataclass(frozen=True)
class AdapterConfig:
    # each branch starting with "v-" represents a version
    adapter_version: str
    # the values for the adapter parameters of corresponding version, in same order
    adapter_parameters: OrderedDict[str, str]


@dataclass(frozen=True)
class AdapterRunDefinition:
    adapter_config: AdapterConfig
    workload: Workload


@dataclass(frozen=True)
class StaticRunDefinition:
    static_size: int
    workload: Workload


@dataclass(frozen=True)
class AdapterResult:
    adapter_run: AdapterRunDefinition
    runtime_seconds: float
    std_deviation: float


@dataclass(frozen=True)
class StaticResult:
    static_run: StaticRunDefinition
    runtime_seconds: float
    std_deviation: float
