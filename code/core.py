from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


PULSE_FACTORS = {
    "square": 1.00,
    "blackman": 0.93,
    "drag_like": 0.90,
    "composite_k3": 0.82,
}


@dataclass(frozen=True)
class ModelParams:
    a_sc: float
    a_leak: float
    a_stark: float
    a_ctrl: float
    omega_scale: float


def sample_model_params(prior_scale: str, rng: np.random.Generator) -> ModelParams:
    scale = {"optimistic": 0.8, "nominal": 1.0, "conservative": 1.25}[prior_scale]
    return ModelParams(
        a_sc=4.8e16 * scale * rng.uniform(0.92, 1.08),
        a_leak=2.0e7 * scale * rng.uniform(0.90, 1.10),
        a_stark=2.5e-4 * scale * rng.uniform(0.92, 1.08),
        a_ctrl=5.5e-5 * scale * rng.uniform(0.92, 1.08),
        omega_scale=6.0e7 / scale * rng.uniform(0.95, 1.05),
    )


def evaluate_gate_point(
    detuning_hz: float,
    pulse_family: str,
    params: ModelParams,
    rng: np.random.Generator,
) -> dict[str, float | bool]:
    assert detuning_hz > 0.0, "detuning_hz must be positive"
    pulse_factor = PULSE_FACTORS[pulse_family]

    omega_eff = params.omega_scale * pulse_factor / (detuning_hz / 1.0e9)
    t_pi_us = float(np.pi / omega_eff * 1.0e6)

    epsilon_sc = params.a_sc / (detuning_hz ** 2)
    epsilon_leak = params.a_leak / detuning_hz
    epsilon_stark = params.a_stark * (detuning_hz / 1.0e10) ** 2 / pulse_factor
    epsilon_ctrl = params.a_ctrl * (t_pi_us / 10.0) ** 1.2 / pulse_factor

    # Bounded positive stochastic variation to emulate calibration/noise drift.
    jitter = abs(rng.normal(0.0, 1.6e-5))

    epsilon_tot = epsilon_sc + epsilon_leak + epsilon_stark + epsilon_ctrl + jitter
    return {
        "t_pi_us": t_pi_us,
        "epsilon_sc": float(epsilon_sc),
        "epsilon_leak": float(epsilon_leak),
        "epsilon_Stark": float(epsilon_stark),
        "epsilon_ctrl": float(epsilon_ctrl),
        "epsilon_tot": float(epsilon_tot),
        "A_positive": bool(params.a_sc > 0.0),
        "B_positive": bool(params.a_stark > 0.0),
        "x_positive": bool(detuning_hz**2 > 0.0),
    }


def fit_surrogate(detuning_hz: np.ndarray, epsilon_tot: np.ndarray) -> dict[str, float]:
    x = detuning_hz**2
    design = np.column_stack((1.0 / x, x, np.ones_like(x)))
    coeff, _, _, _ = np.linalg.lstsq(design, epsilon_tot, rcond=None)
    pred = design @ coeff
    ss_res = float(np.sum((epsilon_tot - pred) ** 2))
    ss_tot = float(np.sum((epsilon_tot - np.mean(epsilon_tot)) ** 2) + 1e-12)
    r2 = 1.0 - ss_res / ss_tot
    a, b, c = coeff
    return {
        "A": float(a),
        "B": float(b),
        "C": float(c),
        "surrogate_fit_r2": float(r2),
        "delta_star_hz": float((a / b) ** 0.25) if (a > 0.0 and b > 0.0) else float("nan"),
    }


def unimodality_pass(y: np.ndarray) -> bool:
    dy = np.diff(y)
    signs = np.sign(dy)
    # Ignore tiny numerical plateaus.
    signs = signs[signs != 0.0]
    if len(signs) < 2:
        return True
    sign_changes = np.sum(np.diff(signs) != 0.0)
    return bool(sign_changes <= 1)


def bootstrap_ci(
    samples: np.ndarray,
    rng: np.random.Generator,
    alpha: float = 0.10,
    n_boot: int = 600,
) -> tuple[float, float, float]:
    means = np.empty(n_boot)
    for i in range(n_boot):
        draw = rng.choice(samples, size=len(samples), replace=True)
        means[i] = np.mean(draw)
    lo = float(np.quantile(means, alpha / 2.0))
    mid = float(np.quantile(means, 0.5))
    hi = float(np.quantile(means, 1.0 - alpha / 2.0))
    return lo, mid, hi


def floor_impossibility(epsilon_floor: float, tau: float) -> bool:
    return bool(epsilon_floor > tau)


def check_monotone_feasibility(tau_values: list[float], feasible: list[bool]) -> bool:
    # As tau decreases, feasibility should not improve.
    paired = sorted(zip(tau_values, feasible), key=lambda x: x[0], reverse=True)
    seen_false = False
    for _, is_feasible in paired:
        if not is_feasible:
            seen_false = True
        if seen_false and is_feasible:
            return False
    return True


def chance_constraint_satisfied(epsilon_samples: np.ndarray, tau: float, alpha: float) -> bool:
    sat_rate = float(np.mean(epsilon_samples <= tau))
    return sat_rate >= 1.0 - alpha


def stable_round(value: float, ndigits: int = 6) -> float:
    return float(np.round(value, ndigits))


def to_jsonable(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (np.floating, np.integer)):
            out[key] = value.item()
        else:
            out[key] = value
    return out
