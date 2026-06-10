# Avalon Escapes — Content Intelligence System

## Project purpose

This system collects public Instagram content from founder accounts, the Avalon brand account,
and reference creator accounts. It analyzes patterns in top-performing posts and generates
new content ideas and weekly plans for Avalon Escapes.

## Accounts

| ID | Handle | Role |
|---|---|---|
| rafa | @_rafamagri | Founder / personal travel-lifestyle |
| sofia | @sofiacollins311 | Co-founder / personal |
| avalon | @avalon.escapes | Brand account — primary output target |

## Brand context

Avalon Escapes is a luxury travel agency and bespoke escape design studio that curates
meaningful, high-end travel experiences around the world. The brand focuses on intentional
journeys, boutique stays, ocean adventures, island escapes, nature-based experiences, cultural
immersion, retreats, wellness travel, romantic getaways, once-in-a-lifetime adventures, and
tailor-made itineraries designed with care, elegance, and authenticity.
Current priority destinations: Maldives, Colombia, Brazil, Türkiye, Sri Lanka — and curated
global luxury travel beyond these.
Voice: premium, elegant, warm, personal, authentic, emotionally intelligent, experience-driven,
globally minded, ocean-inspired, boutique, curated. Not generic, not mass-market, not corporate.

## Privacy rules (always enforce)

- Only public data. Never attempt to access private accounts or data behind login.
- No DMs, private analytics, follower demographics, or anything not publicly visible.
- Always ask for explicit user confirmation before calling any Apify actor (credits cost money).
- Show estimated cost before every Apify run.

## Data rules

- Raw Apify output goes to `data/raw/{account_id}/` — never modify these files.
- Processed data goes to `data/processed/` — always include an `account_id` field per record.
- Never mix account data without labeling the source.
- Analyze each account separately first, then cross-account.

## Key config

`config/profiles.json` — founder and brand account URLs, roles, and collection settings.
`config/reference_creators.json` — reference/inspiration creator accounts (separate).

## Content pillars

| # | Pillar | Focus |
|---|---|---|
| 1 | **Luxury Escapes** | Boutique hotels, private stays, romantic travel, elevated comfort, curated high-end experiences |
| 2 | **Ocean & Island Adventures** | Maldives, Sri Lanka, diving, freediving, marine life, boats, coastal destinations, island escapes, wildlife |
| 3 | **Latin America & Cultural Discovery** | Colombia, Brazil, local experiences, food, art, music, culture, hidden gems, meaningful encounters |
| 4 | **Türkiye & Crossroads Travel** | Boutique stays, cultural routes, coastal escapes, history, design, gastronomy, layered travel |
| 5 | **Nature & Transformation** | Retreats, wellness, mountains, jungles, deserts, slow travel, personal growth through travel |
| 6 | **Founder-Led Travel Storytelling** | Rafa and Sofia's real experiences, personal recommendations, behind-the-scenes, honest travel lessons |
| 7 | **Tailor-Made Journeys** | Custom itineraries, special occasions, honeymoon escapes, group trips, private tours, multi-destination planning |
| 8 | **Viral Travel Inspiration** | Trend-based travel content adapted into Avalon's voice — without making the brand feel generic or copied |

## Viral Influencer Trend Reference Group

**Conceptual name:** `viral_influencer_trend_reference_group`
**Physical folder/config key:** `viral_reference_group` (kept for stability — do not rename)

12 public creator accounts studied as ONE collective benchmark pool — NOT competitors.
Purpose: study viral influencer content, trend formats, and content structures that Avalon can
adapt or recreate. A lot of social media is trend-based — the goal is NOT to avoid replication
entirely. The goal is to understand what can be replicated safely and strategically.

Config: `config/reference_creators.json` → `viral_reference_group.accounts`
Raw data (per account): `data/raw/viral_reference_group/{username}/`
Processed (combined): `data/processed/viral_reference_group/group_posts.json`
Analysis output: `analysis/viral_reference_group/viral_pattern_library.md`

The group is ALWAYS analyzed as a single combined pool.
Analysis sections: A. Viral Pattern Library  B. Hook Bank  C. Reel Script Formulas
                   D. Caption Formulas  E. Visual Direction  F. Avalon Adaptation
                   G. Content Scoring System

**Relative performance scoring:** Each post gets a `relative_score` field — its engagement
signal (plays/views/comments) divided by that creator's own median. Score ≥ 2.0 = high
performing; ≥ 3.0 = viral within their content. This normalizes across different audience sizes.

**Format-adjusted scoring:** `format_adjusted_performance_score()` applies format-specific bonuses.
Reel: bonus for plays + deep comment engagement. Carousel: bonus for guide/list keywords + saveable
first-slide signals + slide count. Photo: bonus for emotional language + long caption.
**Public data limitation:** saves, shares, reach, and impressions are NEVER available from public
scraping. The dashboard never invents these values. Text-based proxies are used as a fallback.
Adding an Instagram analytics CSV to `data/analytics/` unlocks full metric-based scoring.

**New creators (added June 2026):**
- `moore_rachel` — travel, lifestyle & aspirational storytelling (avalon_fit_score: 80)
- `travelcroats` — PRIMARY CAROUSEL REFERENCE. Carousel formats, destination guides, saveable
  posts, itinerary carousels, first-slide hooks, save/share triggers. (avalon_fit_score: 85)

**Data isolation rule:** `_data_type: "viral_reference_group"` on every raw post record.
Never mixed with founder or brand account data.

**Three-tier classification for every pattern identified:**

| Tier | Name | Description |
|---|---|---|
| 1 | **Direct Trend Adaptation** | Format is already trend-based — recreate with Avalon footage, voice, destinations. (POV formats, "send this to" formats, transition trends, list Reels, travel reminder formats, invitation formats, keyword CTAs) |
| 2 | **Structural Replication** | Replicate the structure (hook formula, pacing, emotional arc, caption shape, CTA style) but not the exact words, footage, creator identity, or personal story. |
| 3 | **Inspiration Only** | Do NOT copy directly — too unique to the creator, too personal, or too close to their brand identity. Use only as directional inspiration. (Personal manifestos, signature phrases, private experience framing, unique editing identity) |

## Workflow scripts (full pipeline)

| Script | Purpose |
|---|---|
| `scripts/01_collect.py` | Collect founder + brand account posts |
| `scripts/02_process.py` | Normalize founder + brand data |
| `scripts/03_analyze.py` | Claude analysis for founder + brand accounts |
| `scripts/04_generate.py` | Generate ideas, scores, weekly plans |
| `scripts/05_collect_references.py` | Collect reference creator posts |
| `scripts/06_analyze_references.py` | Analyze reference creators + cross-reference synthesis |

## Analytics CSV

Drop exported Instagram analytics CSV files into `data/analytics/` when available.
See `data/analytics/README.md` for expected format.
