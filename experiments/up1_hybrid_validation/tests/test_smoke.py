from __future__ import annotations

from pathlib import Path

from up1_validation.symbolic import run_sympy_validation


def test_sympy_report(tmp_path: Path) -> None:
    out = tmp_path / "sympy.md"
    checks = run_sympy_validation(out)
    assert out.exists()
    assert checks["h1_convex"]
    assert checks["h1_stationary"]
    assert checks["h1_min_value"]
