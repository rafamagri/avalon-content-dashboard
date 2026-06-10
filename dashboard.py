"""
Avalon Escapes — Content Intelligence Dashboard
Uses only local data. No Apify. No scraping. No credits.
Run: python3 -m streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
import statistics
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be the first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Avalon Escapes — Content Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DATA_PROCESSED  = ROOT / "data" / "processed"
ANALYSIS_DIR    = ROOT / "analysis"
CONTENT_PLANS   = ROOT / "content_plans"
PATTERN_LIB     = ANALYSIS_DIR / "viral_reference_group" / "viral_pattern_library.md"
REF_GROUP_POSTS = DATA_PROCESSED / "viral_reference_group" / "group_posts.json"

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS  (layered over the dark base theme from .streamlit/config.toml)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    color: #7ea8c9 !important;
    font-size: 0.72rem !important;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-size: 1.6rem !important;
    font-weight: 700;
}
[data-testid="stSidebar"] { border-right: 1px solid #1e3a5f; }
.stDataFrame  { border: 1px solid #1e3a5f; border-radius: 6px; }
.stExpander   { border: 1px solid #1e3a5f !important; border-radius: 6px !important; }
.ac { background:#111827; border:1px solid #1e3a5f; border-radius:8px; padding:1.1rem 1.4rem; margin-bottom:.75rem; }
.ac h4 { color:#00b4d8; margin:0 0 .4rem 0; font-size:.95rem; font-weight:600; }
.ac p  { color:#94a3b8; margin:0; font-size:.88rem; line-height:1.65; }
.section-rule { border:none; border-top:1px solid #1e3a5f; margin:1.5rem 0; }
.status-bar { background:#0d1f0d; border:1px solid #1e4d1e; border-radius:6px;
              padding:.6rem 1rem; color:#4ade80; font-size:.82rem; margin-bottom:1.25rem; }
.t1 { background:#0d3040; color:#00b4d8; padding:2px 8px; border-radius:4px; font-size:.75rem; font-weight:700; white-space:nowrap; }
.t2 { background:#312a0d; color:#c9a84c; padding:2px 8px; border-radius:4px; font-size:.75rem; font-weight:700; white-space:nowrap; }
.t3 { background:#1a1a2e; color:#a78bfa; padding:2px 8px; border-radius:4px; font-size:.75rem; font-weight:700; white-space:nowrap; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_TMPL = "plotly_dark"
OCEAN_PAL   = ["#00b4d8","#48cae4","#0077b6","#c9a84c","#90e0ef","#7ea8c9","#4ade80","#a78bfa"]

FOUNDER_META = {
    "rafa":   {"label":"Rafa",          "username":"@_rafamagri",     "role":"Founder / Personal",    "color":"#00b4d8"},
    "sofia":  {"label":"Sofia",         "username":"@sofiacollins311", "role":"Co-founder / Personal", "color":"#c9a84c"},
    "avalon": {"label":"Avalon Escapes","username":"@avalon.escapes",  "role":"Brand Account",         "color":"#4ade80"},
}

# ── Layer 1: Content pillars — what TYPE of content is it? ──────────────────
CONTENT_PILLARS = {
    "Luxury Escapes": [
        "luxury","boutique","hotel","resort","suite","villa",
        "premium","curated","exclusive","escape","escapes",
        "romantic","elegant","private","high-end","bespoke",
        "tailor-made","tailormade","luxury travel","hidden gem",
    ],
    "Ocean & Island Adventures": [
        "ocean","sea","dive","diving","shark","coral",
        "underwater","marine","freedive","free dive","snorkel",
        "whale","turtle","island","coastal","boat","beach",
        "lagoon","reef","manta","dolphin","sailing","yacht","blue water",
    ],
    "Culture & Discovery": [
        "local","food","art","music","culture","cultura",
        "hidden","authentic","community","tradition",
        "gastronomy","street food","coffee","dance",
        "history","heritage","architecture","design",
        "market","bazaar","old town","local experience",
    ],
    "Adventure & Exploration": [
        "adventure","explore","expedition","wild","hike",
        "trek","climb","summit","road trip","off road",
        "remote","trail","journey","discover","discovered",
        "unknown","get lost","once in a lifetime",
    ],
    "Retreat & Wellness": [
        "retreat","yoga","meditation","wellness","mindful",
        "mindfulness","peace","stillness","healing","reset",
        "slow travel","disconnect","reconnect","breath",
        "body","soul","spa","sanctuary","calm",
    ],
    "Nature & Wildlife": [
        "wildlife","animal","bird","nature","forest","jungle",
        "mountain","desert","waterfall","river","lake",
        "safari","rainforest","spider","cobweb","monkey",
        "tropical","sunset","sunrise","landscape","wilderness",
    ],
    "Personal Transformation": [
        "changed","changed me","perspective","realized",
        "learned","growth","transformed","transformation",
        "became","healed","found myself","lost myself",
        "alive","clarity","purpose","meaning","shifted",
        "new version","life changed",
    ],
    "Emotional Travel": [
        "feel","feeling","alive","connection","meaning",
        "home","belonging","freedom","soul","heart",
        "nostalgia","wonder","awe","peace","magic",
        "unreal","dream","grateful","memory","moment",
        "human","hope","beautiful",
    ],
    "Travel Philosophy": [
        "society","no one tells","they told","worth it",
        "why travel","the world","unknown","comfort zone",
        "live more","life is short","reminder","what if",
        "you realize","the more i","travel teaches",
        "perspective","freedom","belong everywhere","belonging",
    ],
    "Destination Guide": [
        "guide","tips","must-see","must see","recommended",
        "recommendation","itinerary","where to","how to",
        "things to do","places to visit","best time",
        "travel guide","save this","list","top","hidden gems",
        "before you go","what to know",
    ],
    "Tailor-Made Journeys": [
        "tailor","tailor-made","bespoke","custom","private tour",
        "honeymoon","special occasion","group trip",
        "multi-destination","how to plan","planned for you",
        "curated itinerary","custom itinerary","personalized",
        "designed for you","proposal","anniversary","birthday trip",
    ],
    "Founder Story": [
        "we built","our agency","avalon was","our story",
        "rafa","sofia","two founders","behind the scenes",
        "we started","why we created","as founders",
        "our clients","we believe","we learned","we planned",
        "we experienced","avalon escapes",
    ],
    "Viral Travel Inspiration": [
        "send this","send this to","pov","travel reminder",
        "trend","this is your sign","you need to",
        "romanticize","main character","bucket list",
        "save this","share this","tag someone",
        "the kind of trip","imagine waking up","places that feel",
        "things i wish","unpopular opinion","nobody talks about",
    ],
}

# ── Layer 2: Destination/package — WHICH Avalon destination does it support? ─
DESTINATION_PACKAGES = {
    "Maldives": [
        "maldives","fuvahmulah","male","malé","atoll",
        "lagoon","shark","tiger shark","reef","manta",
        "dive","diving","freedive","snorkel","island",
        "overwater","marine life","blue water",
    ],
    "Colombia": [
        "colombia","cartagena","providencia","medellin",
        "medellín","bogota","bogotá","santa marta",
        "tayrona","guajira","caribbean","coffee region",
        "eje cafetero","barichara","palomino","isla fuerte",
        "rosario islands","islas del rosario",
    ],
    "Brazil": [
        "brazil","brasil","rio","rio de janeiro","bahia",
        "salvador","trancoso","fernando de noronha",
        "amazonia","amazon","lençóis","lencois",
        "chapada","jericoacoara","florianopolis",
        "paraty","ilha grande","pantanal","buzios","búzios",
    ],
    "Türkiye": [
        "turkey","türkiye","turkiye","istanbul",
        "cappadocia","bodrum","antalya","aegean",
        "mediterranean","bosphorus","turkish","bazaar",
        "hammam","galata","sultanahmet","turquoise coast",
        "pamukkale","ottoman","mosque","hot air balloon",
        "cave hotel","goreme","göreme",
    ],
    "Sri Lanka": [
        "sri lanka","srilanka","ceylon","colombo",
        "mirissa","ella","galle","sigiriya","kandy",
        "yala","udawalawe","arugam bay","surf",
        "tea country","train","wildlife","safari",
        "leopard","elephant","beach","wellness","retreat",
    ],
    "Global / Curated Escapes": [
        "global","world","international","multi-destination",
        "island escape","hidden gem","boutique escape",
        "custom trip","bespoke journey","private tour",
        "curated escape","tailor-made",
    ],
}
DESTINATION_DEFAULT = "Global / Curated Escapes"

HOOK_KW = {
    "Curiosity Gap":      ["that's what they","…","you won't believe","wait for it","at least"],
    "Emotional Reframe":  ["society","no one tells you","they told you","what no one says","the truth about"],
    "Love Declaration":   ["has my heart","i love","this place will","to know","to see"],
    "Expectation Flip":   ["exceeded every","completely changed","surprised me","wasn't expecting","nothing like"],
    "Personal Confession":["i never thought","i never imagined","i couldn't believe","i was nervous"],
    "Society Challenge":  ["society would say","society doesn't","we spend our whole lives"],
    "List Hook":          ["5 things","10 things","here are","things we","reasons why"],
    "Invitation":         ["join us","come with us","who wants to join","we're going","you can be there"],
    "Destination Reveal": ["who knew this was","still can't believe","didn't know this was"],
    "POV / Scenario":     ["pov:","as a traveller","imagine waking","picture this"],
}

GENERIC = ["breathtaking","unforgettable","amazing experience","incredible journey",
           "stunning views","once in a lifetime","hidden gem","paradise",
           "beautiful destination","gorgeous","spectacular views"]

AVALON_TERMS = ["ocean","dive","shark","maldives","fuvahmulah","colombia","brazil","brasil",
                "turkey","turkiye","türkiye","sri lanka","retreat","boutique","luxury",
                "rafa","sofia","avalon","curated","escapes","authentic","premium","elegant","warm"]

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING  (graceful — never crashes on missing files)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def safe_load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def safe_load_markdown(path):
    try:
        return Path(path).read_text()
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def load_founder_posts(account_id):
    path = DATA_PROCESSED / f"{account_id}_posts.json"
    raw = safe_load_json(path)
    if not raw:
        return []
    posts = raw.get("posts", [])
    meta = FOUNDER_META.get(account_id, {})
    normalized = []
    for p in posts:
        likes = p.get("likes_count", 0)
        if likes == -1:
            likes = None
        normalized.append({
            "account_id":    account_id,
            "group":         "founder_brand",
            "label":         meta.get("label", account_id),
            "username":      meta.get("username", ""),
            "post_id":       p.get("post_id"),
            "post_url":      p.get("post_url"),
            "date":          (p.get("timestamp") or "")[:10],
            "type":          p.get("type") or "Unknown",
            "product_type":  p.get("product_type") or "unknown",
            "caption":       (p.get("caption") or "").strip(),
            "hashtags":      p.get("hashtags", []),
            "likes":         likes,
            "comments":      p.get("comments_count"),
            "video_views":   p.get("video_view_count"),
            "video_plays":   p.get("video_play_count"),
            "duration_sec":  p.get("video_duration_sec"),
            "location":      p.get("location_name"),
            "relative_score": None,  # computed below
        })
    # compute relative_score for this account
    signals = [_engagement(p) for p in normalized if _engagement(p) > 0]
    median  = statistics.median(signals) if signals else 0
    for p in normalized:
        sig = _engagement(p)
        p["relative_score"] = round(sig / median, 2) if median > 0 and sig > 0 else None
    return normalized

@st.cache_data(show_spinner=False)
def load_reference_posts():
    raw = safe_load_json(REF_GROUP_POSTS)
    if not raw:
        return []
    posts = []
    for p in raw.get("posts", []):
        likes = p.get("likes", 0)
        if likes == -1:
            likes = None
        posts.append({
            "account_id":    p.get("username", ""),
            "group":         "viral_reference_group",
            "label":         f"@{p.get('username','')}",
            "username":      f"@{p.get('username','')}",
            "post_id":       p.get("post_id"),
            "post_url":      p.get("post_url"),
            "date":          p.get("date",""),
            "type":          p.get("type") or "Unknown",
            "product_type":  p.get("product_type") or "unknown",
            "caption":       (p.get("caption") or "").strip(),
            "hashtags":      p.get("hashtags", []),
            "likes":         likes,
            "comments":      p.get("comments"),
            "video_views":   p.get("video_views"),
            "video_plays":   p.get("video_plays"),
            "duration_sec":  p.get("video_duration_sec"),
            "location":      p.get("location"),
            "relative_score": p.get("relative_score"),
        })
    return posts

def _engagement(post):
    for key in ("video_plays","video_views","comments","likes"):
        v = post.get(key)
        if v and v > 0:
            return float(v)
    return 0.0

@st.cache_data(show_spinner=False)
def all_posts():
    result = []
    for aid in ("rafa","sofia","avalon"):
        result.extend(load_founder_posts(aid))
    result.extend(load_reference_posts())
    return result

# ─────────────────────────────────────────────────────────────────────────────
# INFERENCE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def infer_pillar(caption: str) -> str:
    """Layer 1 — content type / pillar."""
    if not caption:
        return "General"
    low = caption.lower()
    for pillar, keywords in CONTENT_PILLARS.items():
        if any(kw in low for kw in keywords):
            return pillar
    return "General"

def infer_destination(caption: str) -> str:
    """Layer 2 — which Avalon destination/package does the content support."""
    if not caption:
        return DESTINATION_DEFAULT
    low = caption.lower()
    for dest, keywords in DESTINATION_PACKAGES.items():
        if dest == DESTINATION_DEFAULT:
            continue  # checked last as fallback
        if any(kw in low for kw in keywords):
            return dest
    return DESTINATION_DEFAULT

def infer_hook_type(caption: str) -> str:
    if not caption:
        return "Unknown"
    first = caption.split("\n")[0].lower()
    for htype, kws in HOOK_KW.items():
        for kw in kws:
            if re.search(kw, first):
                return htype
    if len(first) < 60:
        return "Short Confident Hook"
    return "Narrative / Essay"

def infer_tier(post: dict) -> str:
    """Estimate adaptation tier. Labelled 'Estimated' in the UI."""
    caption = (post.get("caption") or "").lower()
    first   = caption.split("\n")[0] if caption else ""
    # Likely Tier 3: deeply personal philosophical manifestos
    if any(p in first for p in ["society doesn't kill", "that's what they call"]):
        return "Tier 3 (est.)"
    if len(caption) > 800 and any(p in caption for p in ["i never thought","society would say","what no one tells"]):
        return "Tier 3 (est.)"
    # Likely Tier 1: short trend formats
    if any(p in caption for p in ["dm me the word","comment '","comment \"","join us","dm me '"]):
        return "Tier 1 (est.)"
    if len(caption) < 80:
        return "Tier 1 (est.)"
    # Default: structural replication
    return "Tier 2 (est.)"

def truncate(text, n=90):
    if not text:
        return ""
    return text[:n] + "…" if len(text) > n else text

def fmt_number(n):
    if n is None:
        return "—"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))

def fmt_score(s):
    if s is None:
        return "—"
    return f"{s:.1f}×"

def duration_bucket(sec):
    if sec is None:
        return "Unknown"
    if sec < 15:
        return "< 15s"
    if sec < 30:
        return "15–30s"
    if sec < 45:
        return "30–45s"
    if sec < 60:
        return "45–60s"
    return "60s+"

def posts_to_df(posts):
    if not posts:
        return pd.DataFrame()
    rows = []
    for p in posts:
        rows.append({
            "Account":       p.get("label",""),
            "Group":         p.get("group",""),
            "Date":          p.get("date",""),
            "Type":          p.get("product_type","").capitalize(),
            "Caption":       truncate(p.get("caption",""), 90),
            "Likes":         p.get("likes"),
            "Comments":      p.get("comments"),
            "Plays":         p.get("video_plays"),
            "Views":         p.get("video_views"),
            "Relative Score":p.get("relative_score"),
            "Duration (s)":  p.get("duration_sec"),
            "Pillar":        infer_pillar(p.get("caption","")),
            "Destination":   infer_destination(p.get("caption","")),
            "Hook Type":     infer_hook_type(p.get("caption","")),
            "Tier (est.)":   infer_tier(p),
            "URL":           p.get("post_url",""),
        })
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT SCORING  (rule-based; no API required)
# Future: replace score functions with Claude API calls for richer feedback
# ─────────────────────────────────────────────────────────────────────────────
def score_hook(hook: str, idea: str) -> tuple[int, str]:
    """Max 20 pts. Evaluates first-line hook strength."""
    text = (hook or idea or "").strip()
    first = text.split("\n")[0] if text else ""
    score, notes = 0, []
    # length — short confident hooks score well
    if 0 < len(first) <= 60:
        score += 8; notes.append("Concise first line ✓")
    elif len(first) <= 100:
        score += 4
    # curiosity / tension signals
    tension = ["no one tells","never thought","couldn't believe","that's what","they told","society","nothing like","exceeded"]
    if any(t in first.lower() for t in tension):
        score += 6; notes.append("Strong tension signal ✓")
    elif first.endswith("…") or first.endswith("..."):
        score += 4; notes.append("Curiosity gap ✓")
    # generic openers penalty
    bad = ["we love","check out","beautiful","amazing","incredible","we are so"]
    if any(b in first.lower() for b in bad):
        score = max(0, score - 8); notes.append("Generic opener — rewrite ✗")
    # bonus: hook provided separately
    if hook and len(hook) > 5:
        score = min(20, score + 4); notes.append("Dedicated hook provided ✓")
    return min(20, score), "; ".join(notes) if notes else "Weak hook"

def score_specificity(caption: str, destination: str) -> tuple[int, str]:
    """Max 15 pts. Rewards specific details, penalises generic phrases."""
    text = (caption or "").lower()
    score, notes = 0, []
    if destination and len(destination) > 2:
        score += 5; notes.append(f"Destination mentioned ({destination}) ✓")
    # look for specific sensory or numerical details
    if re.search(r'\d+', text):
        score += 3; notes.append("Contains numbers/specifics ✓")
    if any(t in text for t in AVALON_TERMS):
        score += 4; notes.append("Avalon-relevant specifics ✓")
    # penalise each generic phrase
    hits = [g for g in GENERIC if g in text]
    if hits:
        penalty = min(score, len(hits) * 4)
        score  -= penalty
        notes.append(f"Generic phrases found: {', '.join(hits[:3])} ✗")
    return max(0, min(15, score)), "; ".join(notes) if notes else "Add specific details"

def score_emotional_arc(caption: str, idea: str) -> tuple[int, str]:
    """Max 15 pts. Rewards tension → shift → insight structure."""
    text = (caption or idea or "")
    score, notes = 0, []
    if len(text) > 200:
        score += 5; notes.append("Sufficient length ✓")
    elif len(text) > 80:
        score += 2
    arc_words = ["realized","changed","never thought","unexpected","surprised","discovered","transformed","but then","and yet","turned out","however"]
    hits = [w for w in arc_words if w in text.lower()]
    if len(hits) >= 2:
        score += 7; notes.append("Clear emotional arc ✓")
    elif len(hits) == 1:
        score += 3; notes.append("Some arc language ✓")
    # ending insight
    if any(e in text.lower() for e in ["that's what","that is what","maybe that","this is why","the lesson","what stays"]):
        score += 3; notes.append("Universal insight at end ✓")
    return min(15, score), "; ".join(notes) if notes else "Needs clearer arc (tension → change → insight)"

def score_brand_fit(caption: str, idea: str, emotion: str) -> tuple[int, str]:
    """Max 15 pts. Rewards premium, warm, authentic Avalon voice."""
    text  = " ".join([caption or "", idea or "", emotion or ""]).lower()
    score, notes = 0, []
    term_hits = [t for t in AVALON_TERMS if t in text]
    score += min(10, len(term_hits) * 2)
    if term_hits:
        notes.append(f"Brand terms: {', '.join(term_hits[:4])} ✓")
    corporate = ["agency services","our team offers","contact us today","click the link in bio to learn more","book now to secure"]
    if any(c in text for c in corporate):
        score = max(0, score - 8); notes.append("Corporate language detected ✗")
    generic_travel = ["travel agency","best travel","affordable","packages","deals","discounts"]
    if any(g in text for g in generic_travel):
        score = max(0, score - 5); notes.append("Generic travel agency tone ✗")
    if score >= 8:
        notes.append("Sounds like Avalon ✓")
    return min(15, score), "; ".join(notes) if notes else "Add Avalon-specific voice and destination language"

def score_shareability(caption: str, idea: str) -> tuple[int, str]:
    """Max 10 pts. Rewards universal insights and save-worthy content."""
    text  = (caption or idea or "").lower()
    score, notes = 0, []
    universal = ["everyone","we all","you've felt","most people","no one tells","they don't tell","what no one","maybe that","that's why"]
    if any(u in text for u in universal):
        score += 5; notes.append("Universal insight ✓")
    surprising = ["no one tells","didn't expect","surprised","unexpected","actually","turns out","changed everything"]
    if any(s in text for s in surprising):
        score += 5; notes.append("Surprising angle ✓")
    return min(10, score), "; ".join(notes) if notes else "Add a universal insight or surprising angle to trigger saves/shares"

def score_cta(cta: str) -> tuple[int, str]:
    """Max 10 pts. Rewards keyword CTAs and clear actions."""
    text = (cta or "").lower()
    if not cta or len(cta.strip()) < 3:
        return 0, "No CTA provided ✗"
    score, notes = 5, ["CTA present ✓"]
    keyword_cta = re.search(r'\b(dm|comment|send|type)\b.*\b(word|\'|\"|\w{3,})\b', text)
    if keyword_cta:
        score += 5; notes.append("Keyword CTA ✓")
    if "?" in text:
        score = min(10, score + 3); notes.append("Question CTA ✓")
    return min(10, score), "; ".join(notes)

def score_adaptation(tier: str) -> tuple[int, str]:
    """Max 10 pts. Rewards appropriate tier use."""
    tier_l = tier.lower()
    if "tier 1" in tier_l or "direct" in tier_l:
        return 10, "Tier 1 — safe to recreate directly ✓"
    if "original" in tier_l:
        return 10, "Original Avalon concept ✓"
    if "tier 2" in tier_l or "structural" in tier_l:
        return 7, "Tier 2 — ensure structure is transformed into Avalon's own voice"
    if "tier 3" in tier_l or "inspiration" in tier_l:
        return 4, "Tier 3 — content must be genuinely original, not adapted from reference ✗"
    return 5, "Classify the adaptation tier for accurate scoring"

def score_format(fmt: str, caption: str) -> tuple[int, str]:
    """Max 5 pts. Checks format/content alignment."""
    fmt_l = (fmt or "").lower()
    cap   = (caption or "").lower()
    if "reel" in fmt_l and len(cap) > 50:
        return 5, "Reel + developed caption ✓"
    if "carousel" in fmt_l and any(n in cap for n in ["5 ","10 ","here are","tips","guide"]):
        return 5, "Carousel + list content ✓"
    if "photo" in fmt_l and len(cap) < 150:
        return 5, "Photo + concise caption ✓"
    return 3, "Format match — consider whether the format matches the content type"

def run_scoring(idea, destination, fmt, emotion, hook, caption, cta, tier):
    """Run all 8 scoring criteria. Returns dict of scores and notes."""
    s1, n1 = score_hook(hook, idea)
    s2, n2 = score_specificity(caption or idea, destination)
    s3, n3 = score_emotional_arc(caption, idea)
    s4, n4 = score_brand_fit(caption, idea, emotion)
    s5, n5 = score_shareability(caption, idea)
    s6, n6 = score_cta(cta)
    s7, n7 = score_adaptation(tier)
    s8, n8 = score_format(fmt, caption)
    total  = s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8
    if total >= 80:
        rec, rec_color = "✅ Post it", "#4ade80"
    elif total >= 60:
        rec, rec_color = "🔶 Refine before posting", "#facc15"
    elif total >= 40:
        rec, rec_color = "🔁 Rethink concept", "#fb923c"
    else:
        rec, rec_color = "❌ Skip / discard", "#f87171"
    return {
        "total": total, "recommendation": rec, "rec_color": rec_color,
        "scores": {
            "Hook Strength (20)":          (s1, n1),
            "Specificity (15)":            (s2, n2),
            "Emotional Arc (15)":          (s3, n3),
            "Brand Fit (15)":              (s4, n4),
            "Shareability (10)":           (s5, n5),
            "CTA Quality (10)":            (s6, n6),
            "Adaptation Integrity (10)":   (s7, n7),
            "Format Match (5)":            (s8, n8),
        }
    }

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────
PAGES = {
    "📊  Overview":                   "overview",
    "🌊  Viral Reference Group":      "viral",
    "👥  Founder & Brand":            "founders",
    "🏆  Top Performers":             "top",
    "📈  Pattern Charts":             "charts",
    "🎯  Content Simulator":          "simulator",
    "📅  Weekly Content Plan":        "plan",
    "📖  Playbook":                   "playbook",
    "🔍  Data Quality":               "data_quality",
}

with st.sidebar:
    st.markdown("### 🌊 Avalon Escapes")
    st.markdown("<small style='color:#64748b'>Content Intelligence</small>", unsafe_allow_html=True)
    st.markdown("---")
    page_label = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
    page = PAGES[page_label]
    st.markdown("---")
    st.markdown(
        "<div style='color:#374151;font-size:.75rem;line-height:1.6'>"
        "🔒 Local data only<br>"
        "⚡ No scraping<br>"
        "💳 No Apify credits<br>"
        f"🕐 {datetime.now().strftime('%Y-%m-%d')}"
        "</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# SHARED HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.6rem;font-weight:700;color:#e2e8f0;margin-bottom:.1rem'>"
    "Avalon Escapes — Content Intelligence Dashboard</h1>"
    "<p style='color:#64748b;font-size:.85rem;margin-bottom:.5rem'>"
    "Founder content · Brand content · Viral Influencer Trend Reference Group</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='status-bar'>✅ Using local data only — no scraping, no Apify calls, no credits.</div>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
def page_overview():
    st.markdown("## 📊 Overview")

    rafa_posts   = load_founder_posts("rafa")
    sofia_posts  = load_founder_posts("sofia")
    avalon_posts = load_founder_posts("avalon")
    ref_posts    = load_reference_posts()
    founder_all  = rafa_posts + sofia_posts + avalon_posts
    all_p        = founder_all + ref_posts

    total        = len(all_p)
    founder_cnt  = len(founder_all)
    ref_cnt      = len(ref_posts)
    accounts_cnt = 3 + (10 if ref_posts else 0)

    # ── Engagement aggregates (only non-None values) ──────────────────────
    def _sum(posts, key):
        return sum(p.get(key) or 0 for p in posts if (p.get(key) or 0) > 0) or None

    total_likes    = _sum(all_p, "likes")
    total_comments = _sum(all_p, "comments")
    total_plays    = _sum(all_p, "video_plays")

    viral_posts  = [p for p in ref_posts if (p.get("relative_score") or 0) >= 3.0]
    high_posts   = [p for p in ref_posts if 2.0 <= (p.get("relative_score") or 0) < 3.0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Posts Analysed", fmt_number(total))
    c2.metric("Founder / Brand Posts", fmt_number(founder_cnt))
    c3.metric("Reference Group Posts", fmt_number(ref_cnt))
    c4.metric("Accounts Tracked", str(accounts_cnt))

    st.markdown("")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total Likes", fmt_number(total_likes) if total_likes else "Not available yet")
    c6.metric("Total Comments", fmt_number(total_comments) if total_comments else "Not available yet")
    c7.metric("Total Video Plays", fmt_number(total_plays) if total_plays else "Not available yet")
    c8.metric("Viral Reference Posts (≥3×)", str(len(viral_posts)))

    st.markdown("")
    c9, c10, c11, c12 = st.columns(4)
    c9.metric("High-Performing Ref. Posts (2–3×)", str(len(high_posts)))
    top_ref = max(ref_posts, key=lambda p: p.get("relative_score") or 0, default=None)
    c10.metric("Top Relative Score",   fmt_score(top_ref.get("relative_score") if top_ref else None))
    c11.metric("Avg Comments (founders)", fmt_number(
        round(statistics.mean([p.get("comments") or 0 for p in founder_all if p.get("comments")]), 1)
        if any(p.get("comments") for p in founder_all) else None
    ))
    c12.metric("Avg Engagement (saves/reach)", "Not available yet")

    st.markdown("---")

    # ── Account breakdown mini ──────────────────────────────────────────────
    st.markdown("### Account Groups at a Glance")
    col_f, col_r = st.columns([1, 1])

    with col_f:
        st.markdown("**Founder & Brand**")
        for aid, posts in [("rafa", rafa_posts), ("sofia", sofia_posts), ("avalon", avalon_posts)]:
            m = FOUNDER_META[aid]
            plays_total = sum(p.get("video_plays") or 0 for p in posts if (p.get("video_plays") or 0) > 0)
            st.markdown(
                f"<div class='ac'><h4>{m['label']} <small style='font-weight:400;color:#64748b'>{m['username']}</small></h4>"
                f"<p>{len(posts)} posts &nbsp;·&nbsp; {fmt_number(plays_total)} total plays</p></div>",
                unsafe_allow_html=True,
            )

    with col_r:
        st.markdown("**Viral Influencer Trend Reference Group**")
        if ref_posts:
            usernames = sorted(set(p["account_id"] for p in ref_posts))
            per_user  = {u: [p for p in ref_posts if p["account_id"] == u] for u in usernames}
            rows = []
            for u, ps in per_user.items():
                med = statistics.median([p.get("relative_score") or 0 for p in ps if p.get("relative_score")] or [0])
                rows.append({"Account": f"@{u}", "Posts": len(ps), "Median Score": f"{med:.1f}×"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Reference group data not found.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: VIRAL REFERENCE GROUP
# ─────────────────────────────────────────────────────────────────────────────
def page_viral_reference():
    st.markdown("## 🌊 Viral Influencer Trend Reference Group")
    st.markdown(
        "<div class='ac'><p>This is a combined benchmark group used to identify trend formats, "
        "viral structures, and content patterns that Avalon can adapt. These are not competitors — "
        "they are a collective reference pool studied for what is replicable, structurally adaptable, "
        "or for inspiration only.</p></div>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["📋 Top Viral Posts", "📚 Pattern Library", "🔢 Three-Tier Framework"])

    # ── Tab 1: Top Posts ───────────────────────────────────────────────────
    with tab1:
        ref_posts = load_reference_posts()
        if not ref_posts:
            st.warning("Reference group data not found at `data/processed/viral_reference_group/group_posts.json`.")
            return

        sorted_posts = sorted(ref_posts, key=lambda p: p.get("relative_score") or 0, reverse=True)
        rows = []
        for i, p in enumerate(sorted_posts[:60], 1):
            rows.append({
                "Rank":    i,
                "Account": p.get("label",""),
                "Hook":    truncate(p.get("caption",""), 80),
                "Type":    (p.get("product_type") or "").capitalize(),
                "Likes":   fmt_number(p.get("likes")),
                "Comments":fmt_number(p.get("comments")),
                "Plays":   fmt_number(p.get("video_plays")),
                "Score":   fmt_score(p.get("relative_score")),
                "Tier":    infer_tier(p),
                "URL":     p.get("post_url",""),
            })

        df = pd.DataFrame(rows)
        st.markdown(f"**Top {len(rows)} posts by relative score** (out of {len(ref_posts)} collected)")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("##### Tier Legend (Estimated)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<span class='t1'>Tier 1 (est.)</span> &nbsp;Direct Trend Adaptation — recreate with Avalon footage", unsafe_allow_html=True)
        with col2:
            st.markdown("<span class='t2'>Tier 2 (est.)</span> &nbsp;Structural Replication — use the structure, not the words", unsafe_allow_html=True)
        with col3:
            st.markdown("<span class='t3'>Tier 3 (est.)</span> &nbsp;Inspiration Only — too personal to copy directly", unsafe_allow_html=True)

    # ── Tab 2: Pattern Library ─────────────────────────────────────────────
    with tab2:
        md = safe_load_markdown(PATTERN_LIB)
        if not md:
            st.warning("Pattern library not found at `analysis/viral_reference_group/viral_pattern_library.md`.")
            st.info("Run `python3 scripts/06_analyze_references.py` to generate it.")
            return

        # Split into sections by ## headings
        sections = re.split(r'\n(?=## )', md)
        section_map = {}
        for sec in sections:
            header_match = re.match(r'## (.+)', sec)
            if header_match:
                section_map[header_match.group(1).strip()] = sec
            else:
                # preamble / intro content
                section_map["__intro__"] = sec

        for key, content in section_map.items():
            if key == "__intro__":
                st.markdown(content)
                continue
            # clean title for expander label
            label = re.sub(r'^#+\s*', '', key)
            with st.expander(f"**{label}**", expanded=False):
                # strip the ## heading line before rendering
                body = re.sub(r'^## .+\n', '', content, count=1)
                st.markdown(body)

    # ── Tab 3: Three-Tier Framework ────────────────────────────────────────
    with tab3:
        st.markdown("### The Three-Tier Replication Framework")
        st.markdown(
            "Social media content is often trend-based. The goal is not to avoid replication entirely — "
            "it is to understand what can be replicated **safely and strategically**."
        )
        st.markdown("")

        t1c, t2c, t3c = st.columns(3)

        with t1c:
            st.markdown(
                "<div class='ac'>"
                "<h4>🟦 Tier 1 — Direct Trend Adaptation</h4>"
                "<p>The format is already trend-based. Recreate it directly with Avalon's "
                "footage, destinations, voice, and angle. No transformation required.</p>"
                "<br><b style='color:#e2e8f0;font-size:.85rem'>Examples:</b>"
                "<ul style='color:#94a3b8;font-size:.83rem;margin-top:.4rem'>"
                "<li>POV formats</li><li>&ldquo;Send this to someone&rdquo; formats</li>"
                "<li>List-style Reels</li><li>Keyword / DM CTAs</li>"
                "<li>Invitation formats</li><li>Transition trends</li>"
                "<li>Flag + emotion declarations</li><li>Morning routine Reels</li>"
                "</ul></div>",
                unsafe_allow_html=True,
            )
        with t2c:
            st.markdown(
                "<div class='ac'>"
                "<h4>🟨 Tier 2 — Structural Replication</h4>"
                "<p>Replicate the structure — hook formula, emotional arc, pacing, caption shape — "
                "but not the exact words, footage, creator identity, or personal story.</p>"
                "<br><b style='color:#e2e8f0;font-size:.85rem'>Examples:</b>"
                "<ul style='color:#94a3b8;font-size:.83rem;margin-top:.4rem'>"
                "<li>Expectation-flip formula</li><li>Philosophical essay arc</li>"
                "<li>Curiosity-gap hook pattern</li><li>Milestone narrative structure</li>"
                "<li>Underrated destination reveal</li><li>Parallel stanza captions</li>"
                "</ul></div>",
                unsafe_allow_html=True,
            )
        with t3c:
            st.markdown(
                "<div class='ac'>"
                "<h4>🟪 Tier 3 — Inspiration Only</h4>"
                "<p>Do not copy directly. The content is too tied to a creator's personal identity, "
                "signature phrases, or private experiences. Use only for directional inspiration.</p>"
                "<br><b style='color:#e2e8f0;font-size:.85rem'>Examples:</b>"
                "<ul style='color:#94a3b8;font-size:.83rem;margin-top:.4rem'>"
                "<li>Personal manifestos</li><li>Signature phrases</li>"
                "<li>Deeply personal journey stories</li>"
                "<li>Private experience framing</li>"
                "<li>Unique editing identity</li>"
                "</ul></div>",
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: FOUNDER & BRAND
# ─────────────────────────────────────────────────────────────────────────────
def page_founder_brand():
    st.markdown("## 👥 Founder & Brand Analysis")

    tabs = st.tabs(["Rafa  (@_rafamagri)", "Sofia  (@sofiacollins311)", "Avalon  (@avalon.escapes)", "📄 Full Analysis"])

    for i, (aid, tab) in enumerate(zip(["rafa","sofia","avalon"], tabs[:3])):
        with tab:
            posts = load_founder_posts(aid)
            meta  = FOUNDER_META[aid]

            if not posts:
                st.warning(f"No processed data found for {meta['label']}. Run `01_collect.py` + `02_process.py`.")
                continue

            df = posts_to_df(posts)

            c1, c2, c3 = st.columns(3)
            plays   = sum(p.get("video_plays") or 0 for p in posts if (p.get("video_plays") or 0) > 0)
            comments= [p.get("comments") or 0 for p in posts if p.get("comments")]
            c1.metric("Posts Available", len(posts))
            c2.metric("Total Video Plays", fmt_number(plays) if plays else "—")
            c3.metric("Avg Comments", fmt_number(round(statistics.mean(comments),1)) if comments else "—")

            st.markdown("")
            st.markdown("##### Top Posts by Relative Score")
            top = df.sort_values("Relative Score", ascending=False, na_position="last").head(10)
            show_cols = ["Date","Type","Caption","Likes","Comments","Plays","Relative Score","URL"]
            st.dataframe(top[[c for c in show_cols if c in top.columns]], use_container_width=True, hide_index=True)

            st.markdown("##### Content Pillars")
            pillar_counts = df["Pillar"].value_counts()
            if not pillar_counts.empty:
                fig = px.bar(
                    x=pillar_counts.values, y=pillar_counts.index,
                    orientation="h", template=PLOTLY_TMPL,
                    color_discrete_sequence=["#00b4d8"],
                    labels={"x":"Posts","y":"Content Pillar"},
                )
                fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=260)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("##### Hook Styles")
            hook_counts = df["Hook Type"].value_counts()
            if not hook_counts.empty:
                fig2 = px.pie(
                    names=hook_counts.index, values=hook_counts.values,
                    template=PLOTLY_TMPL, color_discrete_sequence=OCEAN_PAL,
                    hole=0.45,
                )
                fig2.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=260,
                                   legend=dict(font=dict(size=11)))
                st.plotly_chart(fig2, use_container_width=True)

            # analysis file
            analysis_path = ANALYSIS_DIR / f"{aid}_analysis.md"
            analysis_md   = safe_load_markdown(analysis_path)
            if analysis_md:
                with st.expander("📄 View Full Written Analysis"):
                    st.markdown(analysis_md)
            else:
                st.info("Written analysis not found. Run `03_analyze.py` to generate it.")

    with tabs[3]:
        cross_md = safe_load_markdown(ANALYSIS_DIR / "cross_account_report.md")
        if cross_md:
            st.markdown("### Cross-Account Report")
            st.markdown(cross_md)
        else:
            st.info("Cross-account report not found. Run `03_analyze.py` to generate it.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: TOP PERFORMERS
# ─────────────────────────────────────────────────────────────────────────────
def page_top_performers():
    st.markdown("## 🏆 Top Performers")

    rafa_p   = load_founder_posts("rafa")
    sofia_p  = load_founder_posts("sofia")
    avalon_p = load_founder_posts("avalon")
    ref_p    = load_reference_posts()

    group_options = {
        "All":                          rafa_p + sofia_p + avalon_p + ref_p,
        "Rafa":                         rafa_p,
        "Sofia":                        sofia_p,
        "Avalon Escapes":               avalon_p,
        "Viral Reference Group (all)":  ref_p,
    }

    col_filter, col_sort = st.columns([2, 1])
    with col_filter:
        selected_group = st.selectbox("Filter by account / group", list(group_options.keys()))
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Relative Score", "Plays", "Likes", "Comments"])

    posts = group_options[selected_group]
    if not posts:
        st.info("No posts available for this selection.")
        return

    df = posts_to_df(posts)
    sort_col = {
        "Relative Score": "Relative Score",
        "Plays":          "Plays",
        "Likes":          "Likes",
        "Comments":       "Comments",
    }[sort_by]

    # convert display columns back to numeric for sorting
    numeric_df = df.copy()
    for col in ["Likes","Comments","Plays"]:
        if col in numeric_df:
            raw = [p.get({"Likes":"likes","Comments":"comments","Plays":"video_plays"}[col]) for p in posts]
            numeric_df[col+"_raw"] = [v if v and v > 0 else 0 for v in raw]

    sort_col_actual = sort_col + "_raw" if sort_col in ["Likes","Comments","Plays"] else sort_col
    if sort_col_actual in numeric_df.columns:
        numeric_df = numeric_df.sort_values(sort_col_actual, ascending=False, na_position="last")

    display_cols = ["Account","Group","Date","Type","Caption","Likes","Comments","Plays","Relative Score","Tier (est.)","URL"]
    st.markdown(f"**{len(df)} posts** — sorted by {sort_by}")
    st.dataframe(
        numeric_df[[c for c in display_cols if c in numeric_df.columns]],
        use_container_width=True, hide_index=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PATTERN CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def page_charts():
    st.markdown("## 📈 Pattern Evidence Charts")

    ref_p  = load_reference_posts()
    all_p  = load_founder_posts("rafa") + load_founder_posts("sofia") + load_founder_posts("avalon") + ref_p

    if not all_p:
        st.warning("No data available.")
        return

    df = posts_to_df(all_p)

    # add raw numeric columns
    raw_map = {"Likes": "likes", "Comments": "comments", "Plays": "video_plays"}
    for col, key in raw_map.items():
        df[col + " (raw)"] = [p.get(key) if (p.get(key) or -1) > 0 else None for p in all_p]
    df["Score (raw)"] = [p.get("relative_score") for p in all_p]
    df["Duration Bucket"] = [duration_bucket(p.get("duration_sec")) for p in all_p]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Format vs Performance",
        "Content Pillar vs Performance",
        "Destination vs Performance",
        "Top Posts per Destination",
        "Hook Style vs Performance",
        "Caption Length vs Performance",
        "Reel Duration vs Performance",
    ])

    # ── Format ───────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("**Average engagement by post format**")
        fmt_df = df.groupby("Type").agg(
            Avg_Plays=("Plays (raw)", "mean"),
            Avg_Likes=("Likes (raw)", "mean"),
            Avg_Comments=("Comments (raw)", "mean"),
            Avg_Score=("Score (raw)", "mean"),
            Posts=("Type", "count"),
        ).reset_index().sort_values("Avg_Plays", ascending=False, na_position="last")
        fmt_df.columns = ["Format","Avg Plays","Avg Likes","Avg Comments","Avg Rel. Score","Posts"]

        fig = px.bar(
            fmt_df, x="Format", y=["Avg Plays","Avg Likes"],
            barmode="group", template=PLOTLY_TMPL,
            color_discrete_sequence=["#00b4d8","#c9a84c"],
        )
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=320)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(fmt_df, use_container_width=True, hide_index=True)

    # ── Content Pillar vs Performance ────────────────────────────────────────
    with tab2:
        st.markdown("**Engagement by content pillar** (what type of content is it?)")
        pillar_df = df.groupby("Pillar").agg(
            Avg_Plays=("Plays (raw)", "mean"),
            Posts=("Pillar", "count"),
            Avg_Score=("Score (raw)", "mean"),
        ).reset_index().sort_values("Avg_Plays", ascending=False, na_position="last")
        pillar_df.columns = ["Content Pillar","Avg Plays","Posts","Avg Rel. Score"]

        fig = px.bar(
            pillar_df, x="Avg Plays", y="Content Pillar",
            orientation="h", template=PLOTLY_TMPL,
            color="Posts", color_continuous_scale=["#0d3040","#00b4d8"],
            labels={"x":"Avg Plays","y":"Content Pillar"},
        )
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=420)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pillar_df, use_container_width=True, hide_index=True)

    # ── Destination vs Performance ────────────────────────────────────────────
    with tab3:
        st.markdown("**Engagement by destination/package** (which Avalon destination does it support?)")
        dest_df = df.groupby("Destination").agg(
            Avg_Plays=("Plays (raw)", "mean"),
            Posts=("Destination", "count"),
            Avg_Score=("Score (raw)", "mean"),
            Avg_Comments=("Comments (raw)", "mean"),
        ).reset_index().sort_values("Avg_Score", ascending=False, na_position="last")
        dest_df.columns = ["Destination","Avg Plays","Posts","Avg Rel. Score","Avg Comments"]

        dest_order = ["Maldives","Colombia","Brazil","Türkiye","Sri Lanka","Global / Curated Escapes"]
        dest_df["Destination"] = pd.Categorical(
            dest_df["Destination"], categories=dest_order, ordered=True
        )
        dest_df = dest_df.sort_values("Destination", na_position="last")

        fig = px.bar(
            dest_df, x="Destination", y="Avg Rel. Score",
            template=PLOTLY_TMPL, color="Destination",
            color_discrete_sequence=OCEAN_PAL,
            text="Posts",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Best content pillars per destination")
        cross = df.groupby(["Destination","Pillar"]).size().reset_index(name="Posts")
        cross_pivot = cross.pivot(index="Destination", columns="Pillar", values="Posts").fillna(0).astype(int)
        st.dataframe(cross_pivot, use_container_width=True)

    # ── Top Posts per Destination ─────────────────────────────────────────────
    with tab4:
        st.markdown("**Top posts per destination** (by relative score)")
        dest_sel = st.selectbox(
            "Select destination",
            ["Maldives","Colombia","Brazil","Türkiye","Sri Lanka","Global / Curated Escapes"],
            key="dest_chart_sel",
        )
        dest_posts_df = df[df["Destination"] == dest_sel].copy()
        if dest_posts_df.empty:
            st.info(f"No posts detected for **{dest_sel}** in the current dataset.")
        else:
            dest_posts_df = dest_posts_df.sort_values("Relative Score", ascending=False, na_position="last")
            show = ["Account","Date","Type","Pillar","Caption","Plays","Comments","Relative Score","URL"]
            st.dataframe(
                dest_posts_df[[c for c in show if c in dest_posts_df.columns]].head(20),
                use_container_width=True, hide_index=True,
            )

    # ── Hook Style ───────────────────────────────────────────────────────────
    with tab5:
        st.markdown("**Average relative score by hook type**")
        hook_df = df.groupby("Hook Type").agg(
            Avg_Score=("Score (raw)", "mean"),
            Posts=("Hook Type", "count"),
        ).reset_index().dropna(subset=["Avg_Score"]).sort_values("Avg_Score", ascending=False)
        hook_df.columns = ["Hook Type","Avg Rel. Score","Posts"]

        fig = px.bar(
            hook_df, x="Avg Rel. Score", y="Hook Type",
            orientation="h", template=PLOTLY_TMPL,
            color_discrete_sequence=["#c9a84c"],
            text="Posts",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=380)
        st.plotly_chart(fig, use_container_width=True)

    # ── Caption Length ───────────────────────────────────────────────────────
    with tab6:
        st.markdown("**Caption length vs relative score**")
        cap_df = df.copy()
        cap_df["Caption Length"] = [len(p.get("caption") or "") for p in all_p]
        cap_df["Cap. Bucket"] = pd.cut(
            cap_df["Caption Length"], bins=[0,50,150,350,700,5000],
            labels=["< 50","50–150","150–350","350–700","700+"]
        )
        cap_agg = cap_df.groupby("Cap. Bucket", observed=True).agg(
            Avg_Score=("Score (raw)", "mean"),
            Posts=("Cap. Bucket", "count"),
        ).reset_index().dropna(subset=["Avg_Score"])
        cap_agg.columns = ["Caption Length","Avg Rel. Score","Posts"]

        fig = px.bar(
            cap_agg, x="Caption Length", y="Avg Rel. Score",
            template=PLOTLY_TMPL, color_discrete_sequence=["#48cae4"],
            text="Posts",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            "<small style='color:#64748b'>Caption length as a proxy for format "
            "style — ultra-short and very long captions both perform well but for different reasons.</small>",
            unsafe_allow_html=True,
        )

    # ── Reel Duration ────────────────────────────────────────────────────────
    with tab7:
        dur_posts = [p for p in all_p if p.get("duration_sec")]
        if not dur_posts:
            st.info("Duration data not available in current dataset.")
        else:
            dur_df = pd.DataFrame({
                "Duration Bucket": [duration_bucket(p.get("duration_sec")) for p in dur_posts],
                "Rel. Score":      [p.get("relative_score") for p in dur_posts],
            }).dropna(subset=["Rel. Score"])
            order = ["< 15s","15–30s","30–45s","45–60s","60s+","Unknown"]
            dur_agg = dur_df.groupby("Duration Bucket")["Rel. Score"].agg(["mean","count"]).reset_index()
            dur_agg.columns = ["Duration","Avg Rel. Score","Posts"]
            dur_agg["Duration"] = pd.Categorical(dur_agg["Duration"], categories=order, ordered=True)
            dur_agg = dur_agg.sort_values("Duration")

            fig = px.bar(
                dur_agg, x="Duration", y="Avg Rel. Score",
                template=PLOTLY_TMPL, color_discrete_sequence=["#4ade80"],
                text="Posts",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CONTENT SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
def page_simulator():
    st.markdown("## 🎯 Avalon Content Simulator")
    st.markdown(
        "Score a new content idea **before** creating it. Uses the rule-based scoring rubric "
        "from the Viral Influencer Trend Pattern Library (out of 100)."
    )
    # FUTURE: replace the rule-based scorer below with a Claude API call
    # using anthropic.Anthropic().messages.create() for richer, context-aware feedback.

    with st.form("content_form"):
        st.markdown("#### Content Idea")
        col1, col2 = st.columns(2)
        with col1:
            idea        = st.text_area("Content Idea / Concept ✱", height=90,
                                       placeholder="e.g. Reel showing tiger shark dive at Fuvahmulah at sunrise")
            destination = st.text_input("Destination", placeholder="e.g. Fuvahmulah, Maldives")
            fmt         = st.selectbox("Format", ["Reel","Carousel","Static Photo","Story","Video"])
            emotion     = st.text_input("Intended Emotion / Feeling",
                                        placeholder="e.g. awe, peace, longing to be there")
        with col2:
            hook    = st.text_area("Draft Hook (first line / first 3 seconds)", height=80,
                                   placeholder="e.g. No one tells you the Maldives you see on Instagram isn't real.")
            caption = st.text_area("Draft Caption / Script (optional)", height=120,
                                   placeholder="Paste your draft caption or Reel narration here...")
            cta     = st.text_input("Call to Action",
                                    placeholder="e.g. Comment 'FUVAH' for our full guide 🦈")

        st.markdown("#### Classification")
        col3, col4 = st.columns(2)
        with col3:
            tier = st.selectbox("Adaptation Tier", [
                "Tier 1 — Direct Trend Adaptation",
                "Tier 2 — Structural Replication",
                "Tier 3 — Inspiration Only",
                "Original Avalon Concept",
            ])
        with col4:
            pattern = st.text_input("Closest Pattern from Library (optional)",
                                    placeholder="e.g. Curiosity-Gap Hook + Expectation Flip")

        submitted = st.form_submit_button("Score this idea →", type="primary")

    if submitted and (idea or hook or caption):
        result = run_scoring(idea, destination, fmt, emotion, hook, caption, cta, tier)

        st.markdown("---")
        st.markdown("### Results")

        # total score + recommendation
        score_col, rec_col = st.columns([1, 2])
        with score_col:
            score_pct = result["total"]
            color     = "#4ade80" if score_pct >= 80 else "#facc15" if score_pct >= 60 else "#fb923c" if score_pct >= 40 else "#f87171"
            st.markdown(
                f"<div style='background:#111827;border:2px solid {color};border-radius:12px;"
                f"padding:1.5rem;text-align:center'>"
                f"<div style='font-size:3.5rem;font-weight:800;color:{color}'>{score_pct}</div>"
                f"<div style='color:#64748b;font-size:.9rem;margin-top:.25rem'>out of 100</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with rec_col:
            st.markdown(
                f"<div style='background:#111827;border:1px solid #1e3a5f;border-radius:12px;"
                f"padding:1.5rem;height:100%'>"
                f"<div style='color:#94a3b8;font-size:.8rem;font-weight:600;letter-spacing:.07em;text-transform:uppercase'>Recommendation</div>"
                f"<div style='font-size:1.4rem;font-weight:700;margin-top:.4rem;color:{result['rec_color']}'>{result['recommendation']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("")
        st.markdown("#### Criterion Breakdown")

        score_rows = []
        for criterion, (pts, note) in result["scores"].items():
            max_pts = int(re.search(r'\((\d+)\)', criterion).group(1))
            score_rows.append({"Criterion": criterion, "Score": pts, "Max": max_pts, "Notes": note})

        score_df = pd.DataFrame(score_rows)
        fig = px.bar(
            score_df, x="Score", y="Criterion", orientation="h",
            template=PLOTLY_TMPL, color="Score",
            color_continuous_scale=["#f87171","#facc15","#4ade80"],
            range_color=[0, 20],
            text="Score",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(score_df[["Criterion","Score","Max","Notes"]], use_container_width=True, hide_index=True)

        # Quick improvement tips
        weak = [(c, pts, note) for c, (pts, note) in result["scores"].items()
                if pts < int(re.search(r'\((\d+)\)', c).group(1)) * 0.6]
        if weak:
            st.markdown("#### Quick Improvements")
            for criterion, pts, note in weak:
                max_pts = int(re.search(r'\((\d+)\)', criterion).group(1))
                st.markdown(
                    f"<div class='ac'><h4>⚠️ {criterion} — {pts}/{max_pts}</h4><p>{note}</p></div>",
                    unsafe_allow_html=True,
                )
    elif submitted:
        st.warning("Please fill in at least the Content Idea field.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: WEEKLY CONTENT PLAN
# ─────────────────────────────────────────────────────────────────────────────
def page_content_plan():
    st.markdown("## 📅 Weekly Content Plan")

    plan_files = sorted(
        [f for f in CONTENT_PLANS.glob("*.md") if f.name != "template.md"],
        reverse=True,
    )

    if not plan_files:
        st.info("No content plan generated yet.")
        st.markdown(
            "<div class='ac'><h4>How to generate a plan</h4>"
            "<p>Ask Claude Code (in the terminal):</p>"
            "<blockquote style='color:#e2e8f0;border-left:3px solid #00b4d8;padding-left:1rem;margin:.5rem 0'>"
            "\"Generate a 7-day Avalon Escapes content plan using the founder analysis and "
            "viral influencer trend reference group. Do not run Apify.\""
            "</blockquote></div>",
            unsafe_allow_html=True,
        )
        return

    plan_labels = [f.stem for f in plan_files]
    selected = st.selectbox("Select plan", plan_labels)
    chosen   = plan_files[plan_labels.index(selected)]
    content  = safe_load_markdown(chosen)
    if content:
        st.markdown(content)
    else:
        st.error("Could not read plan file.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PLAYBOOK
# ─────────────────────────────────────────────────────────────────────────────
def page_playbook():
    st.markdown("## 📖 Avalon Viral Content Playbook")

    col_do, col_dont = st.columns(2)

    with col_do:
        st.markdown(
            "<div class='ac'><h4>✅ Always Do</h4>"
            "<ul style='color:#94a3b8;font-size:.88rem;line-height:2'>"
            "<li>Open with a strong, specific first line — no generic openers</li>"
            "<li>Use details only someone who's <em>actually been there</em> would know</li>"
            "<li>Build emotional tension — set up something before resolving it</li>"
            "<li>Write as if Rafa or Sofia is speaking personally, not as an agency</li>"
            "<li>Use trend formats (Tier 1) only when they genuinely fit Avalon's voice</li>"
            "<li>Make every post either <strong>saveable</strong> or <strong>shareable</strong></li>"
            "<li>End with a clear, keyword-driven CTA</li>"
            "<li>Prioritise Reels — every viral post in the reference group is video</li>"
            "<li>Use the curiosity-gap, expectation-flip, and love-declaration hooks first</li>"
            "<li>Show the experience before selling it</li>"
            "</ul></div>",
            unsafe_allow_html=True,
        )

    with col_dont:
        st.markdown(
            "<div class='ac'><h4>❌ Never Do</h4>"
            "<ul style='color:#94a3b8;font-size:.88rem;line-height:2'>"
            "<li>Sound like a generic travel agency or use corporate language</li>"
            "<li>Copy another creator's exact caption, hook, or personal story</li>"
            "<li>Use phrases like &ldquo;breathtaking views&rdquo;, &ldquo;unforgettable experience&rdquo;, &ldquo;stunning&rdquo;</li>"
            "<li>Post without a hook — the first line decides whether anyone watches</li>"
            "<li>Use trend formats that don't fit Avalon's premium, warm voice</li>"
            "<li>Over-polish content until it loses authenticity and warmth</li>"
            "<li>Mix private or DM data into any content or analysis</li>"
            "<li>Adapt Tier 3 content (personal stories, signature phrases) from the reference group</li>"
            "<li>Post photos when the content needs video to land</li>"
            "<li>Generic hashtag spam — 1–3 highly relevant hashtags only</li>"
            "</ul></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Optimal Content Specs")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div class='ac'><h4>🎬 Reel</h4>"
            "<p><b>Best length:</b> 15–45s (data shows 15–30s and 30–45s perform best)<br>"
            "<b>Hook window:</b> First 3 seconds — no exceptions<br>"
            "<b>Caption:</b> Either 1–5 words (confident minimal) or 150–400 word essay<br>"
            "<b>CTA:</b> DM/comment keyword at the end<br>"
            "<b>Music:</b> Original audio or trending audio where relevant</p></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div class='ac'><h4>📸 Static Post</h4>"
            "<p><b>Caption:</b> 1–10 words for cinematic shots; use essay format for philosophical content<br>"
            "<b>When to use:</b> Only when the visual is so extraordinary it needs no motion<br>"
            "<b>Avoid:</b> Static posts with long, information-dense captions<br>"
            "<b>Tip:</b> A great photo with 3 words outperforms one with 200 generic ones</p></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            "<div class='ac'><h4>📋 Carousel</h4>"
            "<p><b>Best for:</b> Lists, guides, destination tips, founder debates<br>"
            "<b>First slide:</b> Must have a strong hook — it's the only one most people see<br>"
            "<b>Caption:</b> CTA-forward — &ldquo;swipe for all 5&rdquo; or &ldquo;comment GUIDE&rdquo;<br>"
            "<br><em style='color:#64748b'>Optimal specs will improve once more analytics CSVs are added.</em></p></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Top Hook Formulas by Tier")
    st.markdown(
        "See the full **Hook Bank** (20 formulas) in the **Viral Reference Group → Pattern Library** section."
    )

    tier_data = [
        ("Tier 1 — Direct Trend Adaptation", "t1", [
            '"[Country flag] ❤️ To know [X] is to love [X]"',
            '"Just leave your hometown ✈️🌎"',
            '"Comment \'[WORD]\' for our full guide 🌊"',
            '"5 things Rafa and Sofia never agree on when travelling 🫠"',
            '"Average morning in [extraordinary place]"',
            '"A year ago today, [unexpected event]. And somehow… [counterintuitive outcome]"',
        ]),
        ("Tier 2 — Structural Replication", "t2", [
            '"[Destination] completely rewrote every expectation I had."',
            '"They call it [X]. But [this version] is something [X] photos never show you."',
            '"They told you luxury meant [generic thing]. [That\'s not luxury.] That\'s tourism."',
            '"[Day X] at the most remote [place] in [country]. [Specific sensory detail]."',
            '"Society would say that spending [X] on a trip is irresponsible. We\'d call it the best investment."',
        ]),
    ]

    for tier_name, tier_class, examples in tier_data:
        with st.expander(f"**{tier_name}**"):
            for ex in examples:
                st.markdown(
                    f"<div style='background:#0d1a2a;border-left:3px solid #00b4d8;padding:.5rem 1rem;margin:.4rem 0;border-radius:0 6px 6px 0;color:#e2e8f0;font-size:.9rem'>{ex}</div>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DATA QUALITY
# ─────────────────────────────────────────────────────────────────────────────
def page_data_quality():
    st.markdown("## 🔍 Data Quality & Coverage")

    # File status check
    checks = {
        "data/processed/rafa_posts.json":          (DATA_PROCESSED / "rafa_posts.json").exists(),
        "data/processed/sofia_posts.json":         (DATA_PROCESSED / "sofia_posts.json").exists(),
        "data/processed/avalon_posts.json":        (DATA_PROCESSED / "avalon_posts.json").exists(),
        "data/processed/viral_reference_group/group_posts.json": REF_GROUP_POSTS.exists(),
        "analysis/rafa_analysis.md":               (ANALYSIS_DIR / "rafa_analysis.md").exists(),
        "analysis/sofia_analysis.md":              (ANALYSIS_DIR / "sofia_analysis.md").exists(),
        "analysis/avalon_analysis.md":             (ANALYSIS_DIR / "avalon_analysis.md").exists(),
        "analysis/cross_account_report.md":        (ANALYSIS_DIR / "cross_account_report.md").exists(),
        "analysis/viral_reference_group/viral_pattern_library.md": PATTERN_LIB.exists(),
    }

    st.markdown("### File Status")
    rows = [{"File": k, "Status": "✅ Found" if v else "❌ Missing"} for k, v in checks.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "<div class='ac'><h4>✅ Available from public scraping</h4>"
            "<ul style='color:#94a3b8;font-size:.88rem;line-height:1.9'>"
            "<li>Captions (full text)</li>"
            "<li>Post URLs</li>"
            "<li>Comments count (public)</li>"
            "<li>Video views & plays (where visible)</li>"
            "<li>Hashtags</li>"
            "<li>Post type (Reel, carousel, photo)</li>"
            "<li>Timestamps</li>"
            "<li>Music metadata (public)</li>"
            "<li>Location name (when tagged publicly)</li>"
            "<li>Video duration</li>"
            "</ul></div>",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            "<div class='ac'><h4>⚠️ Not available — requires manual export</h4>"
            "<ul style='color:#94a3b8;font-size:.88rem;line-height:1.9'>"
            "<li>Likes (hidden for some accounts on Instagram)</li>"
            "<li>Saves count</li>"
            "<li>Shares count</li>"
            "<li>Reach and impressions</li>"
            "<li>Profile visits from a post</li>"
            "<li>Follows gained from a post</li>"
            "<li>Instagram Native Insights (behind login)</li>"
            "<li>Audience demographics</li>"
            "<li>Stories performance</li>"
            "<li>Link clicks</li>"
            "</ul></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        "<div class='ac'><h4>📊 How to improve prediction accuracy</h4>"
        "<p>Export your Instagram analytics from the Instagram app or Meta Business Suite and "
        "drop the CSV files into <code>data/analytics/</code>.<br><br>"
        "Once added, the dashboard will be able to show saves, reach, profile visits, "
        "and follows gained — the metrics that most accurately predict post effectiveness.<br><br>"
        "See <code>data/analytics/README.md</code> for the expected format.</p></div>",
        unsafe_allow_html=True,
    )

    # Likes availability check
    st.markdown("### Likes Visibility")
    founder_posts = []
    for aid in ("rafa","sofia","avalon"):
        founder_posts.extend(load_founder_posts(aid))

    hidden = sum(1 for p in founder_posts if p.get("likes") is None)
    visible= sum(1 for p in founder_posts if p.get("likes") is not None)
    st.markdown(
        f"Founder / brand posts — likes visible: **{visible}** · likes hidden by Instagram: **{hidden}**"
    )
    if hidden > 0:
        st.caption(
            "Instagram hides likes by default on many accounts. "
            "Video plays and comments are used as the primary engagement signal instead."
        )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if page == "overview":
    page_overview()
elif page == "viral":
    page_viral_reference()
elif page == "founders":
    page_founder_brand()
elif page == "top":
    page_top_performers()
elif page == "charts":
    page_charts()
elif page == "simulator":
    page_simulator()
elif page == "plan":
    page_content_plan()
elif page == "playbook":
    page_playbook()
elif page == "data_quality":
    page_data_quality()
