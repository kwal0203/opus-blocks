from __future__ import annotations

import argparse
import json
from pathlib import Path

from opus_blocks.evaluation.runner import (
    evaluate_regression_gate,
    load_golden_dataset,
    run_golden_set,
    write_baseline,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run golden set evaluation.")
    parser.add_argument("dataset", type=Path, help="Path to golden dataset JSON.")
    parser.add_argument(
        "--baseline-out",
        type=Path,
        help="Optional path to write baseline metrics JSON.",
    )
    parser.add_argument(
        "--min-support-rate",
        type=float,
        default=0.0,
        help="Minimum acceptable sentence support rate.",
    )
    parser.add_argument(
        "--max-false-support-rate",
        type=float,
        default=0.0,
        help="Maximum acceptable false support rate.",
    )
    args = parser.parse_args()

    dataset = load_golden_dataset(args.dataset)
    result = run_golden_set(dataset)

    gate = evaluate_regression_gate(
        dataset.baseline_metrics,
        result.metrics,
        min_support_rate=args.min_support_rate,
        max_false_support_rate=args.max_false_support_rate,
    )

    summary = {
        "version": dataset.version,
        "metrics": result.metrics.to_dict(),
        "gate_passed": gate.passed,
        "diffs": gate.diffs,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.baseline_out:
        write_baseline(args.baseline_out, result.metrics)

    return 0 if gate.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
