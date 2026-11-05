"""Sweep power caps and find the most efficient one."""
from dataclasses import dataclass
from typing import List


@dataclass
class Point:
    cap_watts: int
    throughput: float
    watts: float

    @property
    def per_watt(self) -> float:
        return self.throughput / self.watts


def sweep(backend, low_pct: int = 50, step_pct: int = 10) -> List[Point]:
    """Run the benchmark from low_pct% to 100% of max power, then restore max."""
    points = []
    try:
        for pct in range(low_pct, 101, step_pct):
            cap = round(backend.max_watts * pct / 100)
            backend.set_power_cap(cap)
            throughput, watts = backend.run_benchmark()
            points.append(Point(cap, throughput, watts))
    finally:
        backend.set_power_cap(backend.max_watts)
    return points


def best(points: List[Point]) -> Point:
    return max(points, key=lambda p: p.per_watt)
