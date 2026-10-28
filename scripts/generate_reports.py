"""Report generation script for Excel, Power BI CSVs, and analytical summaries."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.pipeline import run_pipeline


def main():
    print("Executing scripts/generate_reports.py...")
    run_pipeline(DEFAULT_CONFIG)
    print("All reports generated successfully.")


if __name__ == "__main__":
    main()
