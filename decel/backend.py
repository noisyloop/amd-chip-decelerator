"""GPU backends. A backend can set a power cap and run a benchmark."""
import subprocess
from typing import Protocol, Tuple


class Backend(Protocol):
    max_watts: int

    def set_power_cap(self, watts: int) -> None: ...

    def run_benchmark(self) -> Tuple[float, float]:
        """Return (throughput, average_watts) at the current cap."""
        ...


class FakeBackend:
    """Simulated GPU serving an LLM, so the tool runs without hardware.

    Throughput is in tokens/sec. Bigger batches keep the GPU busier (more
    tokens/sec, more watts). A lower power cap trims speed with diminishing
    returns. All numbers are made up; calibrate against a real MI300X.
    """

    IDLE_FRACTION = 0.2  # idle draw as a share of max power
    BATCH_KNEE = 16      # batch size where utilization reaches 50%

    def __init__(self, max_watts: int = 750, peak_tokens_per_sec: float = 10000.0,
                 batch_size: int = 32):
        self.max_watts = max_watts
        self.peak = peak_tokens_per_sec
        self.batch = batch_size
        self.cap = max_watts

    def set_power_cap(self, watts: int) -> None:
        self.cap = watts

    def run_benchmark(self) -> Tuple[float, float]:
        util = self.batch / (self.batch + self.BATCH_KNEE)
        idle = self.max_watts * self.IDLE_FRACTION
        demand = idle + (self.max_watts - idle) * util
        watts = min(self.cap, demand)
        tokens_per_sec = self.peak * util * (watts / self.max_watts) ** 0.35
        return tokens_per_sec, watts


class AmdSmiBackend:
    """Real GPU via the `amd-smi` CLI.

    UNTESTED on hardware: check the amd-smi flags against your ROCm version.
    The benchmark command must print throughput as a number on its last line.
    """

    def __init__(self, gpu: int, max_watts: int, bench_cmd: str):
        self.gpu = gpu
        self.max_watts = max_watts
        self.bench_cmd = bench_cmd

    def set_power_cap(self, watts: int) -> None:
        subprocess.run(
            ["amd-smi", "set", "-g", str(self.gpu), "--power-cap", str(watts)],
            check=True,
        )

    def run_benchmark(self) -> Tuple[float, float]:
        out = subprocess.run(
            self.bench_cmd, shell=True, check=True, capture_output=True, text=True
        ).stdout.strip().splitlines()
        throughput = float(out[-1])
        # TODO: sample real power draw during the run; using the cap as a stand-in.
        return throughput, float(self._current_cap())

    def _current_cap(self) -> int:
        out = subprocess.run(
            ["amd-smi", "static", "-g", str(self.gpu), "--limit", "--json"],
            check=True, capture_output=True, text=True,
        ).stdout
        import json, re
        m = re.search(r'"socket_power_limit"[^0-9]*([0-9.]+)', out)
        return int(float(m.group(1))) if m else self.max_watts
