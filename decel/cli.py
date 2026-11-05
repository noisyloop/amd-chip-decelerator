import argparse

from .backend import AmdSmiBackend, FakeBackend
from .sweep import best, sweep


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="decel")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sweep", help="find the most efficient power cap")
    s.add_argument("--fake", action="store_true", help="simulated GPU, no hardware")
    s.add_argument("--gpu", type=int, default=0)
    s.add_argument("--max-watts", type=int, default=750)
    s.add_argument("--bench", help="command that prints throughput on its last line")
    s.add_argument("--batch", type=int, default=32, help="batch size for --fake")
    s.add_argument("--low", type=int, default=50, help="lowest cap, %% of max")
    s.add_argument("--step", type=int, default=10, help="step size, %%")
    args = p.parse_args(argv)

    if args.fake:
        backend = FakeBackend(args.max_watts, batch_size=args.batch)
    elif args.bench:
        backend = AmdSmiBackend(args.gpu, args.max_watts, args.bench)
    else:
        p.error("give --bench CMD, or --fake")

    points = sweep(backend, args.low, args.step)
    top = max(pt.throughput for pt in points)
    print(f"{'cap(W)':>7} {'throughput':>11} {'vs peak':>8} {'per watt':>9} {'J/token':>8}")
    for pt in points:
        print(f"{pt.cap_watts:>7} {pt.throughput:>11.1f} {pt.throughput/top:>7.0%} {pt.per_watt:>9.3f} {pt.watts/pt.throughput:>8.4f}")
    b = best(points)
    print(f"\nMost efficient: {b.cap_watts} W "
          f"({b.throughput/top:.0%} of peak speed, {b.cap_watts/backend.max_watts:.0%} of max power)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
