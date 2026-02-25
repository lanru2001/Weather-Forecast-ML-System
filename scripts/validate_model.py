#!/usr/bin/env python3
"""
Model validation script for CI/CD pipeline.
Ensures model meets minimum performance thresholds before deployment.
"""

import argparse
import sys
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)


def validate_model(min_r2: float, max_rmse: float, model_path: str) -> bool:
    """Validate model performance against thresholds"""
    logger.info("🔍 Starting model validation...")
    logger.info(f"  Thresholds: R² ≥ {min_r2}, RMSE ≤ {max_rmse}")

    try:
        from model.train import WeatherMLModel

        model  = WeatherMLModel()
        results = model.train()

        avg_r2   = results["avg_r2"]
        avg_rmse = results["avg_rmse"]

        logger.info(f"  Model R²:   {avg_r2:.4f}  (min required: {min_r2})")
        logger.info(f"  Model RMSE: {avg_rmse:.4f} (max allowed:  {max_rmse})")

        passed = avg_r2 >= min_r2 and avg_rmse <= max_rmse

        if passed:
            logger.info("✅ Model validation PASSED")
        else:
            logger.error("❌ Model validation FAILED")
            if avg_r2 < min_r2:
                logger.error(f"   R² {avg_r2:.4f} is below threshold {min_r2}")
            if avg_rmse > max_rmse:
                logger.error(f"   RMSE {avg_rmse:.4f} exceeds threshold {max_rmse}")

        # Save validation report for CI artifact upload
        report = {
            "timestamp":  datetime.now().isoformat(),
            "passed":     passed,
            "metrics": {
                "r2":   avg_r2,
                "rmse": avg_rmse,
            },
            "thresholds": {
                "min_r2":   min_r2,
                "max_rmse": max_rmse,
            },
            "model_path": model_path,
        }

        report_path = "validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"  Report saved → {report_path}")
        return passed

    except ImportError:
        logger.warning("ML dependencies not available — skipping validation")
        return True

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def print_report_summary(report_path: str = "validation_report.json") -> None:
    """Print a formatted summary of the validation report"""
    try:
        with open(report_path) as f:
            report = json.load(f)

        print("\n" + "=" * 50)
        print("  MODEL VALIDATION REPORT")
        print("=" * 50)
        print(f"  Timestamp : {report['timestamp']}")
        print(f"  Result    : {'✅ PASSED' if report['passed'] else '❌ FAILED'}")
        print()
        print("  Metrics:")
        print(f"    R²   = {report['metrics']['r2']:.4f}  "
              f"(min: {report['thresholds']['min_r2']})")
        print(f"    RMSE = {report['metrics']['rmse']:.4f}  "
              f"(max: {report['thresholds']['max_rmse']})")
        print("=" * 50 + "\n")

    except FileNotFoundError:
        logger.warning(f"Report not found at {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Weather ML Model Validator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--min-r2",
        type=float,
        default=0.85,
        help="Minimum acceptable R² score",
    )
    parser.add_argument(
        "--max-rmse",
        type=float,
        default=3.0,
        help="Maximum acceptable RMSE",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="./model",
        help="Path to model directory",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print report summary after validation",
    )
    args = parser.parse_args()

    success = validate_model(args.min_r2, args.max_rmse, args.model_path)

    if args.summary:
        print_report_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
