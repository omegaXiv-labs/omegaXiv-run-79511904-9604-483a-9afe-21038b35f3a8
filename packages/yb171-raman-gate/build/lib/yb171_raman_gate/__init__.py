"""Reusable Yb-171 Raman gate tradeoff package extracted from omegaXiv UP1 validation."""

from .model import GatePoint, ModelParams, PULSE_FACTORS, RamanGateModel, evaluate_gate_point, sample_model_params
from .tradeoff import (
    SurrogateFit,
    TradeoffRow,
    best_feasible_point,
    bootstrap_ci,
    build_tradeoff_table,
    chance_constraint_satisfied,
    check_monotone_feasibility,
    fit_surrogate,
    floor_impossibility,
    unimodality_pass,
)

__all__ = [
    "GatePoint",
    "ModelParams",
    "PULSE_FACTORS",
    "RamanGateModel",
    "SurrogateFit",
    "TradeoffRow",
    "best_feasible_point",
    "bootstrap_ci",
    "build_tradeoff_table",
    "chance_constraint_satisfied",
    "check_monotone_feasibility",
    "evaluate_gate_point",
    "fit_surrogate",
    "floor_impossibility",
    "sample_model_params",
    "unimodality_pass",
]
