import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

from beam import beam_calculator as calculator
from beam.cantilever import (
    calculate_bending_moment,
    calculate_deflection,
    calculate_max_stress,
    calculate_shear_force,
)


@pytest.mark.parametrize(
    "position, expected",
    [(0, 0), (0.5, -1.157407), (1, -3.703704)],
)
def test_deflection(position, expected):
    result = calculate_deflection(100, 1, 200e9, 4.5e-8, position)

    assert result == pytest.approx(expected)


def test_max_stress():
    # A 50 mm by 100 mm section, under 1000 N at a 2 m free end.
    assert calculate_max_stress(1000, 2, 4.166666666666667e-6, 0.1) == pytest.approx(24)


def test_bending_moment_at_support_midpoint_and_tip():
    result = calculate_bending_moment(1000, 2, np.array([0, 1, 2]))

    np.testing.assert_allclose(result, [-2000, -1000, 0])


def test_shear_preserves_position_shape_and_fractional_force():
    positions = np.array([0, 1, 2])

    result = calculate_shear_force(2.5, positions)

    assert result.shape == positions.shape
    np.testing.assert_allclose(result, [-2.5, -2.5, -2.5])
    np.testing.assert_array_equal(positions, [0, 1, 2])


@pytest.mark.parametrize(
    "field_index, invalid_value",
    [
        (0, ""),
        (0, "not a number"),
        (0, "-1"),
        (0, "nan"),
        (0, "inf"),
        (1, "0"),
        (2, "-5"),
        (2, "inf"),
        (3, "0"),
        (3, "nan"),
        (4, "-0.1"),
        (4, "2.1"),
        (4, "nan"),
        (4, "inf"),
    ],
)
def test_cli_retries_only_the_invalid_field(monkeypatch, field_index, invalid_value):
    responses = ["1000", "2", "50", "100", "1"]
    responses.insert(field_index, invalid_value)
    responses = iter(responses)
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    plot = Mock()
    monkeypatch.setattr(calculator, "plot_all_diagrams", plot)

    calculator.beam_calculator()

    plot.assert_called_once()
    assert plot.call_args.args == pytest.approx(
        (1000, 2, 200e9, 4.166666666666667e-6, 24, 1, -1)
    )


@pytest.mark.parametrize(
    "unrepresentable_beam",
    [
        ["1000", "2", "50", "1e-200"],
        ["1000", "2", "50", "1e200"],
        ["1000", "1e200", "50", "100"],
    ],
)
def test_cli_retries_beam_when_calculations_exceed_float_range(
    monkeypatch, unrepresentable_beam
):
    responses = iter(unrepresentable_beam + ["1000", "2", "50", "100", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    plot = Mock()
    monkeypatch.setattr(calculator, "plot_all_diagrams", plot)

    calculator.beam_calculator()

    plot.assert_called_once()
    assert plot.call_args.args == pytest.approx(
        (1000, 2, 200e9, 4.166666666666667e-6, 24, 1, -1)
    )


@pytest.mark.parametrize("cut_position", [0, 2])
def test_cli_allows_zero_force_and_cut_endpoints(monkeypatch, cut_position):
    responses = iter(["0", "2", "50", "100", str(cut_position)])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    plot = Mock()
    monkeypatch.setattr(calculator, "plot_all_diagrams", plot)

    calculator.beam_calculator()

    plot.assert_called_once()
    assert plot.call_args.args == pytest.approx(
        (0, 2, 200e9, 4.166666666666667e-6, 0, cut_position, 0)
    )


def test_cli_plots_three_diagrams_and_saves_png(monkeypatch, tmp_path):
    responses = iter(["1000", "2", "50", "100", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.chdir(tmp_path)
    show = Mock()
    monkeypatch.setattr(calculator.plt, "show", show)

    try:
        calculator.beam_calculator()

        show.assert_called_once()
        report = tmp_path / "beam_analysis_report.png"
        assert report.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert report.stat().st_size > 1000
        charts = calculator.plt.gcf().axes[:3]
        assert len(charts) == 3
        for chart in charts:
            assert len(chart.lines) == 1
            np.testing.assert_allclose(chart.lines[0].get_xdata()[[0, -1]], [0, 2])
        for chart, expected in zip(charts, ([0, -3.2], [-2000, 0], [-1000, -1000])):
            np.testing.assert_allclose(chart.lines[0].get_ydata()[[0, -1]], expected)
    finally:
        calculator.plt.close("all")


@pytest.mark.parametrize("launch_mode", ["script", "module"])
def test_cli_launch_modes(launch_mode, tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.update(
        MPLBACKEND="Agg",
        MPLCONFIGDIR=str(tmp_path / "matplotlib-config"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    if launch_mode == "script":
        command = [sys.executable, str(project_root / "beam" / "beam_calculator.py")]
    else:
        environment["PYTHONPATH"] = str(project_root)
        command = [sys.executable, "-m", "beam.beam_calculator"]

    result = subprocess.run(
        command,
        input="1000\n2\n50\n100\n1\n",
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "beam_analysis_report.png").read_bytes().startswith(
        b"\x89PNG\r\n\x1a\n"
    )
