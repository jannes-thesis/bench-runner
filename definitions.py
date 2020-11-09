from collections import OrderedDict
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkSuite:
    name: str
    runner_script: str
    parameter_names: tuple[str]
    disk_param_hdd: str
    disk_param_ssd: str
    workloads_definition_file: str


@dataclass(frozen=True)
class Workload:
    benchmark_suite: BenchmarkSuite
    name: str
    disk: str
    workload_parameters: tuple[int]

    using_adapter_parameters: tuple[str]
    no_adapter_parameters: tuple[str]
    static_sizes: tuple[int]

    # def __hash__(self):
    #     workload_parameter_list = tuple(self.workload_parameters.values())
    #     to_hash = [str(hash(self.benchmark_suite)), self.name, self.disk, str(hash(workload_parameter_list))]
    #     return hash(to_hash)
    #
    # def __eq__(self, other):
    #     return type(self) == type(other) and self.__hash__() == other.__hash__()


@dataclass(frozen=True)
class AdapterConfig:
    # each branch starting with "v-" represents a version
    adapter_version: str
    # the values for the adapter parameters of corresponding version, in same order
    adapter_parameters: tuple[str]


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
