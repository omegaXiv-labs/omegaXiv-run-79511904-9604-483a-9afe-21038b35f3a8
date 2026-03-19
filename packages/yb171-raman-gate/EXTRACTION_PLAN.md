# Extraction Plan

1. Core contribution selection:
   - FC1 detuning-optimum surrogate and error decomposition used in UP1 validation.
   - Thresholded fastest-feasible tradeoff decision logic for tau targets.

2. Original source symbols located:
   - `experiments/up1_hybrid_validation/src/up1_validation/core.py::ModelParams`
   - `experiments/up1_hybrid_validation/src/up1_validation/core.py::evaluate_gate_point`
   - `experiments/up1_hybrid_validation/src/up1_validation/core.py::fit_surrogate`
   - `experiments/up1_hybrid_validation/src/up1_validation/core.py::floor_impossibility`
   - `experiments/up1_hybrid_validation/src/up1_validation/core.py::chance_constraint_satisfied`

3. Source-to-public API mapping:
   - `ModelParams` -> `yb171_raman_gate.model.ModelParams`
   - `evaluate_gate_point` -> `yb171_raman_gate.model.evaluate_gate_point`
   - `fit_surrogate` -> `yb171_raman_gate.tradeoff.fit_surrogate`
   - `floor_impossibility` -> `yb171_raman_gate.tradeoff.floor_impossibility`
   - `chance_constraint_satisfied` -> `yb171_raman_gate.tradeoff.chance_constraint_satisfied`
