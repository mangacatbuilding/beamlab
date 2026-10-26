import math

import matplotlib.pyplot as plt
import numpy as np

if __package__:
    from .cantilever import (
        calculate_bending_moment,
        calculate_deflection,
        calculate_max_stress,
        calculate_shear_force,
    )
else:
    from cantilever import (
        calculate_bending_moment,
        calculate_deflection,
        calculate_max_stress,
        calculate_shear_force,
    )


def _read_number(prompt, *, positive=False, maximum=None):
    """Read a finite, nonnegative number, retrying invalid entries."""
    while True:
        try:
            value = float(input(prompt))
        except ValueError:
            print("Please enter a valid number.")
            continue

        if not math.isfinite(value):
            print("Please enter a finite number.")
        elif value < 0 or (positive and value == 0):
            if positive:
                print("Value must be greater than zero.")
            else:
                print("Value must be zero or greater.")
        elif maximum is not None and value > maximum:
            print(f"Value must not exceed {maximum:g}.")
        else:
            return value


def beam_calculator():
    E = 200e9
    while True:
        f = _read_number("Input the force applied (N): ")
        l = _read_number("Input the length of the beam (m): ", positive=True)
        w = _read_number("Input the width of the beam (mm): ", positive=True)
        h = _read_number("Input the height of the beam (mm): ", positive=True)

        w *= 1e-3
        h *= 1e-3
        try:
            I = w * h**3 / 12
            if I <= 0 or not math.isfinite(6 * E * I):
                raise ArithmeticError
            max_stress = calculate_max_stress(f, l, I, h)
            tip_deflection = calculate_deflection(f, l, E, I, l)
            if not all(math.isfinite(value) for value in
                       (max_stress, tip_deflection, f * l)):
                raise ArithmeticError
        except ArithmeticError:
            print("Values are too large or too small for this calculation. "
                  "Please enter the beam values again.")
            continue
        break

    x_cut, v_at_x = calculate_deflection_at_x(f, l, E, I)
    plot_all_diagrams(f, l, E, I, max_stress, x_cut, v_at_x)


def calculate_deflection_at_x(f, l, E, I):
    x = _read_number("Input cut distance from the fixed end (m): ", maximum=l)
    v = calculate_deflection(f, l, E, I, x)
    return x, v


def plot_all_diagrams(f, l, E, I, max_stress, x_cut, v_at_x):
    x = np.linspace(0, l, 100)
    v = calculate_deflection(f, l, E, I, x)
    moment = calculate_bending_moment(f, l, x)
    shear = calculate_shear_force(f, x)
    max_deflection = abs(calculate_deflection(f, l, E, I, l))

    fig, ax = plt.subplots(
        4, 1,
        figsize=(10, 8),
        layout="constrained",
        gridspec_kw={"height_ratios": [1, 1, 1, 0.5]},
    )

    ax[0].plot(x, v)
    ax[0].set_title("Cantilever Beam Deflection")
    ax[0].set_ylabel("Deflection (mm)")
    ax[1].plot(x, moment)
    ax[1].set_title("Bending Moment Diagram")
    ax[1].set_ylabel("Moment (Nm)")
    ax[2].plot(x, shear)
    ax[2].set_title("Shear Force Diagram")
    ax[2].set_xlabel("Position along beam (m)")
    ax[2].set_ylabel("Shear Force (N)")

    for chart in ax[:3]:
        chart.grid(True)

    ax[3].axis("off")
    summary = (
        f"Maximum bending stress: {max_stress:.3f} MPa\n"
        f"Deflection at x = {x_cut:.2f} m: {v_at_x:.3f} mm\n"
        f"Maximum deflection = {max_deflection:.3f} mm"
    )
    ax[3].text(
        0, 1,
        summary,
        fontsize=11,
        linespacing=1.5,
        va="top",
        transform=ax[3].transAxes,
    )

    fig.savefig("beam_analysis_report.png", dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    beam_calculator()
