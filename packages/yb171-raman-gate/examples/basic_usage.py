from __future__ import annotations

from yb171_raman_gate import RamanGateModel, build_tradeoff_table


model = RamanGateModel.from_prior_scale("nominal", seed=101)
rows = build_tradeoff_table(
    model=model,
    detuning_grid_hz=[2.0e9, 4.0e9, 6.0e9, 8.0e9, 1.0e10, 1.2e10],
    pulse_families=["square", "blackman", "drag_like", "composite_k3"],
    tau_targets=[1e-2, 1e-3, 1e-4, 1e-5],
    jitter_seed=13,
)

for row in rows:
    print(
        {
            "tau": row.tau,
            "feasible": row.feasible,
            "best_t_pi_us": row.best_t_pi_us,
            "best_detuning_hz": row.best_detuning_hz,
            "best_pulse_family": row.best_pulse_family,
            "dominant_error_channel": row.dominant_error_channel,
        }
    )
