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

## Professional Frameworks Layer

**GOAL Prompt Framework:** `reference_frameworks/prompting/GOAL_prompt_framework.md`
The official prompt structure for all AI content tasks: G (Goal) + O (Objective) + A (Assets) + L (Layout).
Always use GOAL structure for significant AI requests. Assets block should include Avalon context.

**Advanced Prompt Methods:** `reference_frameworks/prompting/advanced_prompt_methods.md`
5 techniques: Devil's Advocate · Client Lens · Consult the Greats · Back 2 The Future · Style Clone.
Apply as a wrapper around any GOAL prompt for deeper or more critical output.

**Avalon Context Builder:** `reference_frameworks/prompting/avalon_context_builder.md`
Master context document — use as the Assets (A) block in all AI prompts.
Keep updated when business state, destinations, or priorities change.

**Marketing Skills Layer:** `reference_frameworks/marketing_skills_summary.md`
Source repo cloned locally to `reference_frameworks/marketing_skills/` — **NOT committed to GitHub** (in .gitignore).
Key skills: Copywriting (AIDA/PAS), Content Strategy, Marketing Psychology (JTBD), CRO (keyword CTAs), Social Media.

**AI-Ready Business 5 P's:** `reference_frameworks/ai_ready_business/avalon_5ps.md`
People → Process → Platforms → Proprietary Data → Products & Services.
Progression: Knowledge on demand → Collaborative co-worker → Autonomous workflow execution.

**Dashboard — Frameworks page:** 🧠 Frameworks & Prompt Builder
- Tab 1: GOAL Prompt Builder (form → generates structured AI prompt)
- Tab 2: Prompt Templates (10 pre-built prompts for common tasks)
- Tab 3: Professional Skill Lens (content type → marketing skill + GOAL diagnosis)
- Tab 4: Avalon Context Builder (viewer for avalon_context_builder.md)

**Dashboard — Content Simulator:** Section 7 "Professional Marketing Lens"
- Most relevant marketing skill + key frameworks
- GOAL diagnosis (G/O/A/L scored as Strong/Developing/Needs work)
- Generate GOAL prompt from simulator inputs

**Dashboard — Weekly Calendar:** 🎯 GOAL prompt expander on every day card
- Generates structured GOAL prompt from day's fields (idea, hook, format, destination, etc.)
- Supports all 5 advanced prompt modes

**Public repo safety rule:** Do NOT commit `reference_frameworks/marketing_skills/` or any secrets,
tokens, raw private data, or external repos to GitHub. The repo is public for Streamlit deployment.

## Workflow scripts (full pipeline)

| Script | Purpose |
|---|---|
| `scripts/01_collect.py` | Collect founder + brand account posts |
| `scripts/02_process.py` | Normalize founder + brand data |
| `scripts/03_analyze.py` | Claude analysis for founder + brand accounts |
| `scripts/04_generate.py` | Generate ideas, scores, weekly plans |
| `scripts/05_collect_references.py` | Collect reference creator posts |
| `scripts/06_analyze_references.py` | Analyze reference creators + cross-reference synthesis |

## Brand System (source of truth for all content generation)

`brand_system/` contains the official brand reference files — committed to GitHub as safe markdown summaries.
The original brand manual PDF and all logo/design files are in `brand_assets/private/` (gitignored, never committed).

| File | Purpose | Use when |
|---|---|---|
| `brand_system/avalon_brand_summary.md` | Brand personality, voice, promise, founder roles | Any content generation or caption writing |
| `brand_system/avalon_design_system.md` | Color palette (#0F2649, #213A3E, #265196, #FFFFFF), typography (Amore Christmas + Montserrat), iconography | Visual direction, slide design, color references |
| `brand_system/avalon_logo_rules.md` | Logo anatomy, proportions, 4 color variants, incorrect uses | Any logo placement or branding decision |
| `brand_system/avalon_carousel_style_guide.md` | Carousel structure, first-slide rules, save/share/comment triggers, caption format, carousel types | Carousel planning, slide copy, first-slide hooks |
| `brand_system/avalon_asset_index_template.md` | Living index of all brand assets (logos, photos, templates) | Finding or tracking brand asset files |
| `brand_system/avalon_brand_context_for_ai.md` | Complete AI-ready brand context for content generation | Use as the Assets (A) block in GOAL prompts; Content Simulator; caption rewriting; weekly calendar brief |

**Dashboard brand integration — apply brand_system/ across all sections:**
- **Content Simulator:** brand voice rules from `avalon_brand_summary.md` apply to hook/caption scoring and improvement
- **Content Simulator (improvement):** visual direction from `avalon_design_system.md` informs carousel/Reel recommendations
- **Weekly Calendar:** carousel format hints reference `avalon_carousel_style_guide.md` (save triggers, first-slide rules)
- **GOAL prompt builder:** `avalon_brand_context_for_ai.md` is the default Assets (A) block
- **Caption rewriting / brand voice tasks:** always apply the voice guardrails from `avalon_brand_summary.md`
- **Carousel generation:** structure and first-slide design must follow `avalon_carousel_style_guide.md`

**Key brand facts for quick reference:**
- Primary bg color: `#0F2649` (Deep Navy)
- Brand fonts: Amore Christmas (AVALON wordmark) + Montserrat Medium/Bold/Black (everything else)
- Logo type: Imagotype — butterfly+compass symbol + "AVALON - ESCAPES -" wordmark (always together unless isotype-only context)
- Voice test: "Does this sound like Rafa or Sofia wrote it?" + "Does this feel like it costs money?"
- Save test for carousels: "Would I save this if someone else posted it?"

## Analytics CSV

Drop exported Instagram analytics CSV files into `data/analytics/` when available.
See `data/analytics/README.md` for expected format.
