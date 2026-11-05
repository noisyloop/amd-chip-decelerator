# amd-chip-decelerator

More compute from the same power: find the power cap where an AMD Instinct GPU
does the most work per watt. Power-limited data centers can then fit more GPUs.

## Use

```
pip install -e .
decel sweep --fake                                  # simulated GPU, no hardware
decel sweep --gpu 0 --max-watts 750 --bench "./my_benchmark.sh"
```

The benchmark command must print throughput (a number) on its last line.
`sweep` steps the cap from 50% to 100% of max power, prints throughput and
throughput-per-watt at each step, and restores the max cap when done.

## Status

Early. The `--fake` backend is simulated (made-up numbers). The `amd-smi`
backend has not been tested on real hardware; check its flags against your
ROCm version. Power draw is currently approximated by the cap.

## Ideas / next

- `decel apply`: set the chosen cap at boot
- `decel watch`: idle-GPU detection with Prometheus metrics
- `decel partition`: pick an MI300X partition mode for the job mix

## Test

```
pip install pytest && pytest
```
