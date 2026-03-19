from __future__ import annotations

import math

from yb171_raman_gate import RamanGateModel, build_tradeoff_table, fit_surrogate


def test_tradeoff_table_has_expected_tau_rows() -> None:
    model = RamanGateModel.from_prior_scale("nominal", seed=7)
    rows = build_tradeoff_table(
        model=model,
        detuning_grid_hz=[2.0e9, 4.0e9, 6.0e9, 8.0e9, 1.0e10, 1.2e10],
        pulse_families=["square", "blackman"],
        tau_targets=[1e-2, 1e-3, 1e-4, 1e-5],
        jitter_seed=11,
    )

    assert len(rows) == 4
    assert rows[0].tau == 1e-2
    assert rows[-1].tau == 1e-5


def test_surrogate_fit_returns_positive_r2_and_finite_delta_star() -> None:
    detuning = [2.0e9, 4.0e9, 6.0e9, 8.0e9, 1.0e10]
    epsilon = [0.012, 0.0041, 0.0029, 0.0030, 0.0038]
    fit = fit_surrogate(detuning_hz=detuning, epsilon_tot=epsilon)

    assert fit.r2 > 0.0
    assert math.isfinite(fit.delta_star_hz)
