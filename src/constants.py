"""Shared paths, constants, and mappings used across the pipeline."""

from pathlib import Path

ROOT = Path(__file__).parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

WEEKLY_TO_MONTHLY = 52 / 12

# ONS area code prefixes that correspond to lower-tier LAs in England
# E06 = unitary authorities, E07 = non-met districts, E08 = met districts, E09 = London boroughs
LA_CODE_RE = r"^E0[6-9]"

BEDROOM_LABELS = ["1_bed", "2_bed", "3_bed", "4plus_bed"]

# Human-readable labels for reports / charts
BEDROOM_DISPLAY = {
    "1_bed": "1 bedroom",
    "2_bed": "2 bedrooms",
    "3_bed": "3 bedrooms",
    "4plus_bed": "4+ bedrooms",
}
