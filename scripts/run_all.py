"""Single-command runner for entire RetentionLab analytical lifecycle."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retentionlab.pipeline import run_pipeline


def main():
    print("Executing full RetentionLab analytical workflow...")
    run_pipeline()


if __name__ == "__main__":
    main()
