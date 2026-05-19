# England's Hidden Housing Subsidy

England's social housing system delivers a **£21 billion annual implicit subsidy** — a transfer larger than the entire overseas aid budget that has never been voted on, never appears in any spending review, and is overwhelmingly concentrated in the wealthiest part of the country.

This repository quantifies that subsidy for every English local authority, maps its geographic distribution, and examines what it means for regional economic fairness.

---

## The argument

Social and affordable rents are set by regulation well below market levels. The gap between what a tenant *would* pay on the open market and what they *actually* pay is an implicit transfer from the public balance sheet to the tenant. It is economically equivalent to a housing benefit payment, but it flows through the asset rather than through public expenditure — which is why it never appears in any budget.

When you add up this gap across all 3.1 million social homes in England, the total is roughly **£21 billion per year**.

The geographic distribution of that subsidy is not neutral. London receives **47% of the total** while holding only **19% of the social housing stock**. The South East adds a further 14%. Together, the two most expensive regions of England absorb **60% of the entire national subsidy** — more than the combined share of the North East, North West, Yorkshire, East Midlands, and West Midlands.

This is not a rounding error. It is a structural feature of the system that has been compounding for decades and is not self-correcting.

---

## Key findings

- **£21bn/yr** total implicit social housing subsidy across England, never appearing in any government budget
- **London alone: £9.7bn/yr** — 47% of the national total from 19% of the stock
- **London + South East: £12.5bn/yr** — 60% of the national total
- **Kensington & Chelsea: £30,213/unit/year** in implicit subsidy — the highest of any LA
- **Redcar & Cleveland: £694/unit/year** — the lowest. The same national system delivers **44× more** to a K&C tenant than to one in Redcar
- The equivalent annual gross wage saving to London employers: **£13.5bn** — social housing allows businesses to pay wages that do not reflect the true cost of living in the city
- England is building Social Rent homes at **0.22% of stock per year** — at that rate, the existing stock turns over every **462 years**
- Social Rent completions have fallen **79% since their early-1990s peak** (57,000/yr → 12,000/yr). We are not building our way out of this

---

## The subsidy as a London employer benefit

The conventional defence of social housing in high-cost cities is the "essential workers" argument: hospital staff, cleaners, and transport workers need affordable housing close to where they work. That argument is true as far as it goes. But it has a less comfortable implication that is rarely stated.

If workers in central London can live at below-market housing costs because the public sector is bridging the gap, their employers do not have to pay wages that reflect the full cost of living there. Social housing in London is, in economic terms, a labour cost subsidy to London businesses. It expands the supply of affordable labour, keeps wages lower than a genuine market would require, and makes central London more economically competitive than it would otherwise be — at national expense.

The gross-up calculation in this analysis estimates that London employers save the equivalent of **£13.5bn per year** in wages they would otherwise need to pay to attract workers at market housing costs. That is a subsidy larger than the entire budget for HS2's northern legs — which were cancelled. It is paid not by London employers, not from London's council tax, but effectively from the national balance sheet through the suppression of returns on publicly held housing assets.

If this were an explicit payment — an annual grant from the Treasury to London businesses to offset their wage bills — the political scrutiny would be intense. It operates invisibly precisely because it runs through the housing market.

---

## The supply problem: it is not self-correcting

The geographic distribution of social housing is essentially fixed by decades of construction decisions that are now nearly impossible to reverse. The stock turns over at 0.22% per year. Even if government redirected every new social home to the North and Midlands tomorrow, it would take many decades to materially change the distribution.

New supply is making things worse, not better. Of the 12,000 Social Rent homes built in 2024, the majority were in London and the South East — where development economics for housing associations is more favourable but where the subsidy per unit is already highest. The North East, which has the worst renewal rate of any English region (0.07%/yr), is building virtually nothing.

The replacement tenure — Affordable Rent at 80% of market — does not compress geographic inequality. It replicates it. A "social" tenant in Kensington paying Affordable Rent pays **£1,252/month**. A private tenant in Liverpool pays **£675/month** in an open market. The government-subsidised "affordable" home costs nearly twice as much as a genuine market home in the North.

---

## The hidden subsidy in context

The standard counter-argument is that London is a net fiscal contributor — London generates roughly 22% of England's GDP and probably a larger share of national tax revenues, some of which flows to poorer regions through public spending. That argument is correct in broad outline but overstated in ways that matter for this analysis.

Several large transfers to London do not appear on any intra-regional balance sheet:

- **The implicit housing subsidy** (this analysis): ~£10bn/yr to London and the South East, entirely off-balance-sheet
- **London Weighting**: Central government pays NHS staff, teachers, civil servants, police, and fire workers a London supplement — roughly £1.5–2bn/yr from national budgets to compensate for housing costs that are themselves partly a policy choice
- **Infrastructure investment**: Transport for London has received substantially higher per-capita capital investment than any Northern region for decades. The Elizabeth Line alone cost ~£19bn. HS2 promised connectivity benefits to the North, delivered the southern sections at enormous cost, then cancelled the Manchester and Leeds legs
- **National institutional concentration**: The British Museum, National Gallery, V&A, National Theatre, and dozens of other nationally-funded institutions are sited in London, with economic multipliers that benefit London disproportionately
- **Corporation tax attribution**: Large firms headquartered in London pay tax attributed to London but generate revenues nationally

None of this overturns "London is a net contributor." But the margin is almost certainly smaller than headline regional accounts suggest — and at least one large, compounding, unscrutinised transfer flows *to* London rather than from it.

---

## A note on tenure

The analysis covers Social Rent (formula-based, ~33–75% of market depending on region) and Affordable Rent (up to 80% of market, introduced 2012). The geographic argument holds regardless of tenure: in both cases the subsidy is deepest where rents are highest. Affordable Rent does not compress geographic inequality — it replicates it, giving every tenant the same percentage discount regardless of whether their local market is genuinely affordable relative to their income. In 11 local authorities with thin rental markets (mostly in the North East and North West), Affordable Rent contracts from earlier years now exceed the current market rent — those tenants pay more than the open market alternative. The tenure distinction matters for debates about housing policy design; the geographic concentration of subsidy is the structural problem regardless of which tenure delivers it.

---

## Data sources

| Dataset | Source | Period | Coverage |
|---|---|---|---|
| Private Rental Market Statistics (PRMS) | ONS | Oct 2022 – Sep 2023 | All English LAs, median monthly rents by bedroom size |
| Statistical Data Return (SDR) — Private Registered Providers | Regulator of Social Housing | 2024–25 (March 2025) | All registered PRPs, average weekly rents by bedroom size and LA |
| Statistical Data Return (SDR) — Local Authority Registered Providers | Regulator of Social Housing | 2024–25 (March 2025) | All LARPs, average weekly rents by bedroom size |
| Dwelling Stock (Table 100) | MHCLG | March 2024 | LA-owned and PRP stock by LA |
| Affordable Housing Supply | MHCLG | 1991–2025 | Completions by tenure, LA, year |
| LA District Boundaries | ONS via martinjc/UK-GeoJSON | 2013 | Used for choropleth maps |

---

## Methodology

### 1. Market rents (ONS PRMS)
Median private sector monthly rents by LA and bedroom size (1-bed, 2-bed, 3-bed, 4+ bed) from ONS PRMS tables 2.3–2.6. Areas with suppressed data (fewer than ~10 observations) are excluded.

### 2. Social rents (RSH SDR)
Average weekly net rents for General Needs social housing from two sources:

- **Private Registered Providers (PRPs)**: `SDR25_RENTS_COMB_GN` sheet aggregated from provider × LA level to LA level using weighted averages (weights = unit counts by bedroom size).
- **Local Authority Registered Providers (LARPs)**: `LADR25_Low_Cost_Rental_Data` sheet, directly at LA level.

The two streams are combined into a single LA-level weighted average, again using unit counts as weights. Weekly rents are converted to monthly equivalents using `× 52/12`.

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
total_annual     = Σ_bed (subsidy_monthly_bed × units_bed × 12)
```

### 5. Employer wage subsidy gross-up
The implicit subsidy is grossed up by `1 / (1 − 0.28) = 1.39×` to estimate the equivalent gross wage an employer would need to pay to fully compensate a worker for the difference between social and market rent, assuming a 28% effective marginal rate (basic-rate income tax + employee NI).

---

## Caveats and limitations

1. **Data year mismatch**: ONS PRMS covers Oct 2022–Sep 2023; RSH SDR is March 2025. Private rents rose substantially over this period, so the market rent figures likely *understate* current market levels and therefore *understate* the current subsidy. The analysis is directionally valid but not a point-in-time estimate.

2. **Averages, not medians**: RSH reports *average* rents; ONS reports *median* rents. These are not the same measure. The subsidy figures are best read as directional estimates.

3. **Net vs gross rents**: Social rents in the SDR are *net* (excluding service charges); private sector rents in PRMS are the total rent paid. This causes a small understatement of the social subsidy.

4. **LARP geographic attribution**: LARP data is reported by the *owning* local authority regardless of where the stock is located.

5. **Negative affordable subsidies**: In some areas, affordable rents exceed the average private sector rent due to thin private rental markets. These cases are retained as-is.

6. **LA reorganisations**: Some LAs created after 2013 (e.g. North Yorkshire UA) may not appear in all sources.

7. **The subsidy never appears in a budget**: This is part of the point. Off-balance-sheet subsidies of this scale are invisible to conventional public spending frameworks.

---

## Reproducing the analysis

```bash
git clone https://github.com/Kali89/housing-subsidy-analysis.git
cd housing-subsidy-analysis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m src.download    # download all raw data (no credentials required)
python -m src.pipeline    # → data/processed/subsidy_by_la_bedroom.csv
                          # → data/processed/subsidy_summary_by_la.csv

# Visualisations
python -m src.equalisation
python -m src.labour_subsidy
python -m src.new_supply
python -m src.affordable_rent
python -m src.tweet_charts   # Twitter-optimised standalone charts

jupyter lab notebooks/01_subsidy_analysis.ipynb
```

---

## Output files

| File | Description |
|---|---|
| `data/processed/subsidy_by_la_bedroom.csv` | Long format: one row per (LA, bedroom size). Market rents, social rents, affordable rents, unit counts, monthly/annual subsidies. |
| `data/processed/subsidy_summary_by_la.csv` | Wide format: one row per LA. Bedroom-level breakdowns, stock-weighted averages, total annual subsidy bills. |
| `data/processed/fig_labour_subsidy.png` | 3-panel: rent wedge, disproportionality, employer wage saving by region |
| `data/processed/fig_new_supply.png` | 3-panel: SR completions 1991–2025, tenure mix by region, renewal rate |
| `data/processed/fig_affordable_rent.png` | 3-panel: rent ladder, SR/AR as % of market, LA-level scatter |
| `data/processed/fig_equalisation_curve.png` | Cost of equalising subsidy per unit to any target |
| `data/processed/tweet_01_invisible_transfer.png` | £21bn by region — London 47% |
| `data/processed/tweet_02_per_unit_subsidy.png` | £15,600/yr per London home vs £1,906 in North East |
| `data/processed/tweet_03_employer_subsidy.png` | Employer wage saving by region |
| `data/processed/tweet_04_supply_collapse.png` | Social Rent completions 1991–2025 |
| `data/processed/tweet_05_north_vs_london.png` | North: 2× the homes, 3.3× less money |
| `data/processed/tweet_06_subsidy_lottery.png` | 44:1 per-unit lottery, K&C vs Redcar |

---

## Project structure

```
housing-subsidy-analysis/
├── data/
│   ├── raw/           # Downloaded source files (gitignored)
│   └── processed/     # Analysis outputs and charts
├── notebooks/
│   └── 01_subsidy_analysis.ipynb
├── src/
│   ├── download.py        # Downloads all raw data
│   ├── clean_ons.py       # Parses ONS PRMS market rents
│   ├── clean_rsh_larp.py  # Parses LARP social/affordable rents
│   ├── clean_rsh_prp.py   # Aggregates PRP social/affordable rents to LA level
│   ├── clean_stock.py     # Parses MHCLG dwelling stock
│   ├── merge.py           # Joins all datasets
│   ├── analysis.py        # Computes subsidies and summaries
│   ├── pipeline.py        # Orchestrates the full run
│   ├── equalisation.py    # Equalisation cost curve
│   ├── labour_subsidy.py  # London labour subsidy visualisation
│   ├── new_supply.py      # Social housing new supply visualisation
│   ├── affordable_rent.py # Affordable Rent geographic inequality
│   ├── tweet_charts.py    # Twitter-optimised standalone charts
│   └── constants.py       # Shared paths and constants
├── requirements.txt
└── README.md
```
