from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkSuite:
    name: str
    # relative path to the runner script (needs to have shebang and exe rights)
    runner_script: str
    parameter_names: tuple[str]
    disk_param_hdd: str
    disk_param_ssd: str
    # relative path to the workloads.yaml file
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

    def workload_parameters_str(self):
        return ','.join([str(p) for p in self.workload_parameters])

    def description(self) -> str:
        return f'{self.disk}-{self.name}-{self.workload_parameters_str()}'


@dataclass(frozen=True)
class AdapterConfig:
    # each branch starting with "v-" represents a version
    adapter_version: str
    # the values for the adapter parameters of corresponding version, in same order
    adapter_parameters: tuple[str]

    def description(self) -> str:
        return f'version: {self.adapter_version}, params: {",".join(self.adapter_parameters)}'


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
