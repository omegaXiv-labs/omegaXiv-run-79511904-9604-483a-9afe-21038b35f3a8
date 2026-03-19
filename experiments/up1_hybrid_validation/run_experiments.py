from __future__ import annotations

import argparse
import json
from pathlib import Path

from up1_validation.analysis import run_all_experiments


def main() -> None:
    parser = argparse.ArgumentParser(description="Run UP1 hybrid validation experiments.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--experiment-log",
        default=Path("experiments/experiment_log.jsonl"),
        type=Path,
    )
    args = parser.parse_args()

    result = run_all_experiments(args.config, args.output_dir, args.experiment_log)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
