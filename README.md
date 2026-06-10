# Avalon Escapes — Content Intelligence System

A local content intelligence system for **Avalon Escapes** — a luxury travel agency and bespoke
escape design studio focused on intentional journeys, boutique stays, ocean adventures, island
escapes, cultural immersion, and curated global luxury travel.
Priority destinations: Maldives, Colombia, Brazil, Türkiye, Sri Lanka.

Founders: Rafa (@_rafamagri) and Sofia (@sofiacollins311).
Brand account: @avalon.escapes.

---

## Running the Dashboard

```bash
cd ~/avalon-apify-agent
python3 -m pip install -r requirements.txt
python3 -m streamlit run dashboard.py
```

The dashboard opens automatically in your browser at `http://localhost:8501`.

**Important:**
- The dashboard uses **local data only** — no scraping, no Apify calls, no credits used.
- It reads from `data/processed/`, `analysis/`, and `content_plans/`.
- If a file is missing, the dashboard shows a graceful placeholder instead of crashing.

---

## Dashboard Sections

| Section | What it shows |
|---|---|
| 📊 Overview | KPI cards, account breakdown, total engagement |
| 🌊 Viral Reference Group | Top viral posts, full pattern library, tier framework, **Creator Authority table** |
| 👥 Founder & Brand | Per-account analysis for Rafa, Sofia, and Avalon |
| 🏆 Top Performers | Sortable, filterable table across all accounts |
| 📈 Pattern Charts | Format, pillar, destination, hook, caption length, and duration vs. performance |
| 🎯 Content Simulator | Score a new post idea out of 100 + **Reference-Based Improvement** section |
| 📅 Weekly Content Plan | Reads Markdown plans from `content_plans/` |
| 📖 Playbook | Always/Never rules, optimal specs, top hook formulas by tier |
| 🔍 Data Quality | File status, what's available, what needs manual export |

### Content Simulator — Reference-Based Improvement

After scoring your idea, the simulator generates a full improvement plan sourced from the **Viral Influencer Trend Reference Group**:

1. **Matching viral patterns** — which of the 12 library patterns align with your idea
2. **Relevant creators** — which reference accounts are most useful for this type of content
3. **Avalon adaptation guide** — caption structure + visual direction
4. **What NOT to copy** — explicit safety warnings per pattern
5. **Improved version** — 5 stronger hooks, 1 Reel structure, 3 CTAs, 1 hashtag set, projected score

All suggestions are rule-based (no API required). They improve when you add more detail to the idea, hook, or caption fields.

---

## Project Structure

```
avalon-apify-agent/
├── dashboard.py                     # Streamlit dashboard (run this)
├── requirements.txt                 # streamlit, pandas, plotly
├── CLAUDE.md                        # Project instructions for Claude Code
├── config/
│   ├── profiles.json                # Founder + brand account settings
│   └── reference_creators.json     # Viral reference group (10 accounts)
├── data/
│   ├── raw/
│   │   ├── rafa/                    # Raw Apify output — never modify
│   │   ├── sofia/
│   │   ├── avalon/
│   │   └── viral_reference_group/  # Per-account raw data
│   ├── processed/
│   │   ├── rafa_posts.json
│   │   ├── sofia_posts.json
│   │   ├── avalon_posts.json
│   │   └── viral_reference_group/
│   │       └── group_posts.json    # 250-post combined dataset with relative_score
│   └── analytics/                  # Drop Instagram analytics CSVs here
├── analysis/
│   ├── rafa_analysis.md
│   ├── sofia_analysis.md
│   ├── avalon_analysis.md
│   ├── cross_account_report.md
│   └── viral_reference_group/
│       ├── README.md
│       └── viral_pattern_library.md  # Full A–G pattern report
├── content_plans/                   # Weekly Markdown plans go here
└── scripts/
    ├── 01_collect.py                # Collect founder + brand posts
    ├── 02_process.py                # Normalize founder + brand data
    ├── 03_analyze.py                # Claude analysis per account
    ├── 04_generate.py               # Generate weekly content plans
    ├── 05_collect_references.py     # Collect viral reference group posts
    └── 06_analyze_references.py     # Analyze reference group + build pattern library
```

---

## Running the Full Pipeline (data collection)

> **These scripts use Apify credits. Always read the cost estimate before confirming.**

```bash
# Collect founder + brand posts (Rafa, Sofia, Avalon)
python3 scripts/01_collect.py

# Normalize collected data
python3 scripts/02_process.py

# Generate per-account analysis with Claude
python3 scripts/03_analyze.py

# Generate weekly content plans
python3 scripts/04_generate.py

# Collect viral reference group posts (10 accounts)
python3 scripts/05_collect_references.py

# Build group dataset + generate viral pattern library
python3 scripts/06_analyze_references.py
```

---

## Viral Influencer Trend Reference Group

**Conceptual name:** `viral_influencer_trend_reference_group`
**Physical folder:** `viral_reference_group/` (kept stable — do not rename)

10 public creator accounts studied as **one combined benchmark pool** — not competitors.
Purpose: identify trend formats, viral structures, and content patterns that Avalon can adapt.

Accounts: @noareserrunt · @gavinheeks · @jackrosen6 · @colemangeiger · @colinduthie ·
@jords.media · @lilifabienne_ · @monicaroams · @seanhammonds · @viluagency

**Three-tier classification:**
- **Tier 1 — Direct Trend Adaptation:** Recreate directly with Avalon footage and voice
- **Tier 2 — Structural Replication:** Use the structure, not the exact words or personal story
- **Tier 3 — Inspiration Only:** Too creator-specific to copy — use only for directional ideas

**Ethics rule:** Avalon can replicate trend formats and content structures, but must never copy exact captions, scripts, footage, personal stories, signature phrases, or creator identity. All ideas must be transformed into Avalon's own voice, footage, destinations, and brand angle.

Pattern library: `analysis/viral_reference_group/viral_pattern_library.md`

### Adding follower counts

Open `config/reference_creators.json` and update each creator's `"follower_count"` field:
```json
{ "instagram_username": "gavinheeks", "follower_count": 450000, ... }
```
The Creator Authority table in the dashboard will update on next reload.

### Adding new reference creators

Add new creators to `config/new_reference_creators_to_add.json`:
```json
[
  {
    "id": "newcreator",
    "instagram_username": "newcreator",
    "instagram_url": "https://www.instagram.com/newcreator/",
    "follower_count": null,
    "niche": "Ocean travel",
    "why_relevant_to_avalon": "...",
    "avalon_fit_score": 80,
    "notes": ""
  }
]
```
When ready, move the entry into `config/reference_creators.json` under `viral_reference_group.accounts` and run:
```bash
python3 scripts/05_collect_references.py   # collect their posts
python3 scripts/06_analyze_references.py   # rebuild group dataset + pattern library
```

### Influence weighting

Reference Strength Score (0–100) balances four signals:
- **Viral performance (35%)** — posts that outperform that creator's own median matter most
- **Follower authority (25%)** — log-normalized follower count (larger = more weight, but not dominant)
- **Avalon fit (25%)** — static rating in config of how well this creator's style maps to Avalon
- **Replicability (15%)** — share of posts estimated as Tier 1 or Tier 2 (safe to adapt)

Example: small creator + very viral post = strong pattern. Large creator + average post = useful but not automatically top-ranked.

---

## Adding Instagram Analytics CSVs

Drop exported CSV files into `data/analytics/` to improve scoring accuracy.
Once added, the dashboard will show saves, reach, profile visits, and follows gained.

See `data/analytics/README.md` for the expected format.

---

## Privacy Rules

- Only public data. Never attempt to access private accounts or anything behind login.
- No DMs, private analytics, follower demographics, or anything not publicly visible.
- Always confirm before running any Apify actor (credits cost money).
- The dashboard never calls external services — it is fully local.
