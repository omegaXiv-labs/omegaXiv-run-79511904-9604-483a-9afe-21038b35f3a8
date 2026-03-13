from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Mapping


PULSE_FACTORS: Mapping[str, float] = {
    "square": 1.00,
    "blackman": 0.93,
    "drag_like": 0.90,
    "composite_k3": 0.82,
}


@dataclass(frozen=True)
class ModelParams:
    """Calibrated coefficients used by the gate error model."""

    a_sc: float
    a_leak: float
    a_stark: float
    a_ctrl: float
    omega_scale: float


@dataclass(frozen=True)
class GatePoint:
    """Single operating point produced by the Raman gate model."""

    detuning_hz: float
    pulse_family: str
    t_pi_us: float
    epsilon_sc: float
    epsilon_leak: float
    epsilon_stark: float
    epsilon_ctrl: float
    epsilon_tot: float

    @property
    def dominant_error_channel(self) -> str:
        channels = {
            "epsilon_sc": self.epsilon_sc,
            "epsilon_leak": self.epsilon_leak,
            "epsilon_stark": self.epsilon_stark,
            "epsilon_ctrl": self.epsilon_ctrl,
        }
        return max(channels, key=lambda name: channels[name])


def sample_model_params(prior_scale: str, seed: int | None = None) -> ModelParams:
    """Sample physically plausible model parameters following the validated prior scales."""

    if prior_scale not in {"optimistic", "nominal", "conservative"}:
        raise ValueError("prior_scale must be one of optimistic/nominal/conservative")

    scale = {
        "optimistic": 0.8,
        "nominal": 1.0,
        "conservative": 1.25,
    }[prior_scale]
    rng = random.Random(seed)

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
    jitter_seed: int | None = None,
) -> GatePoint:
    """Evaluate one gate operating point using the extracted UP1 error decomposition."""

    if detuning_hz <= 0.0:
        raise ValueError("detuning_hz must be positive")
    if pulse_family not in PULSE_FACTORS:
        raise ValueError(f"unsupported pulse_family: {pulse_family}")

    pulse_factor = PULSE_FACTORS[pulse_family]

    omega_eff = params.omega_scale * pulse_factor / (detuning_hz / 1.0e9)
    t_pi_us = math.pi / omega_eff * 1.0e6

    epsilon_sc = params.a_sc / (detuning_hz**2)
    epsilon_leak = params.a_leak / detuning_hz
    epsilon_stark = params.a_stark * (detuning_hz / 1.0e10) ** 2 / pulse_factor
    epsilon_ctrl = params.a_ctrl * (t_pi_us / 10.0) ** 1.2 / pulse_factor

    rng = random.Random(jitter_seed)
    jitter = abs(rng.gauss(0.0, 1.6e-5))

    epsilon_tot = epsilon_sc + epsilon_leak + epsilon_stark + epsilon_ctrl + jitter
    return GatePoint(
        detuning_hz=detuning_hz,
        pulse_family=pulse_family,
        t_pi_us=t_pi_us,
        epsilon_sc=epsilon_sc,
        epsilon_leak=epsilon_leak,
        epsilon_stark=epsilon_stark,
        epsilon_ctrl=epsilon_ctrl,
        epsilon_tot=epsilon_tot,
    )


class RamanGateModel:
    """Reusable library API for evaluating Yb-171 inner-shell Raman X-gate operating points."""

    def __init__(self, params: ModelParams) -> None:
        self.params = params

    @classmethod
    def from_prior_scale(cls, prior_scale: str = "nominal", seed: int | None = None) -> "RamanGateModel":
        return cls(sample_model_params(prior_scale=prior_scale, seed=seed))

    def evaluate(self, detuning_hz: float, pulse_family: str, jitter_seed: int | None = None) -> GatePoint:
        return evaluate_gate_point(
            detuning_hz=detuning_hz,
            pulse_family=pulse_family,
            params=self.params,
            jitter_seed=jitter_seed,
        )

    def sweep(self, detuning_hz: list[float], pulse_families: list[str], jitter_seed: int | None = None) -> list[GatePoint]:
        points: list[GatePoint] = []
        seed_base = 0 if jitter_seed is None else jitter_seed
        for pulse in pulse_families:
            for index, detuning in enumerate(detuning_hz):
                points.append(self.evaluate(detuning, pulse, jitter_seed=seed_base + index))
        return points
