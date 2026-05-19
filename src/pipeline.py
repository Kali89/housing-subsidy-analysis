"""
Entry point for the full analysis pipeline.

Usage:
    python -m src.pipeline

Steps:
    1. (Optional) Download raw data  →  python -m src.download
    2. Clean and merge all sources
    3. Compute subsidies
    4. Write processed CSVs to data/processed/
"""

from .analysis import run_analysis


def main():
    long, summary = run_analysis()
    print("\nPipeline complete.")
    return long, summary


if __name__ == "__main__":
    main()
