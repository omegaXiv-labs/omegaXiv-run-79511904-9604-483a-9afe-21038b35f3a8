from __future__ import annotations

from pathlib import Path

import sympy as sp


def run_sympy_validation(report_path: Path) -> dict[str, str | bool]:
    A, B, C, x, tau, eps_floor = sp.symbols("A B C x tau eps_floor", positive=True)

    f = A / x + B * x + C
    d2f = sp.diff(f, x, 2)
    d1f = sp.diff(f, x)
    stationary = sp.solve(sp.Eq(d1f, 0), x)
    x_star = stationary[0]
    f_x_star = sp.simplify(f.subs(x, x_star))

    h1_convex = sp.simplify(d2f - (2 * A / x**3)) == 0
    h1_stationary = sp.simplify(x_star - sp.sqrt(A / B)) == 0
    h1_min_value = sp.simplify(f_x_star - (2 * sp.sqrt(A * B) + C)) == 0

    implication = sp.Implies(eps_floor > tau, sp.Not(sp.Le(sp.Symbol("epsilon_tot", positive=True), tau)))

    lines = [
        "# SymPy Validation Report",
        "",
        "## H1 Detuning-Optimum Checks",
        f"- d2f/dx2 identity valid: {h1_convex}",
        f"- Stationary point x*=sqrt(A/B): {h1_stationary}",
        f"- Optimal surrogate value f(x*)=2*sqrt(A*B)+C: {h1_min_value}",
        "",
        "## H3 Feasibility-Floor Logic",
        f"- Symbolic implication object constructed: {implication}",
        "- Logical interpretation: if epsilon_floor > tau, feasible set under epsilon_tot <= tau is empty.",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "h1_convex": bool(h1_convex),
        "h1_stationary": bool(h1_stationary),
        "h1_min_value": bool(h1_min_value),
        "h3_implication_constructed": True,
    }
