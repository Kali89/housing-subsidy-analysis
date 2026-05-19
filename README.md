# UK Social Housing Implicit Subsidy Analysis

Quantifying the implicit subsidy received by social and affordable rent tenants across all English local authorities, by comparing regulated rents to open market rents.

## Key finding

England's social housing stock delivers an implicit subsidy of roughly **£20–21 billion per year** to tenants — a transfer that never appears in any government budget line. The subsidy is concentrated in London and the South East, where the gap between market and social rents is widest.

## What is the implicit subsidy?

Social and affordable rents are set by regulation well below market levels. The difference — what a tenant *would* have paid in the private market minus what they *actually* pay — is an implicit transfer from the public balance sheet (which provides the land, finance, and regulatory framework that makes below-market rents possible) to the tenant. It is directionally equivalent to a housing benefit payment, but flows through the asset rather than through public expenditure.

---

## Data sources

| Dataset | Source | Period | Coverage |
|---|---|---|---|
| Private Rental Market Statistics (PRMS) | ONS | Oct 2022 – Sep 2023 | All English LAs, median monthly rents by bedroom size |
| Statistical Data Return (SDR) — Private Registered Providers | Regulator of Social Housing | 2024–25 (March 2025) | All registered PRPs, average weekly rents by bedroom size and LA |
| Statistical Data Return (SDR) — Local Authority Registered Providers | Regulator of Social Housing | 2024–25 (March 2025) | All LARPs, average weekly rents by bedroom size |
| Dwelling Stock (Table 100) | MHCLG | March 2024 | LA-owned and PRP stock by LA |
| LA District Boundaries | ONS via martinjc/UK-GeoJSON | 2013 | Used for choropleth maps |

---

## Methodology

### 1. Market rents (ONS PRMS)
Median private sector monthly rents by LA and bedroom size (1-bed, 2-bed, 3-bed, 4+ bed) from ONS PRMS tables 2.3–2.6. Areas with suppressed data (fewer than ~10 observations) are excluded.

### 2. Social rents (RSH SDR)
Average weekly net rents for General Needs social housing from two sources:

- **Private Registered Providers (PRPs)**: `SDR25_RENTS_COMB_GN` sheet aggregated from provider × LA level to LA level using weighted averages (weights = unit counts by bedroom size).
- **Local Authority Registered Providers (LARPs)**: `LADR25_Low_Cost_Rental_Data` sheet, directly at LA level.

The two streams are combined into a single LA-level weighted average, again using unit counts as weights.

Weekly rents are converted to monthly equivalents using `× 52/12`.

### 3. Affordable rents (RSH SDR)
Same process using `SDR25_ARGN_Rents` (PRP) and `LADR25_Affordable_Rent_Data` (LARP). Affordable rents are gross rents (inclusive of eligible service charges) charged at up to 80% of market rent.

### 4. Subsidy calculation

```
subsidy_social_monthly     = market_rent_monthly - social_rent_monthly
subsidy_affordable_monthly = market_rent_monthly - affordable_rent_monthly
```

Calculated at the bedroom-size level for each LA. A stock-weighted average across bedroom sizes gives a single per-LA figure.

```
subsidy_weighted = Σ(subsidy_bed × units_bed) / Σ(units_bed)
```

The total annual subsidy bill per LA is:

```
total_annual = Σ_bed (subsidy_monthly_bed × units_bed × 12)
```

---

## Caveats and limitations

1. **Data year mismatch**: ONS PRMS covers Oct 2022–Sep 2023; RSH SDR is March 2025. Private rents rose substantially over this period, so the market rent figures likely *understate* current market levels and therefore *understate* the current subsidy. The analysis is directionally valid but not a point-in-time estimate.

2. **Averages, not medians**: RSH reports *average* rents; ONS reports *median* rents. These are not the same measure. The comparison is imperfect; the subsidy figures are best read as directional estimates.

3. **Net vs gross rents**: Social rents in the SDR are *net* (excluding service charges); private sector rents in PRMS are the total rent paid. This causes a small understatement of the social subsidy.

4. **LARP geographic attribution**: LARP data is reported by the *owning* local authority regardless of where the stock is located. For most councils, stock is overwhelmingly within their own boundary; cross-boundary ownership creates a small geographic mismatch in a minority of cases.

5. **Negative affordable subsidies**: In some areas, affordable rents (capped at 80% of market) exceed the average private sector rent due to thin private rental markets or local supply conditions. These cases are retained in the data as-is.

6. **LA reorganisations**: Some LAs created after 2013 (e.g. North Yorkshire UA, formed April 2023) may not appear in all sources.

7. **The subsidy never appears in a budget**: This is part of the point. Off-balance-sheet subsidies of this scale are invisible to conventional public spending frameworks, which is one motivation for measuring them.

---

## The hidden subsidy to London's economy

The geographic concentration of the subsidy raises an argument that goes beyond housing policy. A conventional defence of social housing in high-cost areas is that it allows low-wage workers — hospital staff, transport workers, cleaners — to live close enough to central London to fill jobs the city depends on. This is sometimes called the "essential workers" argument.

But viewed from the perspective of regional economic balance, that argument is double-edged. If workers in central London can live at below-market housing costs because the state is bridging the gap, employers do not have to pay wages that fully reflect the cost of living there. The social housing stock is, in effect, a labour cost subsidy to London businesses: it expands the supply of affordable labour, keeps wages lower than a genuine market would require, and makes central London more economically competitive than it would otherwise be — at national expense.

The mechanism is invisible precisely because it operates through the housing market rather than through public expenditure. If government were to announce an explicit annual grant to central London employers to offset their wage bills, the political and distributional scrutiny would be intense. The implicit subsidy identified in this analysis — heavily concentrated in inner London, never appearing in a budget line — is economically close to that, but faces none of that scrutiny.

This matters for regional rebalancing. The UK's economic geography is unusually London-centric: London generates roughly 22% of national GDP while housing 13% of the population, and the productivity gap between London and most other English regions has widened over decades. Some of that gap reflects genuine agglomeration advantages. But some of it is built on a platform of state-subsidised labour costs that effectively tilts the economic playing field in London's favour. Businesses in Birmingham or Leeds, paying wages that must cover genuine local market housing costs, compete against London firms whose labour costs are quietly underwritten by the public sector.

A full levelling-up argument would therefore note that selling or reallocating London social housing stock — far from being harmful to the national interest — might be one of the few policy levers that could reduce London-centrism without requiring active redistribution of public spending. If London employers had to pay wages that reflected true market housing costs, the city would become measurably more expensive to operate in. Some activity and investment that currently gravitates to London because it is artificially cheap to staff would instead locate in regions where no such subsidy has distorted the labour market.

**Caveats to this argument:** The direct wage-suppression effect is probably modest in scale — social housing now represents only 5–8% of London households — and many of London's dominant industries cluster there for agglomeration reasons that would not be undone by higher wages alone. The argument is stronger as a structural and political-economy point (a hidden, unscrutinised, compounding subsidy to the richest part of the country) than as a precise labour market mechanism. It is also worth noting that social housing is one of many implicit subsidies to London: major infrastructure investment, the concentration of government employment, and national cultural institutions all tilt the same way. Social housing is a small part of a larger structural bias.

---

## Reproducing the analysis

```bash
# 1. Clone the repo and set up a virtual environment
git clone https://github.com/Kali89/housing-subsidy-analysis.git
cd housing-subsidy-analysis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Download all raw data (no credentials required)
python -m src.download

# 3. Run the full analysis pipeline
python -m src.pipeline
# → writes data/processed/subsidy_by_la_bedroom.csv
# → writes data/processed/subsidy_summary_by_la.csv

# 4. Open the notebook
jupyter lab notebooks/01_subsidy_analysis.ipynb
```

---

## Output files

| File | Description |
|---|---|
| `data/processed/subsidy_by_la_bedroom.csv` | Long format: one row per (LA, bedroom size). Contains market rents, social rents, affordable rents, unit counts, and monthly/annual subsidies. |
| `data/processed/subsidy_summary_by_la.csv` | Wide format: one row per LA. Contains bedroom-level breakdowns, stock-weighted average subsidies, and total annual subsidy bills. |

### Key columns in the summary CSV

| Column | Description |
|---|---|
| `la_code` | ONS area code (E06–E09) |
| `la_name` | Local authority name |
| `region` | English region |
| `market_rent_monthly_{bed}` | ONS median monthly private rent by bedroom size |
| `social_rent_monthly_{bed}` | RSH combined average social rent, monthly |
| `affordable_rent_monthly_{bed}` | RSH combined average affordable rent, monthly |
| `subsidy_social_wtavg_annual` | Stock-weighted average annual social subsidy per unit |
| `subsidy_affordable_wtavg_annual` | Stock-weighted average annual affordable subsidy per unit |
| `total_annual_subsidy_social` | Total annual social subsidy bill (£) |
| `total_annual_subsidy_affordable` | Total annual affordable subsidy bill (£) |
| `la_owned_stock` | LA-owned dwellings (MHCLG Table 100) |
| `prp_stock` | PRP dwellings (MHCLG Table 100) |

---

## Project structure

```
housing-subsidy-analysis/
├── data/
│   ├── raw/           # Downloaded source files (gitignored)
│   └── processed/     # Analysis outputs
├── notebooks/
│   └── 01_subsidy_analysis.ipynb
├── src/
│   ├── download.py    # Downloads all raw data
│   ├── clean_ons.py   # Parses ONS PRMS market rents
│   ├── clean_rsh_larp.py  # Parses LARP social/affordable rents
│   ├── clean_rsh_prp.py   # Aggregates PRP social/affordable rents to LA level
│   ├── clean_stock.py     # Parses MHCLG dwelling stock
│   ├── merge.py       # Joins all datasets
│   ├── analysis.py    # Computes subsidies and summaries
│   ├── pipeline.py    # Orchestrates the full run
│   └── constants.py   # Shared paths and constants
├── requirements.txt
└── README.md
```
