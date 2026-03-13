from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Sequence

from .model import GatePoint, RamanGateModel


@dataclass(frozen=True)
class SurrogateFit:
    """FC1-style convex surrogate fit for epsilon(Delta)."""

    a: float
    b: float
    c: float
    r2: float
    delta_star_hz: float


@dataclass(frozen=True)
class TradeoffRow:
    """Best feasible row for a target infidelity threshold."""

    tau: float
    feasible: bool
    best_t_pi_us: float | None
    best_epsilon_tot: float | None
    best_detuning_hz: float | None
    best_pulse_family: str | None
    dominant_error_channel: str | None


def _solve_linear_system_3x3(matrix: list[list[float]], rhs: list[float]) -> tuple[float, float, float]:
    # Compact Gaussian elimination for the fixed 3x3 normal equations.
    a = [row[:] + [rhs[idx]] for idx, row in enumerate(matrix)]
    n = 3

    for pivot in range(n):
        max_row = max(range(pivot, n), key=lambda r: abs(a[r][pivot]))
        a[pivot], a[max_row] = a[max_row], a[pivot]
        pivot_val = a[pivot][pivot]
        if abs(pivot_val) < 1e-15:
            raise ValueError("degenerate linear system in surrogate fit")

        for col in range(pivot, n + 1):
            a[pivot][col] /= pivot_val

        for row in range(n):
            if row == pivot:
                continue
            factor = a[row][pivot]
            for col in range(pivot, n + 1):
                a[row][col] -= factor * a[pivot][col]

    return a[0][3], a[1][3], a[2][3]


def fit_surrogate(detuning_hz: Sequence[float], epsilon_tot: Sequence[float]) -> SurrogateFit:
    """Fit A/Delta^2 + B*Delta^2 + C using least squares normal equations."""

    if len(detuning_hz) != len(epsilon_tot):
        raise ValueError("detuning_hz and epsilon_tot must have equal length")
    if len(detuning_hz) < 3:
        raise ValueError("at least 3 points are required for surrogate fitting")

    # Normalize detuning before constructing the design terms to avoid
    # ill-conditioned normal equations at Hz-scale magnitudes.
    inv_x: list[float] = []
    x: list[float] = []
    y: list[float] = []
    for detuning, eps in zip(detuning_hz, epsilon_tot):
        if detuning <= 0.0:
            raise ValueError("detuning_hz values must be positive")
        x_val = (detuning / 1.0e10) ** 2
        inv_x.append(1.0 / x_val)
        x.append(x_val)
        y.append(eps)

    s11 = sum(v * v for v in inv_x)
    s12 = sum(inv_x[idx] * x[idx] for idx in range(len(x)))
    s13 = sum(inv_x)
    s22 = sum(v * v for v in x)
    s23 = sum(x)
    s33 = float(len(x))

    r1 = sum(inv_x[idx] * y[idx] for idx in range(len(y)))
    r2 = sum(x[idx] * y[idx] for idx in range(len(y)))
    r3 = sum(y)

    normal_matrix = [
        [s11, s12, s13],
        [s12, s22, s23],
        [s13, s23, s33],
    ]
    a_coeff, b_coeff, c_coeff = _solve_linear_system_3x3(normal_matrix, [r1, r2, r3])

    pred = [a_coeff * inv_x[idx] + b_coeff * x[idx] + c_coeff for idx in range(len(x))]
    mean_y = sum(y) / len(y)
    ss_res = sum((y[idx] - pred[idx]) ** 2 for idx in range(len(y)))
    ss_tot = sum((value - mean_y) ** 2 for value in y) + 1e-12
    r2 = 1.0 - ss_res / ss_tot

    delta_star_hz = (
        1.0e10 * math.pow(a_coeff / b_coeff, 0.25) if a_coeff > 0.0 and b_coeff > 0.0 else math.nan
    )

    return SurrogateFit(
        a=a_coeff,
        b=b_coeff,
        c=c_coeff,
        r2=r2,
        delta_star_hz=delta_star_hz,
    )


def unimodality_pass(values: Sequence[float]) -> bool:
    """Return True if the sequence has at most one monotonicity switch."""

    if len(values) < 3:
        return True
    signs: list[int] = []
    for idx in range(1, len(values)):
        diff = values[idx] - values[idx - 1]
        if abs(diff) < 1e-14:
            continue
        signs.append(1 if diff > 0.0 else -1)

    if len(signs) < 2:
        return True

    sign_changes = 0
    for idx in range(1, len(signs)):
        if signs[idx] != signs[idx - 1]:
            sign_changes += 1
    return sign_changes <= 1


def bootstrap_ci(
    samples: Sequence[float],
    alpha: float = 0.10,
    n_boot: int = 600,
    seed: int | None = None,
) -> tuple[float, float, float]:
    """Bootstrap confidence interval for the sample mean."""

    if not samples:
        raise ValueError("samples must be non-empty")
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")

    rng = random.Random(seed)
    means: list[float] = []
    sample_list = list(samples)

    for _ in range(n_boot):
        draw = [rng.choice(sample_list) for _ in range(len(sample_list))]
        means.append(sum(draw) / len(draw))

    means.sort()

    def quantile(p: float) -> float:
        pos = p * (len(means) - 1)
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))
        if lo == hi:
            return means[lo]
        frac = pos - lo
        return means[lo] * (1.0 - frac) + means[hi] * frac

    return quantile(alpha / 2.0), quantile(0.5), quantile(1.0 - alpha / 2.0)


def floor_impossibility(epsilon_floor: float, tau: float) -> bool:
    return epsilon_floor > tau


def check_monotone_feasibility(tau_values: Sequence[float], feasible_flags: Sequence[bool]) -> bool:
    if len(tau_values) != len(feasible_flags):
        raise ValueError("tau_values and feasible_flags must have equal length")

    paired = sorted(zip(tau_values, feasible_flags), key=lambda item: item[0], reverse=True)
    seen_false = False
    for _, feasible in paired:
        if not feasible:
            seen_false = True
        if seen_false and feasible:
            return False
    return True


def chance_constraint_satisfied(epsilon_samples: Iterable[float], tau: float, alpha: float) -> bool:
    samples = list(epsilon_samples)
    if not samples:
        raise ValueError("epsilon_samples must be non-empty")
    success_rate = sum(1 for value in samples if value <= tau) / float(len(samples))
    return success_rate >= 1.0 - alpha


def best_feasible_point(points: Sequence[GatePoint], tau: float) -> GatePoint | None:
    feasible = [point for point in points if point.epsilon_tot <= tau]
    if not feasible:
        return None
    return min(feasible, key=lambda point: point.t_pi_us)


def build_tradeoff_table(
    model: RamanGateModel,
    detuning_grid_hz: Sequence[float],
    pulse_families: Sequence[str],
    tau_targets: Sequence[float],
    jitter_seed: int = 0,
) -> list[TradeoffRow]:
    """Generate tau-indexed fastest-feasible rows from a model sweep."""

    points = model.sweep(
        detuning_hz=list(detuning_grid_hz),
        pulse_families=list(pulse_families),
        jitter_seed=jitter_seed,
    )

    rows: list[TradeoffRow] = []
    for tau in tau_targets:
        best = best_feasible_point(points=points, tau=tau)
        if best is None:
            rows.append(
                TradeoffRow(
                    tau=tau,
                    feasible=False,
                    best_t_pi_us=None,
                    best_epsilon_tot=None,
                    best_detuning_hz=None,
                    best_pulse_family=None,
                    dominant_error_channel=None,
                )
            )
            continue

        rows.append(
            TradeoffRow(
                tau=tau,
                feasible=True,
                best_t_pi_us=best.t_pi_us,
                best_epsilon_tot=best.epsilon_tot,
                best_detuning_hz=best.detuning_hz,
                best_pulse_family=best.pulse_family,
                dominant_error_channel=best.dominant_error_channel,
            )
        )

    return rows
