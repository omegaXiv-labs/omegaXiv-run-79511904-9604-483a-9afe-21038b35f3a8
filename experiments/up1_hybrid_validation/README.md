# UP1 Hybrid Validation Experiments

This package implements the `validation_simulation` phase for the UP1-centered hybrid plan:
- `EXP_H1_FC1_DETUNING_OPTIMUM_GRID`
- `EXP_H3_FC2_FEASIBILITY_FLOOR_STRESS`
- `EXP_H4_FC3_BAYES_CHANCE_CONSTRAINED_TABLE`
- `EXP_INTEGRATED_UP1_EVIDENCE_ASSEMBLY`

## Structure
- `src/up1_validation/core.py`: model equations, surrogate fitting, theorem checks.
- `src/up1_validation/analysis.py`: experiment orchestration, datasets/tables/figures, summary assembly.
- `src/up1_validation/plotting.py`: seaborn/matplotlib styling and PDF readability rasterization checks.
- `src/up1_validation/symbolic.py`: SymPy validations aligned with `phase_outputs/SYMPY.md`.
- `run_experiments.py`: thin CLI entrypoint.
- `configs/experiment_config.json`: seeds, baselines, sweeps, metrics.
- `tests/`: unit and smoke tests.

## Commands
- `python experiments/up1_hybrid_validation/run_experiments.py --config experiments/up1_hybrid_validation/configs/experiment_config.json --output-dir experiments/up1_hybrid_validation/output`
- `ruff check experiments/up1_hybrid_validation`
- `mypy experiments/up1_hybrid_validation/src`
- `pytest experiments/up1_hybrid_validation/tests -q`

## Outputs
- Experiment datasets: `experiments/up1_hybrid_validation/output/datasets/`
- Figures (PDF): `paper/figures/`
- Tables: `paper/tables/`
- Results summary: `experiments/up1_hybrid_validation/output/results_summary.json`
- Run log: `experiments/experiment_log.jsonl`
