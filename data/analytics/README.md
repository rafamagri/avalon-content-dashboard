# Avalon Escapes — Analytics Data Folder

> Drop exported Instagram analytics CSV files here to unlock full metric-based scoring.
> The dashboard reads this folder automatically on load.
> No credentials required for the current local/static dashboard.

---

## Current State

The dashboard is **local and static** — it does not require any live connection, credentials, or API key.
All scoring and analysis is based on public data, processed JSON files, and rule-based logic.

When analytics CSVs are added to this folder, the dashboard unlocks:
- Full metric-based scoring (saves, reach, impressions, follower growth)
- Engagement rate calculations per post
- Format performance breakdown with real metrics
- Weekly performance trends

---

## How to Export Analytics from Instagram

1. Open Instagram app → tap your profile
2. Tap "Professional dashboard" (if on a business/creator account)
3. Tap "See all" → scroll to any metric → export
4. Or use Meta Business Suite → Insights → Export data

Save the CSV file into this folder with a name like: `avalon_2026_q2.csv`, `rafa_2025_full.csv`

---

## Expected CSV Format

### Minimum columns (Instagram Insights export)

| Column | Description |
|---|---|
| `date` | Publication date (YYYY-MM-DD) |
| `post_type` | Photo / Reel / Carousel |
| `description` | Caption or post title |
| `impressions` | Total impressions |
| `reach` | Unique accounts reached |
| `likes` | Like count |
| `comments` | Comment count |
| `saves` | Save count |
| `shares` | Share count |
| `video_views` | Views (Reels only) |
| `profile_visits` | Profile visits from this post |
| `follows` | New follows from this post |

### Extended columns (add manually for richer analysis)

| Column | Description |
|---|---|
| `destination` | Destination tag (Maldives, Colombia, Türkiye, etc.) |
| `content_pillar` | Avalon content pillar number (1–8) |
| `hook_type` | Question / Statement / List / Story |
| `reference_pattern` | Viral pattern used, if any |
| `notes` | Internal notes |

---

## Future Analytics Sources (planned, not yet connected)

The dashboard is structured to support these sources in the future.
**No live connections are active.** No credentials required now.

### 1. Instagram Analytics CSV Export — available now
Manual export from Instagram Insights or Meta Business Suite. Drop here.

### 2. Google Sheets — planned
Maintain a running sheet with post performance. Dashboard reads from a local export.

### 3. Windsor.ai — planned, not yet connected
Aggregates social media analytics across platforms (Instagram, TikTok, YouTube).
Future path: Windsor.ai → CSV export → this folder, OR Windsor.ai API with key in `secrets.toml`.
**Do not connect yet** — API key must never be committed to GitHub.

### 4. Meta Instagram Graph API — planned, not yet connected
Direct API access to Instagram Business account analytics in real-time.
Requires: Facebook Developer account + Instagram Business account + access token.
Access token goes in `.streamlit/secrets.toml` only (gitignored — never committed).
**Do not implement until production-ready.**

---

## Full Future Analytics Field Model

| Field | Source | Priority |
|---|---|---|
| `date` | Instagram | Required |
| `account` | Manual | Required (rafa / sofia / avalon) |
| `post_type` | Instagram | Required |
| `destination` | Manual / tagged | High |
| `content_pillar` | Manual | High |
| `hook` | Manual | High |
| `views` | Instagram (Reels) | High |
| `likes` | Instagram | Required |
| `comments` | Instagram | Required |
| `shares` | Instagram | High |
| `saves` | Instagram | High |
| `reach` | Instagram | High |
| `impressions` | Instagram | Medium |
| `follower_growth` | Instagram | Medium |
| `engagement_rate` | Calculated | High |
| `profile_visits` | Instagram | Medium |
| `reference_pattern_used` | Manual | Medium |
| `notes` | Manual | Low |

---

## Privacy Rules

- Only drop analytics from accounts Avalon owns (rafa / sofia / avalon)
- Never add competitor data, scraped data, or data from accounts not owned by Avalon
- Analytics CSVs are gitignored — they will never be committed to GitHub
- `.streamlit/secrets.toml` (for future API keys) is gitignored — never commit credentials
