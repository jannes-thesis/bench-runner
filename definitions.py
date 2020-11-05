from collections import OrderedDict
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Workload:
    benchmark_suite: str
    name: str
    disk: str
    params: OrderedDict[str, int]


@dataclass(frozen=True)
class AdapterRunDefinition:
    adapter_version: str
    adapter_parameters: dict[str, Union[int, str]]
    workload: Workload


@dataclass(frozen=True)
class StaticRunsDefinition:
    static_sizes: str
    workload: Workload


@dataclass(frozen=True)
class AdapterResult:
    adapter_run: AdapterRunDefinition
    runtime_seconds: float
    std_deviation: float


@dataclass(frozen=True)
class StaticResults:
    static_runs: StaticRunsDefinition
    runtime_seconds: dict[int, float]
    std_deviation: dict[int, float]
