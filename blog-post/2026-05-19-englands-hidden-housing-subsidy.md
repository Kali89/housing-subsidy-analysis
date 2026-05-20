---
layout: post
title: "England's Hidden Housing Subsidy"
date: 2026-05-19
tags: [data, politics, housing, inequality]
---

England's social housing system delivers a **£21 billion annual subsidy** that has never been voted on, never appears in any spending review, and is overwhelmingly concentrated in the wealthiest part of the country. This post quantifies it — for every local authority in England — and asks where it goes.<!--more-->

The short answer is: to London.

---

## The mechanism

Social rents are set by regulation well below market levels. The gap between what a tenant *would* pay on the open market and what they *actually* pay is an economic transfer — equivalent in effect to a housing benefit payment, but flowing through the asset rather than through public expenditure. It never appears in any budget because it isn't technically a payment at all; it's a suppression of returns on publicly held housing assets.

Add that gap up across all 3.2 million social homes in England and the total is roughly £21 billion per year.

---

## Where it goes

![England's £21bn implicit social housing subsidy by region](/assets/images/housing-01-invisible-transfer.png)

London receives **47% of the total implicit subsidy** while holding only **19% of the social housing stock**. London and the South East together absorb **60%** — more than the combined share of every Northern and Midlands region.

The comparison that hits hardest:

![The North has 2x as many social homes as London but gets 3.3x less money](/assets/images/housing-05-north-vs-london.png)

The North East, North West, and Yorkshire combined have **940,000 social homes** to London's **620,000**. They receive **£3 billion per year** in implicit subsidy. London receives **£9.7 billion**. More homes. 3.3 times less money.

---

## The 44:1 lottery

Every local authority in England operates under the same national policy and the same formula. The subsidy each tenant receives depends entirely on where they live.

![Regional beeswarm showing per-unit subsidy — 44:1 between K&C and Redcar](/assets/images/housing-06-subsidy-lottery.png)

Kensington & Chelsea: **£30,213 per social home per year**. Redcar & Cleveland: **£694**. A ratio of 44:1 — not between different countries or systems, but between two English councils operating under identical national rules. Every dot on that chart is a local authority.

---

## Why it never corrects itself

The subsidy is mechanically the difference between market rent and social rent. Social rents are set by a national formula almost entirely decoupled from the market — they track CPI and wage growth, not property prices. London market rents track London property prices.

So as London house prices diverge from the North — as they have, consistently, for thirty years — the subsidy gap widens *automatically*. Nobody makes a wrong decision. No policy changes. London property just keeps doing what it always does, and the transfer compounds indefinitely, entirely off any balance sheet.

The stock can't self-correct either. England builds Social Rent homes at 0.22% of existing stock per year. At that rate, the current geographic distribution lasts 462 years.

![Social Rent completions collapsed from 57,000/yr in 1992 to 12,000/yr now](/assets/images/housing-04-supply-collapse.png)

And the new investment that was supposed to shift that distribution goes to the wrong places:

![Government-grant Social Rent completions per 100k: London vs North East 2009-2024](/assets/images/housing-08-grant-investment.png)

Over the last 15 years, London received **2.4 times more government-funded Social Rent completions per person** than the North East. In 2017, the North East received zero. London's advantage is partly structural: the Greater London Authority runs a dedicated Mayor's Housing Programme with housing investment powers that no Northern region has any equivalent of.

---

## The employer angle

There is a less comfortable implication that is rarely stated.

If workers in central London can live at below-market rents because the state is bridging the gap, their employers don't have to pay wages that reflect what London actually costs. Social housing in London functions, in economic terms, as a **labour cost subsidy to London businesses** — it expands the affordable labour supply, suppresses wages below what a genuine market would require, and makes central London more economically competitive than it would otherwise be. At national expense.

![Equivalent annual gross wage saving for employers by region](/assets/images/housing-03-employer-subsidy.png)

The equivalent annual gross wage saving to London employers is estimated at **£13.5 billion per year** — larger than the entire budget for the cancelled northern legs of HS2. If this were an explicit Treasury grant to London businesses, the political scrutiny would be intense. It operates invisibly because it runs through the housing market.

---

## This is not the whole picture of regional transfers

London almost certainly remains a net fiscal contributor to the rest of England. But this analysis sits alongside other large transfers that don't appear in standard regional accounts:

- **London Weighting**: central government pays NHS staff, teachers, civil servants, police, and fire workers a London supplement — roughly £1.5–2bn/yr from national budgets, compensating for housing costs that are themselves partly a policy choice
- **Infrastructure investment**: the Elizabeth Line cost ~£19bn; HS2 delivered the southern sections and cancelled the Manchester and Leeds legs
- **National institutional concentration**: the British Museum, National Gallery, V&A, and dozens of other nationally funded institutions are sited in London with economic multipliers that benefit London disproportionately

The margin between London-as-net-contributor and the rest is probably smaller than the headline regional accounts suggest — and at least one large, compounding, unscrutinised transfer flows *to* London rather than from it.

---

## Data and methodology

All data is from open government sources:

- **ONS Private Rental Market Statistics** (Oct 2022–Sep 2023) — median private rents by LA and bedroom size
- **RSH Statistical Data Return 2024–25** — average social rents for all registered providers
- **MHCLG Live Table 100** (March 2024) — dwelling stock by tenure and local authority
- **MHCLG Affordable Housing Supply open data** (1991–2025) — completions by tenure, LA, year, and funding type

The subsidy is calculated as (market rent − social rent) at the bedroom-size level for each LA, weighted by unit counts. The employer gross-up assumes a 28% effective marginal rate (basic-rate income tax + employee NI).

Full methodology, code, and data: **[github.com/Kali89/housing-subsidy-analysis](https://github.com/Kali89/housing-subsidy-analysis)**

*Data year caveat: ONS PRMS covers Oct 2022–Sep 2023; RSH SDR is March 2025. Private rents rose substantially over this period, so the market rent figures likely understate current levels — the subsidy figures are directionally correct but not a precise point-in-time estimate.*
