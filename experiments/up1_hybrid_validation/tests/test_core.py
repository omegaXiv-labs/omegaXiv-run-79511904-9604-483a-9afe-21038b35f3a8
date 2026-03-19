from __future__ import annotations

import numpy as np

from up1_validation.core import check_monotone_feasibility, fit_surrogate, floor_impossibility


def test_surrogate_recovers_positive_optimum() -> None:
    detuning = np.array([2e9, 4e9, 6e9, 8e9, 1e10, 1.2e10], dtype=float)
    x = detuning**2
    eps = 6e16 / x + 2.2e-24 * x + 3e-5
    fit = fit_surrogate(detuning, eps)
    assert fit["A"] > 0
    assert fit["B"] > 0
    assert np.isfinite(fit["surrogate_fit_r2"])
    assert np.isfinite(fit["delta_star_hz"])
    assert fit["delta_star_hz"] > 0


def test_floor_impossibility_logic() -> None:
    assert floor_impossibility(3e-4, 1e-4)
    assert not floor_impossibility(1e-5, 1e-4)


def test_monotone_feasibility() -> None:
    taus = [1e-2, 1e-3, 1e-4, 1e-5]
    assert check_monotone_feasibility(taus, [True, True, False, False])
    assert not check_monotone_feasibility(taus, [True, False, True, False])
