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
    """Simulated GPU so the tool runs without hardware.

    Throughput falls slowly as the cap drops (diminishing returns), which is
    the shape real GPUs roughly follow. The numbers are made up.
    """

    def __init__(self, max_watts: int = 750, peak_throughput: float = 1000.0):
        self.max_watts = max_watts
        self.peak = peak_throughput
        self.cap = max_watts

    def set_power_cap(self, watts: int) -> None:
        self.cap = watts

    def run_benchmark(self) -> Tuple[float, float]:
        return self.peak * (self.cap / self.max_watts) ** 0.35, float(self.cap)


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
