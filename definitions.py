from collections import OrderedDict
from dataclasses import dataclass


@dataclass(frozen=True)
class Workload:
    benchmark_suite: str
    name: str
    disk: str
    params: OrderedDict[str, str]


@dataclass(frozen=True)
class AdapterRun:
    adapter_version: str
    workload: Workload


@dataclass(frozen=True)
class StaticRuns:
    static_sizes: str
    workload: Workload


@dataclass(frozen=True)
class AdapterResult:
    adapter_run: AdapterRun
    runtime_seconds: float
    std_deviation: float


@dataclass(frozen=True)
class StaticResults:
    static_runs: StaticRuns
    runtime_seconds: dict[int, float]
    std_deviation: dict[int, float]
