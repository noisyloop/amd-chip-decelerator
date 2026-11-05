from decel.backend import FakeBackend
from decel.cli import main
from decel.sweep import best, sweep


def test_sweep_covers_range_and_restores_cap():
    b = FakeBackend(750)
    pts = sweep(b, low_pct=50, step_pct=10)
    assert [p.cap_watts for p in pts] == [375, 450, 525, 600, 675, 750]
    assert b.cap == 750


def test_lower_cap_is_more_efficient_on_fake_gpu():
    pts = sweep(FakeBackend(750))
    assert best(pts).cap_watts < 750


def test_cli_fake(capsys):
    assert main(["sweep", "--fake"]) == 0
    assert "Most efficient" in capsys.readouterr().out
