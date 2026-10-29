"""
RetentionLab Master Pipeline Execution Entry Point.
Executes the full end-to-end analytical workflow with a single CLI command.
"""

import sys
from retentionlab.pipeline import RetentionLabPipeline

if __name__ == "__main__":
    pipeline = RetentionLabPipeline()
    summary = pipeline.run_all()
