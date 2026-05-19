"""
Download all raw data sources into data/raw/.

Run this first:  python -m src.download
"""

import sys
from pathlib import Path

import requests
from tqdm import tqdm

RAW = Path(__file__).parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SOURCES = {
    # ONS Private Rental Market Statistics (PRMS)
    # Most recent release: October 2022 – September 2023 (published 20 Dec 2023)
    # This series is now discontinued; no later edition available as of 2024.
    "ons_prms.xls": (
        "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/housing/"
        "datasets/privaterentalmarketsummarystatisticsinengland/"
        "october2022toseptember2023/privaterentalmarketstatistics231220.xls"
    ),
    # RSH – Private Registered Providers full data release 2024-25 (Oct 2025)
    "rsh_prp_2025.xlsx": (
        "https://assets.publishing.service.gov.uk/media/"
        "69049c39ef26c341988b24e2/PRP_Data_Release_2025_Full_Data_FINAL_V1.1.xlsx"
    ),
    # RSH – Local Authority Registered Providers full data release 2024-25 (Oct 2025)
    "rsh_larp_2025.xlsx": (
        "https://assets.publishing.service.gov.uk/media/"
        "68f894a40cef4b4e32f12e4c/LARP_Data_Release_2025_Full_Data_FINAL_V1.0.xlsx"
    ),
    # RSH – PRP geographic look-up tool (summary by LA) 2024-25
    "rsh_prp_geo_2025.xlsx": (
        "https://assets.publishing.service.gov.uk/media/"
        "68f8a6560794bb80118bb71f/GEO_PRP_TOOL_2025_FINAL_V1.0.xlsx"
    ),
    # MHCLG – Table 100: dwellings by tenure and district, England
    "mhclg_table100.ods": (
        "https://assets.publishing.service.gov.uk/media/"
        "682deb00b33f68eaba95391b/LiveTable100.ods"
    ),
    # ONS/martinjc – Local Authority District boundaries for England (GeoJSON, 2013 edition)
    # Used for choropleth mapping.  Note: LAs reorganised after 2013 may be absent.
    "england_lad_boundaries.geojson": (
        "https://github.com/martinjc/UK-GeoJSON/raw/master/json/"
        "administrative/eng/lad.json"
    ),
}


def download_file(filename: str, url: str, overwrite: bool = False) -> Path:
    dest = RAW / filename
    if dest.exists() and not overwrite:
        print(f"  already exists, skipping: {filename}")
        return dest

    print(f"  downloading {filename} ...")
    try:
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
    except requests.HTTPError as e:
        print(f"\n[ERROR] Could not download {filename}: {e}", file=sys.stderr)
        print(f"  URL attempted: {url}", file=sys.stderr)
        print(f"  Please download manually and place at: {dest}", file=sys.stderr)
        return None

    total = int(r.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=filename, leave=False
    ) as bar:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

    print(f"  saved to {dest} ({dest.stat().st_size / 1024:.0f} KB)")
    return dest


def main(overwrite: bool = False):
    print("=== Downloading raw data sources ===")
    failed = []
    for filename, url in SOURCES.items():
        result = download_file(filename, url, overwrite=overwrite)
        if result is None:
            failed.append(filename)

    if failed:
        print(
            f"\n[WARNING] {len(failed)} file(s) could not be downloaded automatically:",
            file=sys.stderr,
        )
        for f in failed:
            print(f"  - {f}", file=sys.stderr)
        print(
            "\nPlease download the missing files manually (see URLs in src/download.py)"
            " and place them in data/raw/ before running the pipeline.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("\nAll files downloaded successfully.")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--overwrite", action="store_true", help="Re-download existing files")
    args = p.parse_args()
    main(overwrite=args.overwrite)
