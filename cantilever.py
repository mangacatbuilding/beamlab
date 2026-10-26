import numpy as np


def calculate_deflection(f, l, E, I, x):
    """Return deflection in mm; inputs use N, m, Pa, and m**4."""
    v = -(f * x**2 * (3 * l - x)) / (6 * E * I)
    v *= 1000
    return v


def calculate_max_stress(f, l, I, h):
    """Return maximum bending stress in MPa for SI inputs."""
    max_stress = (f * l * h) / (2 * I) / 1e6
    return max_stress


def calculate_bending_moment(f, l, x):
    moment = -f * (l - x)
    return moment


def calculate_shear_force(f, x):
    return np.full_like(x, -f, dtype=float)

