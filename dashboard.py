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
DATA_PROCESSED       = ROOT / "data" / "processed"
ANALYSIS_DIR         = ROOT / "analysis"
CONTENT_PLANS        = ROOT / "content_plans"
WEEKLY_CALENDAR_FILE = CONTENT_PLANS / "weekly_calendar.json"
PATTERN_LIB          = ANALYSIS_DIR / "viral_reference_group" / "viral_pattern_library.md"
REF_GROUP_POSTS      = DATA_PROCESSED / "viral_reference_group" / "group_posts.json"

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
# VIRAL PATTERNS  (sourced from viral_pattern_library.md — used by simulator)
# Each pattern: keywords for matching + adaptation guidance for Avalon.
# Three tiers: 1 = Direct Trend Adaptation, 2 = Structural Replication, 3 = Inspiration Only
# ─────────────────────────────────────────────────────────────────────────────
VIRAL_PATTERNS = [
    {
        "id": "curiosity_gap",
        "name": "Curiosity-Gap Hook",
        "tier": 2, "tier_label": "Tier 2 — Structural Replication",
        "accounts": ["colinduthie","seanhammonds","noareserrunt","monicaroams","gavinheeks"],
        "keywords": ["no one tells","couldn't believe","can't believe","nothing like","who knew",
                     "still can't","unexpected","didn't expect","surprised","you won't believe",
                     "unbelievable","shocking","secret","nobody knows","hidden"],
        "hook_templates": [
            "No one tells you there are two [DESTINATION]s. Most people only ever see one.",
            "Still can't believe [DESTINATION] exists and nobody talks about it.",
        ],
        "caption_structure": "Opening gap (the thing nobody says) → specific sensory detail → the shift → universal insight any traveler can relate to",
        "visual_direction": "Open on the unexpected angle, not the postcard shot. Let the visual answer the tension created by the hook.",
        "what_not_to_copy": "Do not use @noareserrunt's signature phrase 'That’s what they call it at least…' — it belongs to that creator's identity.",
        "avalon_fit": 88, "replicability": 90,
    },
    {
        "id": "philosophical_essay",
        "name": "Philosophical Essay Reel",
        "tier": 2, "tier_label": "Tier 2 — Structural Replication",
        "accounts": ["noareserrunt","seanhammonds","jords.media","lilifabienne_","colinduthie"],
        "keywords": ["society","perspective","meaning","what travel","it's not about","more than that",
                     "home is","the truth about","what no one","they don't tell","life is short",
                     "philosophy","reflection","realize","realized","insight","what we forget"],
        "hook_templates": [
            "It's not about the hotel. It's about who you become when you stop being reachable.",
            "What they don't tell you about [DESTINATION]: it doesn't ask you to perform.",
        ],
        "caption_structure": "Universal observation → short parallel tension lines → the turn (specific moment) → insight that transcends the location → open-ended closing line",
        "visual_direction": "Slow-motion cinematic cuts timed to narration. The edit reinforces the emotional arc — not the sights.",
        "what_not_to_copy": "Do not use @noareserrunt's 'Society doesn't kill dreams' manifesto or any passage from it. Do not copy any specific philosophical essay from a reference creator.",
        "avalon_fit": 82, "replicability": 75,
    },
    {
        "id": "love_declaration",
        "name": "Country / Destination Love Declaration",
        "tier": 1, "tier_label": "Tier 1 — Direct Trend Adaptation",
        "accounts": ["jackrosen6","seanhammonds","gavinheeks","colinduthie","monicaroams"],
        "keywords": ["love","heart","favourite","favorite","heaven","adore","obsessed","colombia",
                     "maldives","brazil","brasil","türkiye","turkiye","sri lanka","this place",
                     "will always","changed my life","forever","country","destination love"],
        "hook_templates": [
            "[DESTINATION] 🌊 / Most people only know one side of it. We know all of them.",
            "COLOMBIA 🇨🇴 / Cartagena is just the introduction. / Sofia has been going to Providencia since before there was an Avalon.",
        ],
        "caption_structure": "[DESTINATION + flag emoji] / [Specific personal detail most tourists miss] / [What this means for someone who travels with Avalon]",
        "visual_direction": "Hero destination shot. The footage must be specific and personal, not generic stock-style.",
        "what_not_to_copy": "Generic 'love this place' copy without personal specificity. Do not copy exact captions from reference creators.",
        "avalon_fit": 90, "replicability": 95,
    },
    {
        "id": "expectation_subversion",
        "name": "Expectation Subversion",
        "tier": 2, "tier_label": "Tier 2 — Structural Replication",
        "accounts": ["seanhammonds","colinduthie","monicaroams","jackrosen6"],
        "keywords": ["exceeded","expectation","surprised","wasn't expecting","completely changed",
                     "nothing like i","thought it was","wrong about","misconception","preconception",
                     "actually amazing","not what","different from","changed my mind","rewrote"],
        "hook_templates": [
            "[DESTINATION] completely rewrote every expectation I had about luxury travel.",
            "Everyone told me [DESTINATION] was overwhelming. They were talking about the wrong [DESTINATION].",
        ],
        "caption_structure": "[Admission of the misconception most people have] / [What first-hand experience revealed] / [What it changed in the narrator]",
        "visual_direction": "Open with the cliché frame — then hard cut to the real version Avalon knows.",
        "what_not_to_copy": "Do not copy specific country narratives or personal testimony — those stories belong to those creators.",
        "avalon_fit": 87, "replicability": 88,
    },
    {
        "id": "ultra_short_cinematic",
        "name": "Ultra-Short Hook + Cinematic Visual",
        "tier": 1, "tier_label": "Tier 1 — Direct Trend Adaptation",
        "accounts": ["colinduthie","seanhammonds","noareserrunt","colemangeiger","gavinheeks"],
        "keywords": ["cinematic","footage","visuals","film","just","minimal","pure","dawn","sunrise",
                     "underwater","quiet","wild","raw","real","only","nothing more","brevity"],
        "hook_templates": [
            "Nothing like the [DESTINATION] they show you.",
            "The ocean at Fuvahmulah. That's it. That's the post.",
        ],
        "caption_structure": "One confident sentence. Maximum 6 words. The visual earns the brevity.",
        "visual_direction": "Footage must be extraordinary — Fuvahmulah underwater, Cartagena golden hour, Sri Lanka tea country at dawn. Do not use this format with average footage.",
        "what_not_to_copy": "Do not imitate @colinduthie's specific pop culture comparisons ('Minecraft IRL', 'The Disneyland of Iran') — those are his signature formula.",
        "avalon_fit": 78, "replicability": 92,
    },
    {
        "id": "trip_invitation",
        "name": "Trip Invitation / Join Us",
        "tier": 1, "tier_label": "Tier 1 — Direct Trend Adaptation",
        "accounts": ["gavinheeks","monicaroams","viluagency"],
        "keywords": ["join us","join me","spots","trip","coming with","invite","invitation","hosting",
                     "limited","we're going","group","book","available","register","departure",
                     "space","open","who's coming","who wants to"],
        "hook_templates": [
            "We're taking 6 people to [DESTINATION] this season. Tiger sharks, freedom, and a route no one else is running. 5 spots left.",
            "YOUR CHANCE TO TRAVEL WITH AVALON 🌊 / We're opening [DESTINATION] for a curated group. Who's coming?",
        ],
        "caption_structure": "[Trip reveal — destination + dates] / [What makes this route different] / [Who it's for] / [Limited spots CTA]",
        "visual_direction": "Founders on camera inviting viewers personally. Mix destination footage with behind-the-scenes planning shots.",
        "what_not_to_copy": "Do not copy @viluagency's specific Spanish-language phrasing — those belong to their brand identity.",
        "avalon_fit": 95, "replicability": 96,
    },
    {
        "id": "keyword_cta",
        "name": "Keyword / Comment CTA",
        "tier": 1, "tier_label": "Tier 1 — Direct Trend Adaptation",
        "accounts": ["gavinheeks","monicaroams","colinduthie"],
        "keywords": ["comment","dm","guide","send","keyword","type","message","reply","want info",
                     "interested","itinerary","for the link","drop your","comment below"],
        "hook_templates": [
            "Comment '[DESTINATION]' and we'll send you our full guide — hotels, routes, and the things only we know.",
            "DM us the word 'ESCAPE' and we'll design your [DESTINATION] trip this week.",
        ],
        "caption_structure": "Engaging opening (destination or experience) + value proposition + clear keyword CTA at the end. Short. Every word earns its place.",
        "visual_direction": "Any strong Avalon visual works — the CTA is the engine, not the footage.",
        "what_not_to_copy": "Do not copy specific keyword phrases used by reference creators. Use Avalon's own branded keywords.",
        "avalon_fit": 90, "replicability": 98,
    },
    {
        "id": "society_challenge",
        "name": "Society / System Challenge",
        "tier": 2, "tier_label": "Tier 2 — Structural Replication",
        "accounts": ["noareserrunt","seanhammonds","monicaroams"],
        "keywords": ["society","supposed to","they told","conventional","expected","system","career",
                     "mortgage","office","monday","9 to 5","rat race","escape","different choice",
                     "opted out","quit","left","freedom","not supposed to"],
        "hook_templates": [
            "What they don't teach you: time is the real luxury. Not hotels.",
            "You weren't meant to spend your whole life saving up for a trip you'll keep postponing.",
        ],
        "caption_structure": "[Conventional expectation most people accept] → [The crack in that logic] → [Travel as the alternative] → [Avalon as the practical step]",
        "visual_direction": "Contrast edit — grey/urban/routine shots cut against vivid Avalon destination footage.",
        "what_not_to_copy": "Do not use @noareserrunt's 'Society doesn't kill dreams' manifesto. Do not copy any specific philosophical text from reference creators.",
        "avalon_fit": 72, "replicability": 70,
    },
    {
        "id": "founder_journey",
        "name": "Founder / Agency Journey",
        "tier": 2, "tier_label": "Tier 2 — Structural Replication",
        "accounts": ["monicaroams","colinduthie","jords.media"],
        "keywords": ["founded","started","built","journey","a year ago","origin","story","began",
                     "rafa","sofia","avalon","why we","how we","behind the","milestone",
                     "when we first","the beginning","chapter","how it started"],
        "hook_templates": [
            "A year ago, Avalon was two people and a shared obsession with the Indian Ocean.",
            "Here's how Rafa and Sofia went from diving in Fuvahmulah to designing trips for other people who needed to feel that way.",
        ],
        "caption_structure": "[Founding story beat] → [The key moment of decision or clarity] → [What Avalon became because of it] → [What this means for the viewer]",
        "visual_direction": "Founder footage from early trips + current high-quality production footage. Real and polished together.",
        "what_not_to_copy": "Do not copy personal backstory or milestone narratives from reference creators — Rafa and Sofia have their own genuine story to tell.",
        "avalon_fit": 85, "replicability": 80,
    },
    {
        "id": "underrated_destination",
        "name": "Underrated / Overlooked Destination",
        "tier": 2, "tier_label": "Tier 2 — Structural Replication",
        "accounts": ["seanhammonds","monicaroams","colinduthie","jackrosen6"],
        "keywords": ["underrated","overlooked","no one talks","off the radar","not on the list",
                     "misunderstood","beyond","real side","lesser known","nobody tells",
                     "unpopular opinion","they never show","tourist trail","hidden side"],
        "hook_templates": [
            "Nobody talks about [DESTINATION] beyond the obvious. That's Avalon's favourite thing about it.",
            "The version of [DESTINATION] that never makes it onto Instagram. We've been going there for years.",
        ],
        "caption_structure": "[The common misconception or tourist version] / [What first-hand Avalon experience revealed] / [The specific detail only insiders know] / [Invitation to see it this way]",
        "visual_direction": "Open with the cliché tourist shot — then immediately cut to the real, lesser-known version Avalon knows.",
        "what_not_to_copy": "Do not copy specific country narratives or personal testimonies from reference creators — those observations belong to them.",
        "avalon_fit": 89, "replicability": 85,
    },
    {
        "id": "founder_personality",
        "name": "Founder Personality Dynamic",
        "tier": 1, "tier_label": "Tier 1 — Direct Trend Adaptation",
        "accounts": ["viluagency"],
        "keywords": ["rafa","sofia","founders","team rafa","team sofia","we disagree","non-negotiable",
                     "which one are you","our debate","our rules","behind avalon","two of us",
                     "we couldn't agree","our travel style","personality","both founders"],
        "hook_templates": [
            "Rafa wants 5-star. Sofia wants adventure. Here's what happens when we plan a trip together.",
            "Our 5 non-negotiables when we design an Avalon escape. Rafa and Sofia do not agree on all of them.",
        ],
        "caption_structure": "[The personality reveal or debate topic] / [Rafa's position] / [Sofia's position] / [What Avalon clients get: the best of both] / [Pick sides CTA]",
        "visual_direction": "Both founders on camera. Split-screen or alternating cuts. Real and personal — not rehearsed.",
        "what_not_to_copy": "Do not copy @viluagency's specific Spanish-language personality format — those belong to their brand.",
        "avalon_fit": 93, "replicability": 92,
    },
    {
        "id": "human_moment",
        "name": "Human Moment Over Destination",
        "tier": 3, "tier_label": "Tier 3 — Inspiration Only",
        "accounts": ["jackrosen6","seanhammonds","colinduthie"],
        "keywords": ["local people","locals","met someone","human connection","shared a meal",
                     "person i met","family","community","stranger","kindness","offered","gave me",
                     "reminded me","humanity","connection","the people","a woman","a man","an old"],
        "hook_templates": [
            "You go to [DESTINATION] for the ocean. You come back because of the people who live inside it.",
            "The moment that changed how I see [DESTINATION] had nothing to do with the destination.",
        ],
        "caption_structure": "[The unexpected human encounter, specific and concrete] / [What it revealed about the place] / [What it revealed about travel itself]",
        "visual_direction": "Authentic, unposed footage of human connection moments. The rawness is the point — do not over-produce.",
        "what_not_to_copy": "These stories are deeply personal to each creator. Rafa and Sofia must tell their own genuine version — not an adaptation of a reference creator's narrative.",
        "avalon_fit": 75, "replicability": 40,
    },
]

# ── Hashtag sets per Avalon destination (used by simulator improvement engine) ─
DESTINATION_HASHTAGS = {
    "Maldives": [
        "#maldives", "#fuvahmulah", "#divingmaldives", "#tigershark",
        "#freediving", "#indianocean", "#maldivesislands", "#oceanlife",
        "#luxurymaldives", "#islandescape", "#luxurytravel", "#avalon_escapes",
        "#curatedtravel", "#boutiquetravel",
    ],
    "Colombia": [
        "#colombia", "#cartagena", "#providencia", "#colombiatravel",
        "#caribbeancolombia", "#latinamerica", "#colombialuxury",
        "#tropicalescapes", "#curatedtravel", "#avalon_escapes",
        "#luxurylatin", "#bespoketravel",
    ],
    "Brazil": [
        "#brazil", "#brasil", "#fernandodenoronha", "#riolife",
        "#braziltravel", "#lencoismaranhenses", "#latinamerica",
        "#southamerica", "#brazilianparadise", "#luxurybrazil",
        "#curatedtravel", "#avalon_escapes",
    ],
    "Türkiye": [
        "#turkey", "#turkiye", "#istanbul", "#cappadocia", "#bodrum",
        "#aegeansea", "#turkishcoast", "#turkeytravel", "#luxuryturkey",
        "#boutiqueuescapes", "#curatedtravel", "#avalon_escapes",
    ],
    "Sri Lanka": [
        "#srilanka", "#srilankatravel", "#ella", "#mirissa", "#galle",
        "#srilankaluxury", "#ceylon", "#tropicalluxury", "#srilankan",
        "#boutiqueholiday", "#curatedtravel", "#avalon_escapes",
    ],
    "Global / Curated Escapes": [
        "#luxurytravel", "#boutiquetravel", "#curatedtravel", "#bespoketravel",
        "#tailormadetravel", "#privatetour", "#honeymoontravel", "#travelcouple",
        "#luxurytravelblogger", "#avalon_escapes", "#luxescapes", "#intentionaltravel",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY CALENDAR CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
WEEKDAYS       = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CONTENT_FORMATS = ["", "Reel", "Carousel", "Photo", "Story", "Founder Story", "Destination Guide", "Trend Adaptation"]
POST_STATUSES   = ["Idea", "Draft", "Needs improvement", "Ready", "Posted"]
DESTINATIONS_LIST = ["", "Maldives", "Colombia", "Brazil", "Türkiye", "Sri Lanka", "Global / Other Curated Escapes"]

FORMAT_HINTS = {
    "Reel":               "🎬 Plan first 3 seconds, visual pacing, text overlay, and share trigger.",
    "Carousel":           "📱 Strong first-slide hook = saves. Plan slide sequence, guide value, and save CTA. Reference @travelcroats.",
    "Photo":              "📸 One strong image. Match caption emotion to image energy. End with a comment prompt.",
    "Story":              "📲 Behind-the-scenes tone. Use a poll, question sticker, or swipe-up link.",
    "Founder Story":      "🎤 Rafa or Sofia speaking directly. Personal and specific — not agency language.",
    "Destination Guide":  "🗺️ Numbered hook → specific tips → save trigger → keyword CTA.",
    "Trend Adaptation":   "🔥 Identify Tier 1/2 trend first. Adapt the structure — not the exact words or footage.",
}

_STATUS_STYLE = {
    "Idea":              ("#64748b", "#1e2a3a"),
    "Draft":             ("#0284c7", "#0c2340"),
    "Needs improvement": ("#d97706", "#2d1e04"),
    "Ready":             ("#16a34a", "#0a2614"),
    "Posted":            ("#7c3aed", "#1e0a3a"),
}

SAMPLE_AVALON_WEEK = [
    {
        "format": "Reel",
        "content_pillar": "Ocean & Island Adventures",
        "destination_package": "Maldives",
        "idea": "The Fuvahmulah experience — what it actually feels like to dive with 20 tiger sharks and come back changed",
        "hook": "This is what it feels like to dive with 20 tiger sharks and come back completely changed.",
        "visual_plan": "Open underwater on a tiger shark approaching camera. Cut to surface reflection. Cut to reaction face post-dive. Slow-mo coral. End on island sunset with text CTA overlay.",
        "caption": "No one prepares you for Fuvahmulah.\n\nYou go because you heard about the tiger sharks.\nYou stay because of everything else.\n\nThe silence underwater. The colour of the atoll at 6am. The feeling that you've arrived somewhere the world hasn't quite found yet.\n\nThis is the Maldives we design trips around. Not the overwater bungalow brochure version. The real one.\n\nComment 'FUVA' and we'll send you our Maldives diving guide. 🌊",
        "cta": "Comment 'FUVA' for our Maldives diving guide →",
        "hashtags": "#maldives #fuvahmulah #divingmaldives #tigershark #oceanlover #luxurytravel #avalonescapes",
        "status": "Draft",
        "notes": "Needs underwater footage from Fuvahmulah. If unavailable, adapt for any Maldives diving content.",
        "visual_plan_short": "",
    },
    {
        "format": "Carousel",
        "content_pillar": "Destination Guide",
        "destination_package": "Sri Lanka",
        "idea": "5 things no one tells you about Sri Lanka before you go",
        "hook": "5 things no one tells you about Sri Lanka (save this before your trip)",
        "visual_plan": "Slide 1: Bold text — '5 things no one tells you about Sri Lanka'. Slide 2: Hill country train — 'The train is the journey, not just the transport'. Slide 3: Temple at dawn — 'Go before 7am'. Slide 4: East coast beach — 'The south and east coast are completely different countries'. Slide 5: Local food — 'Sri Lankan food is the secret everyone misses'. Slide 6: Avalon brand slide with CTA.",
        "caption": "Sri Lanka will surprise you — but only if you know what to look for.\n\nSave this before your trip →\n\nWe design bespoke Sri Lanka escapes: cultural triangle, tea hills, east coast, and the parts no guidebook covers. DM 'SRILANKA' to start yours.",
        "cta": "DM 'SRILANKA' for our bespoke Sri Lanka itinerary →",
        "hashtags": "#srilanka #srilankatravel #travelguide #asiatravel #luxurytravel #avalonescapes",
        "status": "Idea",
        "notes": "Reference @travelcroats for carousel structure and first-slide hook style. High save potential.",
    },
    {
        "format": "Photo",
        "content_pillar": "Founder Story",
        "destination_package": "Colombia",
        "idea": "A quiet morning in Cartagena — why Rafa keeps going back",
        "hook": "Cartagena at 6am is a completely different city.",
        "visual_plan": "Single editorial frame: colonial street at dawn, warm orange light, no tourists yet. Rafa walking away from camera or standing still. Clean, warm, intimate feel.",
        "caption": "Cartagena at 6am is a completely different city.\n\nBefore the heat. Before the crowds. Before the day has decided what it wants to be.\n\nI've been here a dozen times and this hour still stops me.\n\nThis is the Colombia we introduce people to. Not the surface. The underneath.\n\nWhere should we take you this year?",
        "cta": "Where should we take you this year? ↓",
        "hashtags": "#cartagena #colombia #colombiatravel #founderstory #boutiquetraveler #avalonescapes",
        "status": "Idea",
        "notes": "Best with a genuinely quiet, golden-hour Cartagena shot. No heavy filter — keep it real and editorial.",
    },
    {
        "format": "Reel",
        "content_pillar": "Travel Philosophy",
        "destination_package": "Global / Other Curated Escapes",
        "idea": "Philosophical Reel — what travel actually costs you (not money)",
        "hook": "No one tells you what travel actually costs you. And I don't mean money.",
        "visual_plan": "[0–3s] Static wide shot — airport or empty road. Text overlay: 'No one tells you what travel actually costs you.' [3–15s] Quick cuts: meaningful moments — people, landscapes, meals. [15–35s] Slower pace — one face, one place, stillness. [35–50s] Return shot — back home but different. [50–60s] Final line on screen + Avalon CTA.",
        "caption": "No one tells you what travel actually costs you.\nAnd I don't mean money.\n\nIt costs you the comfortable version of yourself.\nThe one that knew what to expect.\nThe one that had a clean answer to every question.\n\nYou go. You see something you can't unsee.\nAnd you come back as someone the old version of you would find slightly confusing.\n\nThat's the point. That's what we design.\n\nComment 'AVALON' if you're ready. 🌍",
        "cta": "Comment 'AVALON' if you're ready →",
        "hashtags": "#travelphilosophy #whyitravel #travelmindset #conscioustravel #luxurytraveler #avalonescapes",
        "status": "Idea",
        "notes": "Tier 2 structural replication — philosophical essay format. @jords.media + @noareserrunt reference. Strong share/save potential.",
    },
    {
        "format": "Destination Guide",
        "content_pillar": "Destination Guide",
        "destination_package": "Türkiye",
        "idea": "The Türkiye no one shows you — beyond Istanbul and the balloon photos",
        "hook": "Türkiye has 3 versions. Most tourists only see 1.",
        "visual_plan": "Slide 1: Bold — 'Türkiye has 3 versions. Most tourists only see 1.' Slide 2: Istanbul skyline — 'The one everyone knows'. Slide 3: Cappadocia balloons — 'The one Instagram made famous'. Slide 4: Lycian coast/Kaş — 'The one that actually stays with you'. Slide 5: Boutique hotel detail shot. Slide 6: Avalon CTA.",
        "caption": "Türkiye has 3 versions.\nMost tourists only see 1.\n\nSave this — then ask us to show you the third one.\n\nDM 'TURKEY' for our custom Türkiye escape design.",
        "cta": "DM 'TURKEY' for our custom Türkiye escape →",
        "hashtags": "#turkiye #turkey #istanbul #cappadocia #kastravel #aegeancoast #boutiquetraveler #avalonescapes",
        "status": "Idea",
        "notes": "Three-part reveal structure. Inspired by @travelcroats carousel format. Needs footage across all three regions.",
    },
    {
        "format": "Reel",
        "content_pillar": "Luxury Escapes",
        "destination_package": "Brazil",
        "idea": "A boutique stay in Trancoso — luxury that stops trying to impress you",
        "hook": "This is what luxury looks like when it stops trying to impress you.",
        "visual_plan": "[0–3s] Trancoso quadrado at golden hour. [3–15s] Boutique property detail — handmade textiles, hammock, outdoor shower. [15–35s] Atlantic forest, red cliffs, ocean. [35–50s] Guest walking slowly. [50–60s] Final frame: ocean through a door frame. Avalon text CTA.",
        "caption": "This is what luxury looks like when it stops trying to impress you.\n\nNo marble lobbies. No dress code. No pretense.\n\nJust space. Light. The sound of the Atlantic forest at 5am.\n\nTrancoso is the version of Brazil most people never find.\n\nWe design private escapes there. DM us 'TRANCOSO' if you want the full picture. 🌿",
        "cta": "DM 'TRANCOSO' for our Trancoso escape design →",
        "hashtags": "#trancoso #brazil #brasil #boutiquehotel #luxurytravel #atlanticforest #avalonescapes",
        "status": "Idea",
        "notes": "Expectation subversion format — redefining luxury. Tier 2 structural replication. Needs non-generic Trancoso footage.",
    },
    {
        "format": "Story",
        "content_pillar": "Founder Story",
        "destination_package": "Global / Other Curated Escapes",
        "idea": "Sunday behind-the-scenes: how Rafa or Sofia actually plans a custom escape",
        "hook": "This is what building a custom trip actually looks like on a Sunday.",
        "visual_plan": "Story series: (1) Rafa/Sofia at desk with maps or mood board. (2) Zoomed shot of route being planned. (3) Poll sticker: 'Would you want to see more behind-the-scenes?' (4) Question sticker: 'Where should we take you in 2026?'",
        "caption": "Not a Reel today. Just a Sunday process peek.\n\nThis is how an Avalon escape gets built — before it becomes the trip someone tells their friends about for years.\n\nSlide 2 → our current favourite route.\nSlide 3 → vote on what we share next.\nSlide 4 → the one that matters. 👇",
        "cta": "Question sticker: Where should we take you in 2026?",
        "hashtags": "#behindthescenes #founderstory #customtravel #travelagency #avalonescapes",
        "status": "Idea",
        "notes": "Stories don't need high production value — raw is better. Poll + question sticker are the engagement drivers. Use to research audience destination preferences.",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL FRAMEWORKS CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
MARKETING_SKILLS_MAP = {
    "copywriting": {
        "name": "Copywriting",
        "icon": "✍️",
        "source_skill": "skills/copywriting/",
        "one_liner": "Clear, compelling, action-driving copy — clarity over cleverness.",
        "key_frameworks": ["AIDA (Attention → Interest → Desire → Action)", "PAS (Problem → Agitate → Solution)", "BAB (Before → After → Bridge)"],
        "core_principles": [
            "Benefits over features — 'feel the silence at Fuvahmulah' not '5-night Maldives package'",
            "Specificity creates credibility — exact sensory detail beats vague superlatives",
            "Customer language — use the words your client uses to describe the feeling they want",
            "One idea per section — each stanza advances one emotional argument",
        ],
        "avalon_application": "Every hook, caption, CTA, and carousel slide. If the copy doesn't earn its sentence, cut it.",
        "content_types": {"Reel", "Photo", "Carousel", "Story", "Founder Story"},
        "keywords": ["hook", "headline", "caption", "copy", "first line", "cta", "rewrite", "open"],
    },
    "content_strategy": {
        "name": "Content Strategy",
        "icon": "📐",
        "source_skill": "skills/content-strategy/",
        "one_liner": "Decide what to create, why, and how to make it searchable or shareable.",
        "key_frameworks": ["Searchable vs Shareable", "Content Pillars (3–5 topics)", "80/20 Content Mix", "Repurposing Matrix"],
        "core_principles": [
            "Every post must be searchable, shareable, or both",
            "Searchable content captures existing demand (Maldives guides, Sri Lanka itinerary)",
            "Shareable content creates demand (emotional Reels, philosophical travel essays)",
            "Consistency compounds — 3–4× per week beats sporadic high-effort output",
        ],
        "avalon_application": "Weekly calendar planning, pillar balance, guide carousels (searchable), philosophical Reels (shareable).",
        "content_types": {"Destination Guide", "Carousel", "Trend Adaptation"},
        "keywords": ["guide", "tips", "itinerary", "plan", "calendar", "pillar", "strategy", "content"],
    },
    "marketing_psychology": {
        "name": "Marketing Psychology",
        "icon": "🧠",
        "source_skill": "skills/marketing-psychology/",
        "one_liner": "Understand why people buy and how to influence decisions ethically.",
        "key_frameworks": ["Jobs to Be Done", "Loss Aversion", "Social Proof", "Scarcity & Exclusivity", "Anchoring"],
        "core_principles": [
            "JTBD — clients hire Avalon for transformation and connection, not logistics",
            "Loss aversion — 'most people never find this side of Sri Lanka' works harder than 'discover Sri Lanka'",
            "Social proof — real founder experience > generic travel claims",
            "Scarcity — 'we design 8 custom escapes per month' creates urgency without pressure",
        ],
        "avalon_application": "Caption angle framing, CTA psychology, how Rafa and Sofia talk about their real experiences.",
        "content_types": {"Reel", "Photo", "Founder Story"},
        "keywords": ["feel", "emotion", "transform", "philosophy", "reminder", "why", "soul", "meaning"],
    },
    "cro": {
        "name": "Conversion Optimisation",
        "icon": "🎯",
        "source_skill": "skills/cro/",
        "one_liner": "Turn attention into action — DMs, saves, link clicks, and inquiries.",
        "key_frameworks": ["CTA Specificity", "Friction Reduction", "Value Proposition Clarity", "Headline-to-Offer Congruency"],
        "core_principles": [
            "Value prop clarity in 5 seconds — what is this and why should I care?",
            "Keyword CTAs reduce friction ('Comment FUVA' > 'visit our website')",
            "Specific CTAs convert better than generic ones ('DM us your dream destination' → vague)",
            "The hook must match what the post delivers — no bait-and-switch",
        ],
        "avalon_application": "CTA writing, keyword comment/DM funnels, carousel save triggers, inquiry generation.",
        "content_types": {"Reel", "Carousel", "Destination Guide"},
        "keywords": ["dm", "comment", "guide", "keyword", "cta", "convert", "inquiry", "book", "save"],
    },
    "social_media": {
        "name": "Social Media Strategy",
        "icon": "📱",
        "source_skill": "skills/social/",
        "one_liner": "Platform-specific content creation, Reels, carousels, and engagement strategy.",
        "key_frameworks": ["Platform Content Pillars (30/25/25/15/5 mix)", "Reel Hook Framework", "Carousel Save Framework", "Story Engagement Loop"],
        "core_principles": [
            "Reels are the primary Instagram discovery channel — prioritise them",
            "Carousels drive saves — the most bookmarkable post format",
            "Stories build direct connection — raw, behind-the-scenes, polls",
            "Engagement depth (comments > likes) is the algorithm signal that content resonated",
        ],
        "avalon_application": "Weekly format mix, Reel vs carousel ratio, Stories cadence, hashtag strategy.",
        "content_types": {"Reel", "Story", "Carousel"},
        "keywords": ["reel", "carousel", "story", "algorithm", "format", "schedule", "cadence", "reach"],
    },
}

ADVANCED_PROMPT_MODES = {
    "Standard": {
        "description": "Clean GOAL prompt — no modification.",
        "prefix": "",
    },
    "Devil's Advocate": {
        "description": "Challenge the idea first, identify failure modes, then improve.",
        "prefix": "[DEVIL'S ADVOCATE MODE]\n\nBefore answering, challenge this request. Point out every way this approach could fail, backfire, or underperform. Be specific and honest. Then — having identified the weaknesses — provide the stronger version that addresses them.\n\n",
    },
    "Client Lens": {
        "description": "Respond as Avalon's ideal client — how does this content land for them?",
        "prefix": "[CLIENT LENS MODE]\n\nYou are Avalon Escapes' ideal client: a 35-year-old professional who values meaningful premium travel, has discretionary income, follows 20+ travel creators on Instagram, and is deciding whether to trust a boutique agency. Read this content with their exact eyes — what do they feel, doubt, or want more of?\n\n",
    },
    "Consult the Greats": {
        "description": "Evaluate through expert lenses — Ogilvy, behavioural economics, viral travel creators.",
        "prefix": "[CONSULT THE GREATS MODE]\n\nEvaluate this through four lenses: (1) David Ogilvy — is the headline clear, specific, and honest? (2) Rory Sutherland — what psychological mechanism is at play? (3) A viral travel creator — is the hook compressed enough to hold attention? (4) A boutique luxury founder — does this build long-term trust? Synthesise all four into ONE clear recommendation.\n\n",
    },
    "Back 2 The Future": {
        "description": "Imagine the content was already posted — analyse results, then rewrite.",
        "prefix": "[BACK 2 THE FUTURE MODE]\n\nImagine this content has already been posted on @avalon.escapes. Three weeks have passed. Tell me: Did it perform? What did the audience respond to? What fell flat? What would have made the biggest difference? Then provide the rewritten version based on those lessons.\n\n",
    },
    "Style Clone": {
        "description": "Write in Avalon's exact voice — personal, premium, not corporate.",
        "prefix": "[STYLE CLONE MODE]\n\nWrite entirely in the Avalon Escapes brand voice: premium but personal, short punchy stanzas, emotionally precise, specific sensory detail, ocean-influenced, founder-speaking-not-agency-selling. Do NOT copy exact words from reference creators. Write as if Rafa or Sofia is speaking from personal experience.\n\n",
    },
}

AVALON_CONTEXT_BLOCK = """Brand: Avalon Escapes — luxury travel agency and bespoke escape design studio.
Founders: Rafa (@_rafamagri, Brazilian, personal travel-lifestyle brand, ocean-obsessed) and Sofia (@sofiacollins311, freediver, ocean adventure specialist).
Brand account: @avalon.escapes (launched April 2026, early-stage).
Priority destinations: Maldives (Fuvahmulah diving), Colombia (Cartagena, Providencia), Brazil (Trancoso, Fernando de Noronha), Türkiye (Kaş, Cappadocia), Sri Lanka (tea hills, east coast, cultural triangle).
Voice: premium, elegant, warm, personal, authentic, emotionally intelligent, ocean-inspired, boutique, curated. NOT generic, NOT corporate, NOT mass-market.
Content style: narrative Reels, destination guide carousels, founder story posts, philosophical travel essays, trip invitation formats.
Viral reference group: 12 accounts — adapt trend structures, never copy captions, scripts, footage, or creator identity.
Marketing principles: copywriting (AIDA/PAS, benefits over features), CRO (keyword CTAs), content strategy (searchable + shareable), marketing psychology (JTBD, loss aversion)."""

PROMPT_TEMPLATES = [
    {
        "id": "improve_idea",
        "name": "Improve this content idea",
        "icon": "✨",
        "goal": "Improve this Instagram content idea for @avalon.escapes so it is more specific, more emotionally resonant, and more likely to drive DM inquiries.",
        "objective": "A stronger hook (under 8 words), a refined caption structure (100–130 words, short stanzas), and a specific keyword CTA. Preserve the emotional core.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nContent idea: [INSERT IDEA]\nFormat: [FORMAT]\nDestination: [DESTINATION]\nCurrent hook: [HOOK]",
        "layout": "Output: (1) Improved hook (2) Caption draft — short punchy stanzas (3) CTA (4) One sentence on what was strengthened.",
    },
    {
        "id": "weekly_plan",
        "name": "Generate a 7-day content plan",
        "icon": "📅",
        "goal": "Create a complete 7-day Avalon Escapes content plan that mixes formats and destinations, balancing brand awareness and DM inquiry generation.",
        "objective": "7 posts — minimum 3 Reels, 2 carousels, 1 photo, 1 Story. Each post covers a different destination or pillar. At least 2 designed for high save rate. At least 1 founder story.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nContent pillars available: Ocean & Island Adventures, Destination Guide, Founder Story, Luxury Escapes, Travel Philosophy, Viral Travel Inspiration, Tailor-Made Journeys.\nViral patterns available: curiosity-gap hook, keyword CTA, trip invitation, carousel guide, philosophical essay, expectation subversion.",
        "layout": "For each day: Day / Weekday / Format / Pillar / Destination / Idea (2 sentences) / Hook (1 line) / CTA / Status: Idea. Output as clean list.",
    },
    {
        "id": "analyze_trend",
        "name": "Analyse an influencer trend",
        "icon": "🔍",
        "goal": "Analyse a viral trend observed in the reference group and determine how Avalon can adapt it safely.",
        "objective": "Tier classification (1/2/3), pattern name, what NOT to copy, and a full Avalon adaptation with hook, visual direction, and CTA.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nTier definitions: Tier 1 = Direct Trend Adaptation (recreate with Avalon footage), Tier 2 = Structural Replication (use structure only), Tier 3 = Inspiration Only (too personal to copy).\n\nCreator post to analyse: [DESCRIBE THE POST STRUCTURE, HOOK, FORMAT — do not copy exact text]",
        "layout": "Output: (1) Pattern name (2) Tier + reasoning (3) What NOT to copy (4) Avalon adaptation: hook, visual direction, caption structure, CTA.",
    },
    {
        "id": "carousel_plan",
        "name": "Create a carousel",
        "icon": "📱",
        "goal": "Design a complete Instagram carousel for @avalon.escapes that maximises saves and drives DM inquiries.",
        "objective": "6–7 slides. First slide must stop the scroll and trigger a 'save this' instinct. Each slide has exactly one idea. Strong guide CTA on the last slide.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nCarousel type: [Guide / Narrative / Itinerary]\nDestination: [DESTINATION]\nMain topic: [TOPIC]\nReference: @travelcroats (PRIMARY CAROUSEL REFERENCE — slide sequencing, first-slide hooks, save/share triggers).",
        "layout": "Output: (1) First-slide hook (2) Slides 2–6/7 with headline + 1-sentence body (3) Final slide: Avalon brand + keyword CTA (4) Caption (2–3 lines + 'Save this →') (5) Save trigger explanation.",
    },
    {
        "id": "reel_script",
        "name": "Create a Reel script",
        "icon": "🎬",
        "goal": "Write a complete Reel brief for @avalon.escapes that drives strong watch-through rate and keyword CTA engagement.",
        "objective": "Hook under 8 words. Visual sequence with timestamps (60s). Caption 100–130 words. Keyword CTA. Tier label stated.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nReel concept: [INSERT CONCEPT]\nDestination: [DESTINATION]\nEmotion target: [e.g. awe + curiosity + FOMO]\nViral pattern: [e.g. curiosity-gap, expectation subversion, love declaration]",
        "layout": "Output: (1) Hook [max 8 words] (2) Visual sequence with timestamps [0–3s], [3–15s], [15–35s], [35–50s], [50–60s] (3) Caption [short punchy stanzas] (4) CTA [keyword-based] (5) Tier label + what NOT to copy.",
    },
    {
        "id": "rewrite_caption",
        "name": "Rewrite caption in Avalon voice",
        "icon": "🎤",
        "goal": "Rewrite a draft caption in the Avalon Escapes brand voice without losing the core message.",
        "objective": "Remove generic/corporate language. Add specificity and sensory detail. Preserve the emotional core. End with a clean CTA. Max 130 words.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nCaption to rewrite:\n[INSERT DRAFT CAPTION HERE]",
        "layout": "Output: (1) Rewritten caption (short punchy stanzas) (2) One sentence on the main change made (3) Optional alternative hook.",
    },
    {
        "id": "score_before_posting",
        "name": "Score content before posting",
        "icon": "📊",
        "goal": "Evaluate this content idea against Avalon's scoring rubric and professional marketing standards before it goes live.",
        "objective": "Score /100 with breakdown, identify 2–3 weakest areas, provide specific fixes for each, give a projected score after improvements.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nIdea: [INSERT IDEA]\nHook: [HOOK]\nCaption: [CAPTION]\nCTA: [CTA]\nFormat: [FORMAT]\nDestination: [DESTINATION]",
        "layout": "Output: (1) Overall score /100 (2) Breakdown by criterion (3) Top 2–3 weaknesses with specific fixes (4) Projected score after fixes.",
    },
    {
        "id": "why_fail",
        "name": "Identify why content may fail",
        "icon": "⚠️",
        "goal": "Identify every reason this content idea might underperform before it is created or posted.",
        "objective": "3–5 specific failure risks, each with a concrete fix. Output should make the final version meaningfully stronger.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nContent idea: [INSERT IDEA AND HOOK]",
        "layout": "Output: For each risk — (1) Failure mode (2) Why it happens (3) Specific fix. Then one paragraph on the stronger version.",
    },
    {
        "id": "client_facing_content",
        "name": "Create client-facing travel content",
        "icon": "✈️",
        "goal": "Create a client-facing piece of travel content for Avalon Escapes — could be a DM response, proposal section, itinerary description, or email copy.",
        "objective": "Warm, personal, specific, premium. Sounds like Rafa or Sofia speaking — not a template. Builds trust and desire simultaneously.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nContent type: [DM response / proposal / itinerary / email]\nDestination: [DESTINATION]\nClient context: [e.g. honeymoon, first luxury trip, ocean adventure, cultural immersion]\nTone: conversational and premium",
        "layout": "Output: (1) Draft copy (2) Tone notes: what makes this feel personal vs generic.",
    },
    {
        "id": "turn_trend_into_avalon",
        "name": "Turn influencer pattern into Avalon content",
        "icon": "🔄",
        "goal": "Take a viral influencer content pattern and transform it fully into Avalon's voice, destinations, and brand angle.",
        "objective": "A complete Avalon post: hook, visual brief, caption draft, CTA — that uses the pattern's structure but contains NONE of the original creator's words, footage, identity, or personal story.",
        "assets": AVALON_CONTEXT_BLOCK + "\n\nPattern to adapt: [PATTERN NAME AND DESCRIPTION]\nOriginal creator: [CREATOR HANDLE]\nTier: [1 / 2 / 3]\nAvalon destination to apply it to: [DESTINATION]",
        "layout": "Output: (1) Hook [adapted] (2) Visual direction [original] (3) Caption draft [short stanzas] (4) CTA (5) What NOT to copy note.",
    },
]

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
            "account_id":       account_id,
            "group":            "founder_brand",
            "label":            meta.get("label", account_id),
            "username":         meta.get("username", ""),
            "post_id":          p.get("post_id"),
            "post_url":         p.get("post_url"),
            "date":             (p.get("timestamp") or "")[:10],
            "type":             p.get("type") or "Unknown",
            "product_type":     p.get("product_type") or "unknown",
            "caption":          (p.get("caption") or "").strip(),
            "hashtags":         p.get("hashtags", []),
            "likes":            likes,
            "comments":         p.get("comments_count"),
            "video_views":      p.get("video_view_count"),
            "video_plays":      p.get("video_play_count"),
            "duration_sec":     p.get("video_duration_sec"),
            "location":         p.get("location_name"),
            "relative_score":   None,  # computed below
            # Optional fields — populated from analytics CSV or richer Apify data when available
            "saves":            p.get("savesCount") or p.get("saves"),
            "shares":           p.get("sharesCount") or p.get("shares"),
            "reach":            p.get("reach"),
            "impressions":      p.get("impressions"),
            "engagement_rate":  p.get("engagement_rate"),
            "carousel_slides":  len(p.get("childPosts") or []) or p.get("carousel_slide_count") or None,
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
            "account_id":      p.get("username", ""),
            "group":           "viral_reference_group",
            "label":           f"@{p.get('username','')}",
            "username":        f"@{p.get('username','')}",
            "post_id":         p.get("post_id"),
            "post_url":        p.get("post_url"),
            "date":            p.get("date",""),
            "type":            p.get("type") or "Unknown",
            "product_type":    p.get("product_type") or "unknown",
            "caption":         (p.get("caption") or "").strip(),
            "hashtags":        p.get("hashtags", []),
            "likes":           likes,
            "comments":        p.get("comments"),
            "video_views":     p.get("video_views"),
            "video_plays":     p.get("video_plays"),
            "duration_sec":    p.get("video_duration_sec"),
            "location":        p.get("location"),
            "relative_score":  p.get("relative_score"),
            # Optional fields — None unless available in processed data or analytics CSV
            "saves":           p.get("saves"),
            "shares":          p.get("shares"),
            "reach":           p.get("reach"),
            "impressions":     p.get("impressions"),
            "engagement_rate": p.get("engagement_rate"),
            "carousel_slides": p.get("carousel_slide_count") or len(p.get("child_posts") or []) or None,
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

def format_adjusted_performance_score(post: dict):
    """
    Format-aware performance score. Uses relative_score as base, then applies
    format-specific weights and quality signals from available data.

    PUBLIC DATA LIMITATION: shares, saves, reach, and impressions are NOT available
    from Instagram public scraping. When None, falls back to relative_score + text-based
    signals. Add analytics CSVs to data/analytics/ to unlock the full score.

    Reel   — plays-heavy base; comment depth + saves/shares bonuses
    Carousel — guide/list text signals; very high bonus when saves/shares available
    Photo  — caption emotional depth; saves/shares bonus when available
    """
    relative = post.get("relative_score")
    if relative is None:
        return None

    fmt      = (post.get("product_type") or post.get("type") or "").lower()
    caption  = (post.get("caption") or "").lower()
    saves    = post.get("saves") or 0
    shares   = post.get("shares") or 0
    likes    = post.get("likes") or 0
    comments = post.get("comments") or 0

    is_reel     = any(x in fmt for x in ["video", "clips", "reel"])
    is_carousel = any(x in fmt for x in ["sidecar", "carousel", "album"])

    bonus = 0.0

    if is_reel:
        if saves > 0 and likes > 0:
            bonus += min(0.4, (saves / likes) * 1.5)
        if shares > 0 and likes > 0:
            bonus += min(0.4, (shares / likes) * 1.5)
        if likes > 0 and comments > 0 and (comments / likes) > 0.03:
            bonus += 0.15  # deep comment engagement

    elif is_carousel:
        guide_kws = ["guide", "tips", "save this", "save for", "things to", "how to",
                     "itinerary", "best", "top", "places", "spots", "hotels",
                     "what to", "must", "list", "number"]
        bonus += min(0.25, sum(1 for kw in guide_kws if kw in caption) * 0.07)
        first_line = caption.split("\n")[0] if caption else ""
        if 0 < len(first_line) <= 70:
            bonus += 0.08  # short punchy first slide
        if saves > 0 and likes > 0:
            bonus += min(0.7, (saves / likes) * 3.0)
        if shares > 0 and likes > 0:
            bonus += min(0.5, (shares / likes) * 2.5)

    else:  # Photo / Image
        if len(caption) > 300:
            bonus += 0.08
        emo_kws = ["feel", "alive", "connection", "meaning", "soul", "heart",
                   "changed", "beauty", "wonder", "grateful", "moment",
                   "memory", "human", "love", "peace"]
        bonus += min(0.15, sum(1 for kw in emo_kws if kw in caption) * 0.04)
        if saves > 0 and likes > 0:
            bonus += min(0.4, (saves / likes) * 2.0)
        if shares > 0 and likes > 0:
            bonus += min(0.4, (shares / likes) * 2.0)

    return round(relative * (1.0 + bonus), 2)


def posts_to_df(posts):
    if not posts:
        return pd.DataFrame()
    rows = []
    for p in posts:
        row = {
            "Account":        p.get("label",""),
            "Group":          p.get("group",""),
            "Date":           p.get("date",""),
            "Type":           p.get("product_type","").capitalize(),
            "Caption":        truncate(p.get("caption",""), 90),
            "Likes":          p.get("likes"),
            "Comments":       p.get("comments"),
            "Plays":          p.get("video_plays"),
            "Views":          p.get("video_views"),
            "Relative Score": p.get("relative_score"),
            "Adj. Score":     format_adjusted_performance_score(p),
            "Duration (s)":   p.get("duration_sec"),
            "Pillar":         infer_pillar(p.get("caption","")),
            "Destination":    infer_destination(p.get("caption","")),
            "Hook Type":      infer_hook_type(p.get("caption","")),
            "Tier (est.)":    infer_tier(p),
            "URL":            p.get("post_url",""),
        }
        # Optional fields — only include column when at least something is present
        for opt_field, col_name in [
            ("saves",           "Saves"),
            ("shares",          "Shares"),
            ("reach",           "Reach"),
            ("impressions",     "Impressions"),
            ("engagement_rate", "Eng. Rate"),
            ("carousel_slides", "Slides"),
        ]:
            v = p.get(opt_field)
            if v is not None:
                row[col_name] = v
        rows.append(row)
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

def score_format(fmt: str, caption: str, idea: str = "") -> tuple[int, str]:
    """Max 5 pts. Format-aware: Reel / Carousel / Photo each scored on different criteria."""
    fmt_l = (fmt or "").lower()
    cap   = (caption or idea or "").lower()

    is_reel     = any(x in fmt_l for x in ["reel", "video"])
    is_carousel = any(x in fmt_l for x in ["carousel"])
    is_photo    = any(x in fmt_l for x in ["photo", "image", "static"])

    if is_reel:
        if len(cap) > 50:
            return 5, "Reel + developed caption/script ✓ — prioritise plays, comment depth, saves"
        return 4, "Reel — add hook/caption detail; plays + comment depth are the key signals"

    if is_carousel:
        guide_kws = ["guide","tips","save","list","things to","how to","itinerary",
                     "best","top","spots","places","number","must","step"]
        if any(kw in cap for kw in guide_kws):
            return 5, "Carousel + guide/list content = strong save/share potential ✓"
        first = cap.split("\n")[0] if cap else ""
        if len(first) < 80:
            return 4, "Carousel + short first-slide hook ✓ — add guide/list value to maximise saves"
        return 3, "Carousel — add numbered list, itinerary, or tips format to trigger saves (carousel's most valuable metric)"

    if is_photo:
        if len(cap) < 150:
            return 5, "Photo + concise caption ✓"
        if len(cap) > 300:
            return 4, "Photo + long caption — works when the visual is strong; check emotional resonance"
        return 5, "Photo + caption ✓"

    return 3, "Specify format (Reel / Carousel / Photo) for format-specific scoring"

def _crit_max(criterion: str, default: int = 10) -> int:
    """Safely extract the max score from a criterion label like 'Hook Strength (20)'."""
    m = re.search(r'\((\d+)\)', criterion)
    return int(m.group(1)) if m else default


def run_scoring(idea, destination, fmt, emotion, hook, caption, cta, tier):
    """Run all 8 scoring criteria. Returns dict of scores and notes."""
    s1, n1 = score_hook(hook, idea)
    s2, n2 = score_specificity(caption or idea, destination)
    s3, n3 = score_emotional_arc(caption, idea)
    s4, n4 = score_brand_fit(caption, idea, emotion)
    s5, n5 = score_shareability(caption, idea)
    s6, n6 = score_cta(cta)
    s7, n7 = score_adaptation(tier)
    s8, n8 = score_format(fmt, caption, idea)
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
# REFERENCE GROUP HELPERS  (creator metadata + stats + strength scoring)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_creator_config() -> dict:
    """Load reference_creators.json and return a dict keyed by instagram_username."""
    cfg_path = ROOT / "config" / "reference_creators.json"
    raw = safe_load_json(cfg_path)
    if not raw:
        return {}
    accounts = raw.get("viral_reference_group", {}).get("accounts", [])
    return {a["instagram_username"]: a for a in accounts}

@st.cache_data(show_spinner=False)
def compute_creator_stats() -> dict:
    """Compute per-creator engagement stats from group_posts.json."""
    ref_posts = load_reference_posts()
    if not ref_posts:
        return {}
    stats: dict = {}
    for p in ref_posts:
        uid = p.get("account_id", "")
        if not uid:
            continue
        if uid not in stats:
            stats[uid] = {"total": 0, "viral": 0, "high": 0, "scores": [], "formats": {}}
        score = p.get("relative_score")
        stats[uid]["total"] += 1
        if score:
            stats[uid]["scores"].append(score)
            if score >= 3.0:
                stats[uid]["viral"] += 1
            elif score >= 2.0:
                stats[uid]["high"] += 1
        fmt = (p.get("product_type") or "unknown").lower()
        stats[uid]["formats"][fmt] = stats[uid]["formats"].get(fmt, 0) + 1
    for uid, d in stats.items():
        d["avg_score"] = statistics.mean(d["scores"]) if d["scores"] else 1.0
        d["top_format"] = max(d["formats"], key=d["formats"].get) if d["formats"] else "—"
    return stats

def _follower_authority(follower_count) -> float:
    """Log-normalize follower count to 0–100. 1M = 100. None → 50 (mid default)."""
    import math
    if not follower_count or follower_count <= 0:
        return 50.0
    return min(100.0, math.log10(max(1, follower_count)) / math.log10(1_000_000) * 100)

def compute_reference_strength(username: str, stats: dict, creator_cfgs: dict) -> int:
    """
    0–100 score:  viral performance 35% + follower authority 25%
                  + Avalon fit 25%   + replicability 15%
    """
    s   = stats.get(username, {})
    cfg = creator_cfgs.get(username, {})
    viral_perf    = min(100.0, s.get("avg_score", 1.0) * 20)
    follower_auth = _follower_authority(cfg.get("follower_count"))
    avalon_fit    = float(cfg.get("avalon_fit_score", 70))
    total_posts   = s.get("total", 0)
    viral_posts   = s.get("viral", 0) + s.get("high", 0)
    replicability = (viral_posts / total_posts * 100) if total_posts > 0 else 50.0
    raw = viral_perf * 0.35 + follower_auth * 0.25 + avalon_fit * 0.25 + replicability * 0.15
    return min(100, max(0, int(raw)))

# ─────────────────────────────────────────────────────────────────────────────
# PATTERN MATCHING ENGINE  (rule-based, no API)
# ─────────────────────────────────────────────────────────────────────────────
def match_patterns_for_improvement(full_text: str) -> list:
    """Match user input against VIRAL_PATTERNS. Returns top-4 sorted by keyword hits + Avalon fit."""
    if not full_text:
        return []
    low = full_text.lower()
    matches = []
    for p in VIRAL_PATTERNS:
        score = sum(1 for kw in p["keywords"] if kw in low)
        if score > 0:
            matches.append((p, score))
    matches.sort(key=lambda x: (x[1], x[0]["avalon_fit"]), reverse=True)
    return matches[:4]

def _fill(template: str, destination: str) -> str:
    """Fill [DESTINATION] placeholder in a template string."""
    dest = (destination or "").strip().split(",")[0].strip() or "this destination"
    return template.replace("[DESTINATION]", dest).replace("[MONTH]", "this season")

# ─────────────────────────────────────────────────────────────────────────────
# IMPROVEMENT GENERATOR  (rule-based, no API, driven by pattern matches)
# ─────────────────────────────────────────────────────────────────────────────
def generate_improvement(idea, hook, caption, destination, fmt, emotion, cta, tier) -> dict:
    """
    Generate reference-based improvement suggestions.
    Returns: matched_patterns, relevant_creators, hooks (5), caption_guide,
             reel_structure, ctas (3), hashtags, warnings, projected_score.
    """
    full_text = " ".join(filter(None, [idea, hook, caption, destination, emotion]))
    matched   = match_patterns_for_improvement(full_text)
    creator_cfgs  = load_creator_config()
    creator_stats = compute_creator_stats()

    # ── Relevant creators ─────────────────────────────────────────────────────
    creator_freq: dict = {}
    for pattern, _ in matched:
        for uname in pattern["accounts"]:
            creator_freq[uname] = creator_freq.get(uname, 0) + 1

    relevant_creators = []
    for uname, _ in sorted(creator_freq.items(), key=lambda x: x[1], reverse=True)[:4]:
        cfg = creator_cfgs.get(uname, {})
        s   = creator_stats.get(uname, {})
        creator_patterns = [p for p, _ in matched if uname in p["accounts"]]
        if not creator_patterns:
            continue
        best = creator_patterns[0]
        relevant_creators.append({
            "handle":         f"@{uname}",
            "follower_count": cfg.get("follower_count"),
            "niche":          cfg.get("niche", ""),
            "why_relevant":   cfg.get("why_relevant_to_avalon", ""),
            "pattern_name":   best["name"],
            "tier_label":     best["tier_label"],
            "tier":           best["tier"],
            "posts_analyzed": s.get("total", 0),
            "viral_posts":    s.get("viral", 0),
            "ref_strength":   compute_reference_strength(uname, creator_stats, creator_cfgs),
        })

    # ── Generate 5 hooks ──────────────────────────────────────────────────────
    dest  = (destination or "").strip()
    hooks: list = []
    seen: set   = set()
    for pattern, _ in matched:
        for tmpl in pattern["hook_templates"]:
            h = _fill(tmpl, dest)
            if h not in seen:
                hooks.append({"text": h, "pattern": pattern["name"], "tier": pattern["tier_label"], "tier_num": pattern["tier"]})
                seen.add(h)
    fallbacks = [
        {"text": f"No one tells you the real side of {dest or 'this destination'}.", "pattern": "Curiosity-Gap Hook", "tier": "Tier 2 — Structural Replication", "tier_num": 2},
        {"text": f"{dest or 'This destination'} completely rewrote every expectation I had.", "pattern": "Expectation Subversion", "tier": "Tier 2 — Structural Replication", "tier_num": 2},
        {"text": f"The {dest or 'trip'} they show you. And the one that actually changes you.", "pattern": "Expectation Subversion", "tier": "Tier 2 — Structural Replication", "tier_num": 2},
        {"text": f"Comment '{re.sub(r'[^A-Z]','',dest.upper())[:6] or 'ESCAPE'}' and we'll design your escape.", "pattern": "Keyword CTA", "tier": "Tier 1 — Direct Trend Adaptation", "tier_num": 1},
        {"text": "What they don't teach you: time is the real luxury. Not hotels.", "pattern": "Society Challenge", "tier": "Tier 2 — Structural Replication", "tier_num": 2},
    ]
    for fb in fallbacks:
        if len(hooks) >= 5:
            break
        if fb["text"] not in seen:
            hooks.append(fb)
    hooks = hooks[:5]

    # ── Caption structure guide ────────────────────────────────────────────────
    if matched:
        best = matched[0][0]
        caption_guide = {"structure": best["caption_structure"], "visual": best["visual_direction"], "pattern_used": best["name"]}
    else:
        caption_guide = {
            "structure": "Opening hook → specific sensory detail → emotional shift → universal insight → CTA",
            "visual":    "Open strong — lead with your most compelling shot, not a setup shot.",
            "pattern_used": "General Avalon formula",
        }

    # ── Reel structure ─────────────────────────────────────────────────────────
    _reel_structures = {
        "curiosity_gap":         "[0–3s]  Hook: state the gap — what no one tells you\n[3–15s] Setup: show the conventional / expected version\n[15–35s] Reveal: cut to the unexpected reality only Avalon knows\n[35–50s] Insight: one line that transcends the destination\n[50–60s] CTA: comment/DM keyword",
        "philosophical_essay":   "[0–3s]  Hook: universal observation, one sentence\n[3–20s] Tension: 3–5 short parallel lines (things people accept)\n[20–40s] The turn: one specific personal moment that breaks the tension\n[40–55s] Insight: the universal truth it reveals\n[55–60s] Quiet closing shot + keyword CTA",
        "love_declaration":      "[0–2s]  Destination name + flag — confident, no explanation needed\n[2–20s] The specific detail most tourists never see\n[20–40s] What this means for someone traveling with Avalon\n[40–60s] CTA: join us / comment for the guide",
        "trip_invitation":       "[0–3s]  Hook: announce the trip + destination\n[3–15s] What makes this route different from anything on the market\n[15–35s] Who it's for + what they'll actually experience\n[35–50s] Founders on camera with personal direct invitation\n[50–60s] Limited spots CTA + keyword",
        "expectation_subversion": "[0–3s]  State the misconception most people have\n[3–15s] Setup: the cliché version\n[15–35s] Hard cut to the real version Avalon knows\n[35–50s] The emotional shift — what changed\n[50–60s] Invitation + CTA",
        "founder_personality":   "[0–3s]  Hook: reveal the personality clash\n[3–20s] Rafa's perspective (on camera)\n[20–35s] Sofia's perspective (on camera)\n[35–50s] The result: what Avalon clients get from both\n[50–60s] Pick a side CTA",
        "underrated_destination": "[0–3s]  Hook: nobody talks about this side of [DESTINATION]\n[3–15s] The tourist cliché — what everyone already knows\n[15–40s] The real version — footage only insiders have\n[40–55s] Why this changes the trip entirely\n[55–60s] Comment CTA: DM for the insider guide",
    }
    top_id = matched[0][0]["id"] if matched else "curiosity_gap"
    reel_struct = _reel_structures.get(top_id, _reel_structures["curiosity_gap"])

    # ── 3 CTAs ────────────────────────────────────────────────────────────────
    dest_slug = re.sub(r'[^A-Z]', '', dest.upper())[:8] or "ESCAPE"
    ctas = [
        f"Comment '{dest_slug}' and we'll send you our complete guide — hotels, routes, and the things only we know. →",
        f"DM us 'AVALON' and we'll design your {dest or 'escape'} this month.",
        f"Tag someone who needs this trip. 🌊",
    ]

    # ── Hashtag set ────────────────────────────────────────────────────────────
    detected_dest = infer_destination(full_text)
    hashtags = DESTINATION_HASHTAGS.get(detected_dest, DESTINATION_HASHTAGS["Global / Curated Escapes"])

    # ── What NOT to copy ──────────────────────────────────────────────────────
    warnings = []
    for pattern, _ in matched:
        if pattern.get("what_not_to_copy"):
            warnings.append({"pattern": pattern["name"], "warning": pattern["what_not_to_copy"]})
    if not warnings:
        warnings.append({"pattern": "General rule", "warning": "Always transform reference content into Avalon's own voice, footage, destinations, and brand angle. Never copy exact captions, scripts, personal stories, or signature phrases."})

    # ── Projected score (run scorer with improved hook) ───────────────────────
    proj_hook    = hooks[0]["text"] if hooks else hook
    proj_caption = caption or idea or ""
    proj_result  = run_scoring(idea, destination, fmt, emotion, proj_hook, proj_caption, ctas[0], tier)

    # ── Format-specific advice ─────────────────────────────────────────────────
    format_advice = generate_format_advice(fmt, idea, destination, emotion, hooks)

    return {
        "matched_patterns":   matched,
        "relevant_creators":  relevant_creators,
        "hooks":              hooks,
        "caption_guide":      caption_guide,
        "reel_structure":     reel_struct,
        "ctas":               ctas,
        "hashtags":           hashtags,
        "warnings":           warnings,
        "projected_score":    proj_result["total"],
        "format_advice":      format_advice,
    }

# ─────────────────────────────────────────────────────────────────────────────
# FORMAT-SPECIFIC IMPROVEMENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def generate_carousel_plan(idea: str, destination: str, emotion: str) -> dict:
    """Slide-by-slide carousel plan. Detects guide vs narrative type from the idea text."""
    dest     = (destination or "this destination").strip().split(",")[0].strip()
    idea_low = (idea or "").lower()
    is_guide = any(kw in idea_low for kw in [
        "guide", "tips", "things to", "how to", "itinerary", "best", "top", "list", "spots", "places"
    ])

    if is_guide:
        slides = [
            f"Slide 1 (Hook) — Short bold curiosity-gap headline: '[Number] things about {dest} most people never discover' — saves start here",
            "Slide 2 — Lead with your strongest, most surprising detail (don't save the best for last)",
            "Slide 3 — Second insight — visual-heavy, one idea per slide, minimal text",
            "Slide 4 — Third insight — make this feel essential, not optional",
            "Slide 5 — Fourth insight — this is where save rates peak; deliver something truly specific",
            f"Slide 6 — A short personal note from Rafa or Sofia about {dest}",
            f"Slide 7 (Close) — 'Avalon designs custom {dest} escapes. Comment '{dest.upper()[:6]}' to start yours.'",
        ]
        save_trigger  = f"Numbered guide + specific destination = high save rate. People bookmark it as a pre-trip reference for {dest}."
        share_trigger = f"Slide 1 should make people think 'I need to send this to [person going to {dest}]'. The curiosity-gap headline is the share trigger."
        caption_angle = f"Short 1–2 line intro + 'Save this for your {dest} trip →' CTA. Do not write the whole guide in the caption — the slides carry it."
        why_works     = f"Guide carousels score high on saves, which signals Instagram to push them harder. The numbered hook also doubles as a Reel hook if repurposed."
        slide_count   = 7
        carousel_type = "Guide Carousel"
    else:
        slides = [
            f"Slide 1 (Hook) — One short powerful statement about {dest}. No explanation. Creates curiosity.",
            f"Slide 2 — The setup: what most people expect or know about {dest}",
            f"Slide 3 — The unexpected reality: what Avalon actually knows (visual + short caption)",
            "Slide 4 — The emotional moment or shift — slower, more personal",
            "Slide 5 — The universal insight: what this reveals about travel in general",
            f"Slide 6 (Close) — Avalon's connection to {dest} + keyword CTA",
        ]
        save_trigger  = "A strong universal insight on slide 5–6 drives saves. People save it to revisit the feeling or share the last slide standalone."
        share_trigger = "Slide 1 must make the viewer think 'I need to send this to someone'. The hook is the share trigger — not the destination name."
        caption_angle = f"2–3 lines that tease the arc. End with 'Swipe to see what we found →' or 'Save this before your {dest} trip.'"
        why_works     = f"Narrative carousels work when each slide has exactly one idea and the last slide lands hard. Swipe-through rate drops after slide 3 — make slides 3–5 count."
        slide_count   = 6
        carousel_type = "Narrative Carousel"

    dest_slug = re.sub(r'[^A-Z]', '', dest.upper())[:8] or "ESCAPE"
    return {
        "type":              carousel_type,
        "slide_count":       slide_count,
        "slides":            slides,
        "first_slide_hook":  slides[0],
        "save_trigger":      save_trigger,
        "share_trigger":     share_trigger,
        "caption_angle":     caption_angle,
        "cta":               f"Comment '{dest_slug}' for our full {dest} guide →" if is_guide else f"DM us 'AVALON' and we'll design your {dest} escape →",
        "why_it_works":      why_works,
        "travelcroats_note": "Study @travelcroats — the primary carousel reference in the group — for slide sequencing, first-slide hooks, guide CTAs, and save/share triggers.",
    }


def generate_format_advice(fmt: str, idea: str, destination: str, emotion: str, hooks: list) -> dict:
    """Generate format-specific improvement advice for the simulator."""
    fmt_l   = (fmt or "").lower()
    dest    = (destination or "this destination").strip().split(",")[0].strip()
    is_reel = any(x in fmt_l for x in ["reel", "video", "story"])
    is_car  = "carousel" in fmt_l
    is_photo= any(x in fmt_l for x in ["photo", "image", "static"])

    if is_reel:
        h3s = hooks[0]["text"] if hooks else f"No one tells you the real side of {dest}."
        return {
            "format": "Reel",
            "first_3s_hook":   h3s,
            "visual_sequence": (
                f"[0–3s]  Hook shot — the one frame that stops the scroll\n"
                f"[3–10s] Setup: show the conventional expectation of {dest}\n"
                f"[10–25s] The reveal: Avalon's real version\n"
                f"[25–45s] Emotional turn — slow the pacing here\n"
                f"[45–60s] CTA overlay on a clean final shot"
            ),
            "text_overlay":  "On-screen text for the hook only (first 3s). Max 4 words per overlay. Then let visuals + audio carry it.",
            "pacing":         "Cuts every 2–3s in the hook. Slow to 5–7s cuts in the emotional middle. End on a still or very slow shot.",
            "audio_angle":    "Trending audio for Tier 1 formats. Original audio or calm instrumental for Tier 2 narrative Reels to keep the premium feel.",
            "share_trigger":  "The hook makes people tag someone. The last 10 seconds closes the emotional loop that drives saves.",
            "key_metric":     "Plays / views are the primary signal. Comment depth (comments/likes ratio) indicates resonance.",
        }
    elif is_car:
        return {"format": "Carousel", "carousel_plan": generate_carousel_plan(idea, destination, emotion)}
    elif is_photo:
        return {
            "format": "Photo",
            "caption_angle":          f"Long caption if the image is simple. Short caption if the image is extraordinary. They should answer different questions about {dest}.",
            "emotional_framing":      "What feeling does this image create in the first second? Start the caption from that feeling — not from the destination's name.",
            "visual_caption_pairing": "The image shows the where. The caption explains the why. If both tell the same story, one of them is redundant.",
            "comment_prompt":         "End with a question that requires a personal answer: 'What does this remind you of?' or 'Would you stay here?' or 'Tag the person you'd bring.'",
            "key_metric":             "Likes + comments are primary. Caption emotional depth drives saves and shares when available.",
        }
    return {"format": fmt or "Unknown", "note": "Select Reel, Carousel, or Photo for format-specific advice."}


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY CALENDAR HELPERS
# ─────────────────────────────────────────────────────────────────────────────
_WC_FIELDS = ["format", "content_pillar", "destination_package", "idea", "hook",
              "visual_plan", "caption", "cta", "hashtags", "status", "notes"]

def _wc_key(day_idx: int, field: str) -> str:
    return f"wc_{day_idx}_{field}"

def _default_day(i: int) -> dict:
    return {
        "day": f"Day {i + 1}", "weekday": WEEKDAYS[i],
        "format": "", "content_pillar": "", "destination_package": "",
        "idea": "", "hook": "", "visual_plan": "", "caption": "",
        "cta": "", "hashtags": "", "status": "Idea", "notes": "",
    }

def default_weekly_calendar() -> dict:
    return {"week_label": "Current Week", "days": [_default_day(i) for i in range(7)]}

def _load_wc_json() -> dict:
    try:
        if WEEKLY_CALENDAR_FILE.exists():
            return json.loads(WEEKLY_CALENDAR_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default_weekly_calendar()

def _wc_save_json(data: dict):
    CONTENT_PLANS.mkdir(parents=True, exist_ok=True)
    WEEKLY_CALENDAR_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

def _sanitise_day(raw: dict, i: int) -> dict:
    pillar_opts = [""] + list(CONTENT_PILLARS.keys())
    fmt    = raw.get("format", "")
    pillar = raw.get("content_pillar", "")
    dest   = raw.get("destination_package", "")
    status = raw.get("status", "Idea")
    return {
        "format":             fmt    if fmt    in CONTENT_FORMATS   else "",
        "content_pillar":     pillar if pillar in pillar_opts       else "",
        "destination_package":dest   if dest   in DESTINATIONS_LIST else "",
        "idea":               raw.get("idea",        ""),
        "hook":               raw.get("hook",        ""),
        "visual_plan":        raw.get("visual_plan", ""),
        "caption":            raw.get("caption",     ""),
        "cta":                raw.get("cta",         ""),
        "hashtags":           raw.get("hashtags",    ""),
        "status":             status if status in POST_STATUSES else "Idea",
        "notes":              raw.get("notes",       ""),
    }

def _wc_write_day_to_state(i: int, day: dict):
    clean = _sanitise_day(day, i)
    for field in _WC_FIELDS:
        st.session_state[_wc_key(i, field)] = clean[field]

def _ensure_wc_state():
    if _wc_key(0, "idea") not in st.session_state:
        data = _load_wc_json()
        days = data.get("days", [])
        for i in range(7):
            _wc_write_day_to_state(i, days[i] if i < len(days) else {})
        st.session_state["wc_week_label"] = data.get("week_label", "Current Week")

def _wc_load_sample():
    for i, sample in enumerate(SAMPLE_AVALON_WEEK):
        _wc_write_day_to_state(i, sample)
    st.session_state["wc_week_label"] = "Sample Avalon Week"

def _wc_load_defaults():
    for i in range(7):
        _wc_write_day_to_state(i, {})
    st.session_state["wc_week_label"] = "Current Week"

def _wc_collect() -> dict:
    days = []
    for i in range(7):
        day = {"day": f"Day {i + 1}", "weekday": WEEKDAYS[i]}
        for field in _WC_FIELDS:
            day[field] = st.session_state.get(_wc_key(i, field), "")
        days.append(day)
    return {"week_label": st.session_state.get("wc_week_label", "Current Week"), "days": days}

def _wc_overview() -> dict:
    ideas    = [st.session_state.get(_wc_key(i, "idea"),        "") for i in range(7)]
    statuses = [st.session_state.get(_wc_key(i, "status"),      "") for i in range(7)]
    pillars  = [st.session_state.get(_wc_key(i, "content_pillar"), "") for i in range(7)]
    dests    = [st.session_state.get(_wc_key(i, "destination_package"), "") for i in range(7)]

    planned = sum(1 for v in ideas if v.strip())
    empty   = 7 - planned
    ready   = statuses.count("Ready")
    draft   = statuses.count("Draft")
    p_counts = {}
    for p in pillars:
        if p: p_counts[p] = p_counts.get(p, 0) + 1
    d_counts = {}
    for d in dests:
        if d: d_counts[d] = d_counts.get(d, 0) + 1
    return {
        "planned":    planned,
        "empty":      empty,
        "ready":      ready,
        "draft":      draft,
        "top_pillar": max(p_counts, key=p_counts.get) if p_counts else "—",
        "top_dest":   max(d_counts, key=d_counts.get) if d_counts else "—",
    }

def _wc_export_markdown() -> str:
    lines = [
        "# Avalon Escapes — Weekly Content Plan\n",
        f"**Week:** {st.session_state.get('wc_week_label', 'Current Week')}  ",
        f"**Exported:** {datetime.now().strftime('%Y-%m-%d')}\n",
        "---\n",
    ]
    field_labels = [
        ("format",               "Format"),
        ("content_pillar",       "Pillar"),
        ("destination_package",  "Destination"),
        ("idea",                 "Idea"),
        ("hook",                 "Hook"),
        ("visual_plan",          "Visual Plan"),
        ("caption",              "Caption"),
        ("cta",                  "CTA"),
        ("hashtags",             "Hashtags"),
        ("status",               "Status"),
        ("notes",                "Notes"),
    ]
    for i in range(7):
        lines.append(f"## Day {i + 1} / {WEEKDAYS[i]}\n")
        for field, label in field_labels:
            val = st.session_state.get(_wc_key(i, field), "") or "—"
            if field == "caption":
                indented = val.replace("\n", "\n  ")
                lines.append(f"- **{label}:**\n\n  {indented}\n")
            else:
                lines.append(f"- **{label}:** {val}")
        lines.append("\n---\n")
    return "\n".join(lines)

def _render_wc_day(i: int):
    weekday  = WEEKDAYS[i]
    day_num  = i + 1
    status_v = st.session_state.get(_wc_key(i, "status"), "Idea")
    s_col, s_bg = _STATUS_STYLE.get(status_v, ("#64748b", "#1e2a3a"))

    st.markdown(
        f"<div style='background:#0d1117;border:1.5px solid #1e293b;border-radius:12px;"
        f"padding:.55rem 1rem;margin-bottom:.75rem;display:flex;"
        f"justify-content:space-between;align-items:center'>"
        f"<span style='font-size:1.02rem;font-weight:700;color:#e2e8f0'>"
        f"Day {day_num} — {weekday}</span>"
        f"<span style='font-size:.73rem;font-weight:700;color:{s_col};"
        f"background:{s_bg};padding:.16rem .55rem;border-radius:20px;"
        f"border:1px solid {s_col}55'>{status_v}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Row 1: format + pillar
    fa_col, pi_col = st.columns(2)
    with fa_col:
        st.selectbox("Format", CONTENT_FORMATS, key=_wc_key(i, "format"))
    with pi_col:
        pillar_opts = [""] + list(CONTENT_PILLARS.keys())
        st.selectbox("Content pillar", pillar_opts, key=_wc_key(i, "content_pillar"))

    # Destination
    st.selectbox("Destination / Package", DESTINATIONS_LIST, key=_wc_key(i, "destination_package"))

    # Text inputs
    st.text_input("Content idea / concept", key=_wc_key(i, "idea"),
                  placeholder="What is this post about?")
    st.text_input("Hook — first line or first 3 seconds", key=_wc_key(i, "hook"),
                  placeholder="The opening line that stops the scroll...")
    st.text_input("Visual plan", key=_wc_key(i, "visual_plan"),
                  placeholder="Shots, slides, or scenes...")
    st.text_area("Caption draft", key=_wc_key(i, "caption"), height=110,
                 placeholder="Draft your caption here...")

    cta_col, ht_col = st.columns(2)
    with cta_col:
        st.text_input("CTA", key=_wc_key(i, "cta"),
                      placeholder="Comment 'WORD' / DM 'AVALON'...")
    with ht_col:
        st.text_input("Hashtags", key=_wc_key(i, "hashtags"),
                      placeholder="#maldives #luxurytravel...")

    st.selectbox("Status", POST_STATUSES, key=_wc_key(i, "status"))
    st.text_input("Notes (internal)", key=_wc_key(i, "notes"),
                  placeholder="Internal reminders, feedback, or ideas...")

    # Format hint
    fmt_now = st.session_state.get(_wc_key(i, "format"), "")
    if fmt_now and fmt_now in FORMAT_HINTS:
        st.markdown(
            f"<div style='background:#0f1f35;border-left:3px solid #0369a1;border-radius:0 6px 6px 0;"
            f"padding:.38rem .8rem;margin:.25rem 0 .15rem;font-size:.8rem;color:#7dd3fc'>"
            f"{FORMAT_HINTS[fmt_now]}</div>",
            unsafe_allow_html=True,
        )

    # Simulator link hint
    idea_now = st.session_state.get(_wc_key(i, "idea"), "")
    if idea_now.strip():
        st.caption("📊 _Copy idea + hook into the **Content Simulator** to score and improve it._")

    # GOAL prompt expander
    with st.expander("🎯 Generate GOAL prompt for this day", expanded=False):
        adv_key = f"wc_{i}_adv_mode"
        if adv_key not in st.session_state:
            st.session_state[adv_key] = "Standard"
        adv_mode = st.selectbox(
            "Advanced prompt mode",
            list(ADVANCED_PROMPT_MODES.keys()),
            key=adv_key,
            help=ADVANCED_PROMPT_MODES.get(st.session_state.get(adv_key, "Standard"), {}).get("description", ""),
        )
        if st.button("Generate GOAL prompt", key=f"wc_{i}_gen_goal"):
            g = st.session_state.get(_wc_key(i, "idea"), "(no idea yet)") or "(no idea yet)"
            o = f"Format: {st.session_state.get(_wc_key(i, 'format') or 'not specified', 'not specified')}. Status target: Ready to post."
            hook_v   = st.session_state.get(_wc_key(i, "hook"), "") or ""
            vis_v    = st.session_state.get(_wc_key(i, "visual_plan"), "") or ""
            cap_v    = st.session_state.get(_wc_key(i, "caption"), "") or ""
            cta_v    = st.session_state.get(_wc_key(i, "cta"), "") or ""
            dest_v   = st.session_state.get(_wc_key(i, "destination_package"), "") or ""
            pillar_v = st.session_state.get(_wc_key(i, "content_pillar"), "") or ""
            notes_v  = st.session_state.get(_wc_key(i, "notes"), "") or ""
            a_parts = [AVALON_CONTEXT_BLOCK]
            if dest_v:   a_parts.append(f"Destination: {dest_v}")
            if pillar_v: a_parts.append(f"Content pillar: {pillar_v}")
            if hook_v:   a_parts.append(f"Current hook: {hook_v}")
            if vis_v:    a_parts.append(f"Visual plan: {vis_v}")
            if cap_v:    a_parts.append(f"Caption draft: {cap_v}")
            if cta_v:    a_parts.append(f"CTA: {cta_v}")
            if notes_v:  a_parts.append(f"Notes: {notes_v}")
            l_text = f"Output a fully developed {st.session_state.get(_wc_key(i, 'format'), 'post')} for @avalon.escapes including: improved hook, caption (short punchy stanzas, 100–130 words), CTA, and visual direction."
            prompt = generate_goal_prompt(
                goal=f"Create a strong, ready-to-post {WEEKDAYS[i]} {st.session_state.get(_wc_key(i,'format'),'post')} for @avalon.escapes: {g}",
                objective=o,
                assets="\n".join(a_parts),
                layout=l_text,
                mode=st.session_state.get(adv_key, "Standard"),
            )
            st.session_state[f"wc_{i}_goal_prompt"] = prompt

        if st.session_state.get(f"wc_{i}_goal_prompt"):
            st.text_area(
                "Copy this prompt →",
                value=st.session_state[f"wc_{i}_goal_prompt"],
                height=280,
                key=f"wc_{i}_goal_display",
                label_visibility="visible",
            )
            st.caption("Paste into Claude Code (! or a new conversation) for full AI assistance.")


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL FRAMEWORKS HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def generate_goal_prompt(goal: str, objective: str, assets: str, layout: str, mode: str = "Standard") -> str:
    prefix = ADVANCED_PROMPT_MODES.get(mode, {}).get("prefix", "")
    body = (
        f"GOAL Prompt — Avalon Escapes\n\n"
        f"🎯 GOAL — What outcome am I working toward?\n{goal or '(not specified)'}\n\n"
        f"📏 OBJECTIVE — What does success look like?\n{objective or '(not specified)'}\n\n"
        f"🧰 ASSETS — Context, brand voice, audience, destinations, references\n{assets or '(not specified)'}\n\n"
        f"🖼️ LAYOUT — Format, structure, tone, output style\n{layout or '(not specified)'}"
    )
    return prefix + body


def generate_goal_diagnosis(idea: str, hook: str, caption: str, destination: str, fmt: str, cta: str) -> dict:
    """Evaluate how well the current content inputs satisfy each GOAL dimension."""
    full = " ".join(filter(None, [idea, hook, caption, destination, fmt, cta])).lower()

    # G — Goal clarity
    goal_signals = ["dm", "comment", "guide", "book", "plan", "escape", "design", "invite", "join",
                    "awareness", "share", "save", "viral", "show", "inspire", "inquiry", "trust"]
    g_hits = sum(1 for s in goal_signals if s in full)
    g_score = 3 if (len((idea or "").split()) >= 10 and g_hits >= 2) else (2 if g_hits >= 1 else 1)

    # O — Objective clarity (measurable CTA present)
    has_cta     = bool(cta and cta.strip())
    has_kw_cta  = any(k in (cta or "").lower() for k in ["dm", "comment", "save", "share", "book", "click", "tap"])
    o_score = 3 if (has_cta and has_kw_cta) else (2 if has_cta else 1)

    # A — Asset richness (context provided)
    char_count = len(" ".join(filter(None, [idea, hook, caption, destination])))
    a_score = 3 if char_count > 280 else (2 if char_count > 80 else 1)

    # L — Layout clarity (format + structure defined)
    has_fmt  = bool(fmt and fmt.strip())
    has_body = len((caption or "").split()) >= 25
    l_score = 3 if (has_fmt and has_body) else (2 if has_fmt else 1)

    _labels = {1: "Needs work", 2: "Developing", 3: "Strong"}
    _colors = {1: "#ef4444",    2: "#f59e0b",    3: "#22c55e"}
    _tips = {
        "goal": {
            1: "No clear outcome. What should happen after someone sees this? (DM, save, brand trust, inquiry?)",
            2: "Outcome is implied but not explicit. State the desired result clearly.",
            3: "Clear goal signal present.",
        },
        "objective": {
            1: "No measurable CTA. Add a specific keyword-driven action ('Comment MALDIVES', 'DM AVALON').",
            2: "CTA present but generic. Make it specific and keyword-driven for better conversion.",
            3: "Measurable, specific CTA present.",
        },
        "assets": {
            1: "Very thin context. Add destination details, emotion target, visual angle, or reference pattern.",
            2: "Some context present. Add more specificity — sensory detail, destination, founder angle.",
            3: "Good context richness — the AI has enough to work with.",
        },
        "layout": {
            1: "Format not specified and no caption structure. Define format + draft at least a caption outline.",
            2: "Format specified but caption is short. Develop the caption structure further.",
            3: "Format and caption structure are clear.",
        },
    }
    return {
        "goal":      {"score": g_score, "label": _labels[g_score], "color": _colors[g_score], "tip": _tips["goal"][g_score]},
        "objective": {"score": o_score, "label": _labels[o_score], "color": _colors[o_score], "tip": _tips["objective"][o_score]},
        "assets":    {"score": a_score, "label": _labels[a_score], "color": _colors[a_score], "tip": _tips["assets"][a_score]},
        "layout":    {"score": l_score, "label": _labels[l_score], "color": _colors[l_score], "tip": _tips["layout"][l_score]},
    }


def match_marketing_skill(fmt: str, pillar: str, idea: str) -> dict:
    """Return the most relevant marketing skill dict for this content type."""
    full = " ".join(filter(None, [fmt, pillar, idea])).lower()
    for skill_id, skill in MARKETING_SKILLS_MAP.items():
        if any(k in full for k in skill["keywords"]):
            return skill
    # Default by format
    fmt_l = (fmt or "").lower()
    if "carousel" in fmt_l or "guide" in fmt_l:
        return MARKETING_SKILLS_MAP["content_strategy"]
    if "story" in fmt_l:
        return MARKETING_SKILLS_MAP["social_media"]
    return MARKETING_SKILLS_MAP["copywriting"]


# ─────────────────────────────────────────────────────────────────────────────
# CONTENT STUDIO  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
_STUDIO_CAROUSEL_TYPES = {
    "Destination Guide":      {"arc":"guide",      "footer":"◆ CURATED · LUXURY · TRAVEL ◆"},
    "Brand Mythology":        {"arc":"mythology",  "footer":"◆ CURATED · LUXURY · TRAVEL ◆"},
    "Founders Story":         {"arc":"founders",   "footer":"◆ CURATED · LUXURY · TRAVEL ◆"},
    "Itinerary":              {"arc":"itinerary",  "footer":"◆ SAVE THIS ITINERARY ◆"},
    "Services / What We Offer":{"arc":"services",  "footer":"◆ CURATED · LUXURY · TRAVEL ◆"},
    "Hotel / Stay Comparison":{"arc":"comparison", "footer":"◆ CURATED · LUXURY · TRAVEL ◆"},
}

_STUDIO_DEST_DATA = {
    "Maldives":   {"places":["Fuvahmulah","Baa Atoll","South Ari","North Malé","SAII Maldives"],
                   "angle":"most resorts won't tell you about",
                   "photo_tags":["maldives_sunset_palms","ocean_underwater_coral","founder_diving_gear"]},
    "Colombia":   {"places":["Providencia","Medellín","Eje Cafetero","Cartagena","Santa Marta"],
                   "angle":"beyond Cartagena",
                   "photo_tags":["founder_city_monument","tropical_boat_beach"]},
    "Türkiye":    {"places":["Kaş","Cappadocia","Istanbul","Ölüdeniz","Bodrum"],
                   "angle":"is not one country",
                   "photo_tags":["founder_city_monument","singapore_night_cityscape"]},
    "Sri Lanka":  {"places":["Sigiriya","Mirissa","Ella","Arugam Bay","Kandy"],
                   "angle":"few travelers understand",
                   "photo_tags":["batu_caves_temple","tropical_boat_beach"]},
    "Brazil":     {"places":["Fernando de Noronha","Florianópolis","Rio de Janeiro","Bahia"],
                   "angle":"beyond the obvious",
                   "photo_tags":["christ_redeemer_sky","tropical_boat_beach"]},
    "Global":     {"places":["your chosen destination"],
                   "angle":"worth the journey",
                   "photo_tags":["founder_city_monument","founder_beach_golden_hour"]},
}

_STUDIO_OWN_POST_REFS = [
    {
        "folder": "Avalon Definiton/",
        "post": "¿Sabes qué significa Avalon?",
        "type": "Brand mythology carousel — 4 slides",
        "visual_tags": "Navy overlay · text-dominant · gold tags · italic serif",
        "mood": "Mythological · philosophical · intimate · invitational",
        "reusable_pattern": "Question hook → etymology → emotional meaning → DM CTA",
        "best_use": "Brand introduction · audience building · philosophy content",
    },
    {
        "folder": "Avalon - Founders/",
        "post": "Two women. Two cultures. One mission.",
        "type": "Founders introduction carousel — 6 slides",
        "visual_tags": "Authorial portraits · circular headshots · destination proof collage · navy overlay",
        "mood": "Trustworthy · personal · aspirational · human · global",
        "reusable_pattern": "Declaration cover → Mission → Meet Founder 1 → Meet Founder 2 → Promise → Photo proof",
        "best_use": "Trust building · new follower onboarding · campaign launches",
    },
    {
        "folder": "Avalon Escapes - 1st Post/",
        "post": "AVALON ESCAPES — The best places are not found. They are lived.",
        "type": "Brand launch carousel — 13+ slides (4 observed: 1, 5, 7, 13)",
        "visual_tags": "Full-bleed authorial photos · brand cover · services slide · end card · imagotype CTA",
        "mood": "Discovery · aspiration · confidence · invitation",
        "reusable_pattern": "Brand cover → Services → World philosophy → End card with imagotype",
        "best_use": "Brand introduction · services explanation · campaign opener · end-card format",
    },
]


def _cs_brand_fit_score(idea: str, hook: str, caption: str, fmt: str, dest: str) -> tuple:
    """Score content idea against Avalon brand standards. Returns (score, issues, strengths)."""
    text = f"{idea} {hook} {caption}".lower()
    score = 50
    issues, strengths = [], []

    _pos = [("feel","transform","shift","discover","real","authentic","personal","specific","inside","earned"),
            ("we've been","rafa","sofia","i've","personal","our trip","firsthand","actually"),
            ("save","guide","itinerary","tips","things","best","know before")]
    _pos_labels = ["Transformation/authenticity language ✓",
                   "Founder/personal voice ✓",
                   "Save-worthy framing ✓"]
    for kws, label in zip(_pos, _pos_labels):
        if any(w in text for w in kws):
            score += 8
            strengths.append(label)

    if dest and dest.lower() in text:
        score += 5
        strengths.append("Destination specificity ✓")
    if hook and len(hook.strip()) > 8:
        score += 5
        strengths.append("Hook present ✓")

    _neg = [("amazing","magical","stunning","incredible","breathtaking","paradise","luxurious","unforgettable"),
            ("book now","link in bio","swipe up","click the link","limited offer","discount"),
            ("award-winning","world-class","best travel agency","premium service","industry-leading"),
            ]
    _neg_labels = ["Generic luxury adjectives — replace with specific, earned details",
                   "Generic CTA — use 'DM us' or 'ESCRÍBENOS' instead",
                   "Corporate language — Avalon sounds like a trusted friend, not a company"]
    for kws, label in zip(_neg, _neg_labels):
        if any(w in text for w in kws):
            score -= 12
            issues.append(label)

    if "!" in (hook or "") or (caption or "").count("!") > 1:
        score -= 5
        issues.append("Multiple exclamation marks undercut the premium tone")
    if fmt == "Carousel" and not any(w in text for w in ["guide","tips","things","itinerary","best","know"]):
        issues.append("Carousel hook could be more guide/save-oriented")

    return max(0, min(100, score)), issues, strengths


_CS_LANG = {
    "English":    {"swipe":"SWIPE →","cta_btn":"[ SEND US A MESSAGE ]",
                   "cta_label":"YOUR {dest} ESCAPE","cta_soul":"Let's design yours.",
                   "cta_body":"Tell us where you want to go. We'll take care of the rest.",
                   "myth_cover_hl":"DO YOU KNOW","myth_cover_soul":"what Avalon actually means?",
                   "myth_cover_label":"THE NAME HAS A STORY",
                   "myth_labels":["● CELTIC MYTHOLOGY","FOR US","WE DON'T CREATE TRIPS"],
                   "myth_hls":["ÁVALON","AVALON IS","WE DESIGN"],
                   "myth_souls":["The Isle of Apples","something more","escapes, not trips"],
                   "save_trigger":"Save this before you book anything.",
                   "lang_note":""},
    "Spanish":    {"swipe":"DESLIZA PARA DESCUBRIR","cta_btn":"[ ESCRÍBENOS ]",
                   "cta_label":"TU PRÓXIMA ESCAPADA","cta_soul":"te está esperando.",
                   "cta_body":"Cuéntanos dónde quieres ir. Nosotras nos encargamos del resto.",
                   "myth_cover_hl":"¿SABES","myth_cover_soul":"qué significa Avalon?",
                   "myth_cover_label":"EL NOMBRE TIENE UNA HISTORIA",
                   "myth_labels":["● MITOLOGÍA CELTA","PARA NOSOTRAS","NO CREAMOS VIAJES"],
                   "myth_hls":["ÁVALON","AVALON ES","DISEÑAMOS"],
                   "myth_souls":["La isla de las manzanas","algo más","escapadas, no viajes"],
                   "save_trigger":"Guarda esto antes de reservar nada.",
                   "lang_note":"🌐 Spanish — all body copy should be written in Avalon's Spanish voice."},
    "Portuguese": {"swipe":"DESLIZE PARA DESCOBRIR","cta_btn":"[ ESCREVA-NOS ]",
                   "cta_label":"SUA PRÓXIMA FUGA","cta_soul":"está esperando por você.",
                   "cta_body":"Conta-nos onde queres ir. Cuidamos do resto.",
                   "myth_cover_hl":"VOCÊ SABE","myth_cover_soul":"o que significa Avalon?",
                   "myth_cover_label":"O NOME TEM UMA HISTÓRIA",
                   "myth_labels":["● MITOLOGIA CELTA","PARA NÓS","NÃO CRIAMOS VIAGENS"],
                   "myth_hls":["ÁVALON","AVALON É","DESENHAMOS"],
                   "myth_souls":["A ilha das maçãs","algo mais","escapadas, não viagens"],
                   "save_trigger":"Salva isto antes de reservares.",
                   "lang_note":"🌐 Portuguese — all body copy should be written in Avalon's Portuguese voice."},
}

_CS_CTA_BTNS = {
    "DM CTA (ESCRÍBENOS)":        {"en":"[ SEND US A MESSAGE ]","es":"[ ESCRÍBENOS ]","pt":"[ ESCREVA-NOS ]"},
    "Soft CTA (save + follow)":   {"en":"[ SAVE + FOLLOW ]","es":"[ GUARDA + SÍGUENOS ]","pt":"[ SALVA + SEGUE-NOS ]"},
    "Comment CTA (emoji response)":{"en":"Comment 🌊 below","es":"Comenta 🌊 abajo","pt":"Comenta 🌊 abaixo"},
    "Save CTA":                   {"en":"[ SAVE THIS ]","es":"[ GUARDA ESTO ]","pt":"[ SALVA ISTO ]"},
}


def parse_carousel_brief(brief: str) -> dict:
    """Infer all carousel parameters from natural language. Rule-based — no API."""
    b = brief.lower()

    # Destination
    dest = "Global"
    if any(w in b for w in ["maldives","maldive","atoll","fuvahmulah","baa atoll","lhaviyani","south ari"]):
        dest = "Maldives"
    elif any(w in b for w in ["colombia","colombian","cartagena","providencia","medellín","medellin","bogotá","bogota","eje cafetero"]):
        dest = "Colombia"
    elif any(w in b for w in ["brazil","brasil","rio","fernando de noronha","bahia","florianópolis","florianopolis","noronha"]):
        dest = "Brazil"
    elif any(w in b for w in ["türkiye","turkey","turkish","istanbul","cappadocia","kaş","kas","aegean","bosphorus","bodrum"]):
        dest = "Türkiye"
    elif any(w in b for w in ["sri lanka","srilanka","sigiriya","mirissa","ella","kandy","arugam"]):
        dest = "Sri Lanka"

    # Carousel type
    ctype = "Destination Guide"
    if any(w in b for w in ["founder","rafa","sofia","rafaella","co-founder","why we started","who we are","our story","the team","meet rafa","meet sofia"]):
        ctype = "Founders Story"
    elif any(w in b for w in ["meaning","mythology","celtic","what avalon means","qué significa","que significa","brand identity","brand story","brand meaning","what is avalon","el nombre","the name","avalon significa","origin","origen"]):
        ctype = "Brand Mythology"
    elif any(w in b for w in ["itinerary","day 1","day by day","schedule","days in","day trip"]):
        ctype = "Itinerary"
    elif any(w in b for w in ["offer","package","service","what we do","what we offer","included","group travel","dive travel","private travel","advisory"]):
        ctype = "Services / What We Offer"
    elif any(w in b for w in ["hotel","resort","villa","boutique","compare","comparison"," vs ","where to stay","which resort","which hotel"]):
        ctype = "Hotel / Stay Comparison"
    elif dest == "Global":
        ctype = "Brand Mythology"

    # Goal
    goal = "Destination desire + DM inquiry"
    if any(w in b for w in ["save","saveable","bookmark","share","viral","save-worthy"]):
        goal = "Save/share + reach"
    elif any(w in b for w in ["brand awareness","trust","identity","awareness"]):
        goal = "Brand awareness + trust"
    elif any(w in b for w in ["education","teach","learn","guide","tips","know before"]):
        goal = "Educational + save"

    # Target emotion
    emotion = "Curiosity → longing → trust → inquiry"
    if any(w in b for w in ["mythology","transformation","transform","shift","celtic","meaning"]):
        emotion = "Curiosity → wonder → belonging → desire to connect"
    elif any(w in b for w in ["emotional","emotion","feel","warm","warmth","touch","moving"]):
        emotion = "Emotion → connection → trust → desire"
    elif any(w in b for w in ["desire","dream","aspir","wish","longing"]):
        emotion = "Longing → desire → inspiration → inquiry"
    elif any(w in b for w in ["elegant","luxury","premium","high-end","sophisticated"]):
        emotion = "Aspiration → trust → desire → inquiry"

    # Slide count
    slides = 6
    m = re.search(r'(\d+)\s*[-–]?\s*slide', b)
    if m:
        slides = max(4, min(12, int(m.group(1))))
    else:
        for word, n in [("four",4),("five",5),("six",6),("seven",7),("eight",8),("nine",9),("ten",10)]:
            if word in b:
                slides = n
                break

    # Language
    language = "English"
    if any(w in b for w in ["spanish","español","espanol","en español","in spanish","castellano"]):
        language = "Spanish"
    elif any(w in b for w in ["portuguese","português","portugues","in portuguese","em português"]):
        language = "Portuguese"

    # CTA style
    cta_style = "DM CTA (ESCRÍBENOS)"
    if any(w in b for w in ["soft cta","soft cta","gentle cta","no sell","no cta","soft"]):
        cta_style = "Soft CTA (save + follow)"
    elif any(w in b for w in ["comment cta","comment","emoji response"]):
        cta_style = "Comment CTA (emoji response)"
    elif any(w in b for w in ["save cta","save trigger"]):
        cta_style = "Save CTA"

    # Visual mood
    mood_parts = []
    if any(w in b for w in ["navy","dark navy","deep navy","dark blue","#0f2649"]):
        mood_parts.append("Deep navy `#0F2649`")
    if any(w in b for w in ["ocean","underwater","sea","water","diving","marine"]):
        mood_parts.append("ocean blues + underwater light")
    if any(w in b for w in ["warm","golden","sunset","amber","terracotta"]):
        mood_parts.append("warm gold tones")
    if any(w in b for w in ["white serif","serif typography","white typography"]):
        mood_parts.append("white serif typography")
    if any(w in b for w in ["subtle gold","gold detail","gold accent"]):
        mood_parts.append("subtle gold accents")
    if any(w in b for w in ["cultural","city","urban","architecture","historic"]):
        mood_parts.append("cultural depth")
    if not mood_parts:
        mood_parts = ["Deep navy `#0F2649`", "premium editorial"]
    mood = " · ".join(mood_parts)

    # Photo tags
    dd = _STUDIO_DEST_DATA.get(dest, _STUDIO_DEST_DATA["Global"])
    photo_tags = list(dd["photo_tags"])
    if any(w in b for w in ["founder","rafa","sofia","personal","real photo"]):
        for t in ["founder_beach_golden_hour","founder_city_monument"]:
            if t not in photo_tags: photo_tags.insert(0, t)
    if any(w in b for w in ["ocean","diving","underwater","shark","coral","fish"]):
        for t in ["ocean_underwater_coral","founder_diving_gear"]:
            if t not in photo_tags: photo_tags.insert(0, t)
    if any(w in b for w in ["maldives","sunset","palm","island","overwater"]):
        if "maldives_sunset_palms" not in photo_tags: photo_tags.insert(0, "maldives_sunset_palms")

    needs_ai_brief = any(w in b for w in ["ai brief","image brief","ai image","midjourney","dall-e","no photos","generate image"])

    return {
        "carousel_type": ctype, "destination": dest, "goal": goal,
        "emotion": emotion, "slides": slides, "language": language,
        "cta_style": cta_style, "mood": mood,
        "photo_tags": photo_tags, "needs_ai_brief": needs_ai_brief,
    }


def _cs_ai_image_briefs(slides: int, dest: str, arc: str, mood: str) -> str:
    """Generate per-slide AI image prompt briefs (no API — descriptive only)."""
    dd = _STUDIO_DEST_DATA.get(dest, _STUDIO_DEST_DATA["Global"])
    places = dd["places"]
    L = ["### AI Image Briefs (when no authorial photo is available)\n"]
    L.append(f"Style reference: Deep navy overlay on real travel photography. Never stock-looking.")
    L.append(f"Palette: `#0F2649` navy dominant · white text · warm gold accents")
    L.append(f"Mood: {mood}\n")
    for i in range(1, slides + 1):
        place = places[(i - 2) % len(places)] if i > 1 else dest
        if i == 1:
            b = f"Wide, atmospheric establishing shot of {dest}. Moody, no people, ultra-premium travel editorial. Dark ocean or dramatic landscape."
        elif i == slides:
            b = f"{dest} golden hour — warm light, palm silhouettes or ocean reflection. End-card energy. Dark navy overlay."
        else:
            b = f"{place}, {dest} — authentic, non-tourist angle, atmospheric. {mood}. No logos, no crowds, no stock energy."
        L.append(f"**Slide {i}:** {b}")
    return "\n".join(L)


def _cs_build_carousel(ctype: str, dest: str, goal: str, emotion: str,
                        slides: int, tags_raw: str,
                        language: str = "English",
                        cta_style: str = "DM CTA (ESCRÍBENOS)") -> str:
    """Generate structured carousel copy brief with language + CTA style awareness."""
    ct  = _STUDIO_CAROUSEL_TYPES.get(ctype, _STUDIO_CAROUSEL_TYPES["Destination Guide"])
    dd  = _STUDIO_DEST_DATA.get(dest, _STUDIO_DEST_DATA["Global"])
    lng = _CS_LANG.get(language, _CS_LANG["English"])
    lang_code = {"English":"en","Spanish":"es","Portuguese":"pt"}.get(language, "en")
    cta_btn = _CS_CTA_BTNS.get(cta_style, _CS_CTA_BTNS["DM CTA (ESCRÍBENOS)"])[lang_code]

    places = dd["places"]
    angle  = dd["angle"]
    footer = ct["footer"]
    user_tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    all_tags  = user_tags + dd["photo_tags"]
    def _tag(i): return f"`{all_tags[i % len(all_tags)]}`" if all_tags else "`authorial photo`"

    arc = ct["arc"]
    L = []
    if lng["lang_note"]:
        L.append(f"> {lng['lang_note']}\n")
    L.append(f"**Type:** {ctype}  |  **Destination:** {dest}  |  **Slides:** {slides}  |  **Language:** {language}")
    L.append(f"**Goal:** {goal}  |  **Emotion:** {emotion}")
    L.append(f"**CTA style:** {cta_style}")
    L.append("")

    # Cover slide — language-aware
    if arc == "mythology":
        cover_hl    = lng["myth_cover_hl"]
        cover_soul  = lng["myth_cover_soul"]
        cover_label = lng["myth_cover_label"]
    elif arc == "founders":
        cover_hl    = "TWO WOMEN." if language == "English" else "DOS MUJERES." if language == "Spanish" else "DUAS MULHERES."
        cover_soul  = "Two cultures. One mission." if language == "English" else "Dos culturas. Una misión." if language == "Spanish" else "Duas culturas. Uma missão."
        cover_label = "WHY AVALON EXISTS" if language == "English" else "POR QUÉ EXISTE AVALON" if language == "Spanish" else "POR QUE EXISTE AVALON"
    elif arc == "services":
        cover_hl    = "AVALON ESCAPES"
        cover_soul  = "The best places are not found. They are lived." if language == "English" else "Los mejores lugares no se encuentran. Se viven." if language == "Spanish" else "Os melhores lugares não se encontram. Vivem-se."
        cover_label = "CURATED EXPERIENCES · CULTURE & DIVING"
    elif arc == "itinerary":
        cover_hl    = "THE PERFECT" if language == "English" else "EL ITINERARIO PERFECTO" if language == "Spanish" else "O ITINERÁRIO PERFEITO"
        cover_soul  = f"{dest} itinerary" if language == "English" else f"de {dest}" if language == "Spanish" else f"de {dest}"
        cover_label = f"SAVE THIS · {slides - 1} DAYS" if language == "English" else f"GUARDA ESTO · {slides - 1} DÍAS" if language == "Spanish" else f"SALVA ISTO · {slides - 1} DIAS"
    elif arc == "comparison":
        cover_hl    = dest.upper()
        cover_soul  = "where to actually stay" if language == "English" else "dónde hospedarse de verdad" if language == "Spanish" else "onde realmente ficar"
        cover_label = "THE STAY MATTERS" if language == "English" else "EL ALOJAMIENTO IMPORTA" if language == "Spanish" else "A HOSPEDAGEM IMPORTA"
    else:  # guide
        cover_hl    = dest.upper()
        cover_soul  = angle
        cover_label = "WHAT MOST TRAVELERS MISS" if language == "English" else "LO QUE LA MAYORÍA NO VE" if language == "Spanish" else "O QUE A MAIORIA PERDE"

    L.append("### Slide 1 — Hook (Cover)")
    L.append(f"**Headline (Montserrat Black):** {cover_hl}")
    L.append(f"**Soul line (Amore Christmas italic):** {cover_soul}")
    L.append(f"**Micro label (gold):** {cover_label}")
    L.append(f"**Swipe instruction (gold):** {lng['swipe']}")
    L.append(f"**Footer:** {footer}")
    L.append(f"**Photo:** {_tag(0)}  ·  **Logo:** Butterfly isotype top-right · @avalon.escapes top-left")
    L.append("")

    # Middle slides
    for i in range(2, slides):
        place = places[(i - 2) % len(places)]
        role  = place if arc == "guide" else _mid_role(arc, i, slides)
        lbl   = lng["myth_labels"][min(i-2,2)] if arc == "mythology" else _mid_label(arc, dest, place, i)
        hl    = lng["myth_hls"][min(i-2,2)] if arc == "mythology" else _mid_hl(arc, dest, place, i)
        soul  = lng["myth_souls"][min(i-2,2)] if arc == "mythology" else _mid_soul(arc, dest, place)
        L.append(f"### Slide {i} — {role}")
        L.append(f"**Category label (gold):** {lbl}")
        L.append(f"**Headline (Montserrat Black):** {hl}")
        L.append(f"**Soul line (italic):** {soul}")
        L.append(f"**Body:** [Specific insider knowledge — not guidebook, not stock copy]")
        L.append(f"**Photo:** {_tag(i)}  ·  **Logo:** Butterfly isotype top-right")
        L.append("")

    # CTA slide
    cta_label = lng["cta_label"].format(dest=dest.upper())
    L.append(f"### Slide {slides} — CTA")
    L.append(f"**Micro label (gold):** {cta_label}")
    L.append(f"**Soul headline:** {lng['cta_soul']}")
    L.append(f"**Sub-text:** {lng['cta_body']}")
    L.append(f"**CTA button:** {cta_btn} (outlined white)")
    L.append(f"**Footer:** {footer}")
    L.append(f"**Photo:** {_tag(slides - 1)} golden hour  ·  **Logo:** Full imagotype centered")
    L.append("")

    L.append("---")
    L.append("**Caption hook:** " + _caption_hook_cs(arc, dest, language))
    L.append("")
    L.append("**Caption body:** 3–4 short stanzas. Specific knowledge. Rafa or Sofia's voice.")
    L.append(f"**Save trigger:** \"{lng['save_trigger']}\"")
    L.append("**CTA:** DM invite or comment prompt — never \"link in bio\"")
    L.append("")
    L.append("**Colors:** Navy `#0F2649` backgrounds · White Montserrat Black headlines · Gold labels")
    L.append("**Logo:** Isotype (top-right) on all slides · Full imagotype on CTA slide only")

    return "\n".join(L)


def _mid_role(arc, i, total):
    roles = {
        "mythology": ["Etymology / Origin", "Brand Meaning", "Philosophy", "Promise"],
        "founders":  ["Our Mission", "Meet Rafa", "Meet Sofia", "Our Promise", "Destination Proof"],
        "services":  ["What We Offer", "Dive & Ocean Travel", "Custom Escapes", "Our Philosophy"],
        "itinerary": [f"Days {j*2-1}–{j*2}" for j in range(1, 6)],
        "comparison":["Why the Stay Matters", "Option A", "Option B", "Our Recommendation"],
        "guide":     ["Context", "Insight 1", "Insight 2", "Insider Angle"],
    }
    return roles.get(arc, ["Body Slide"])[(i - 2) % len(roles.get(arc, ["Body Slide"]))]


def _mid_label(arc, dest, place, i):
    if arc == "mythology": return ["● CELTIC MYTHOLOGY","FOR US","WE DON'T CREATE TRIPS"][min(i-2,2)]
    if arc == "founders":  return ["OUR MISSION","CO-FOUNDER","CO-FOUNDER","OUR PROMISE"][min(i-2,3)]
    if arc == "services":  return "WHAT WE OFFER"
    return dest.upper()


def _mid_hl(arc, dest, place, i):
    if arc == "mythology": return ["ÁVALON","AVALON IS","WE DESIGN"][min(i-2,2)]
    if arc == "founders":  return ["OUR MISSION","MEET\nRAFA","MEET\nSOFIA","OUR PROMISE"][min(i-2,3)]
    if arc == "services":  return ["WHAT WE OFFER","DIVE TRAVEL","PRIVATE ADVISORY","THE WORLD AWAITS"][min(i-2,3)]
    if arc == "itinerary": return f"DAYS {(i-1)*2-1}–{(i-1)*2}"
    return place.upper() + "."


def _mid_soul(arc, dest, place):
    if arc == "mythology": return "La isla de las manzanas"
    if arc == "founders":  return "Avalon is for those who want to feel a place, not just visit it."
    if arc == "services":  return "Trips designed to turn dreams into real experiences."
    return "worth the detour."


def _caption_hook_cs(arc, dest, language="English"):
    hooks_en = {
        "mythology": "There's a reason we named it Avalon.",
        "founders":  "We didn't start a travel agency.",
        "guide":     f"Most people think they know {dest}.",
        "itinerary": f"The {dest} itinerary most people never find.",
        "services":  "We don't book trips. We design escapes.",
        "comparison":f"The right stay in {dest} changes the whole trip.",
    }
    hooks_es = {
        "mythology": "Hay una razón por la que lo llamamos Avalon.",
        "founders":  "No empezamos una agencia de viajes.",
        "guide":     f"La mayoría cree que conoce {dest}.",
        "itinerary": f"El itinerario de {dest} que la mayoría nunca encuentra.",
        "services":  "No reservamos viajes. Diseñamos escapadas.",
        "comparison":f"El alojamiento correcto en {dest} cambia el viaje entero.",
    }
    hooks_pt = {
        "mythology": "Há uma razão pela qual o chamamos Avalon.",
        "founders":  "Não começámos uma agência de viagens.",
        "guide":     f"A maioria acha que conhece {dest}.",
        "itinerary": f"O itinerário de {dest} que a maioria nunca encontra.",
        "services":  "Não reservamos viagens. Desenhamos escapadas.",
        "comparison":f"A hospedagem certa em {dest} muda toda a viagem.",
    }
    bank = {"English": hooks_en, "Spanish": hooks_es, "Portuguese": hooks_pt}.get(language, hooks_en)
    return bank.get(arc, f"The {dest} you haven't discovered yet." if language == "English"
                   else f"El {dest} que aún no has descubierto." if language == "Spanish"
                   else f"O {dest} que ainda não descobriste.")


def parse_content_idea_brief(brief: str) -> dict:
    """Parse a natural-language content idea into simulator parameters. Rule-based — no API."""
    b = brief.lower()

    # ── Destination ──────────────────────────────────────────────────────────
    dest = "Global / Curated Escapes"
    if any(w in b for w in ["maldives","maldive","fuvahmulah","fuvah","atoll","tiger shark","whale shark","hammerhead","manta ray"]):
        dest = "Maldives"
    elif any(w in b for w in ["colombia","colombian","cartagena","providencia","medellín","medellin","bogotá","bogota","eje cafetero"]):
        dest = "Colombia"
    elif any(w in b for w in ["brazil","brasil","rio","fernando de noronha","bahia","florianópolis","noronha","ipanema","copacabana"]):
        dest = "Brazil"
    elif any(w in b for w in ["türkiye","turkey","turkish","istanbul","cappadocia","kaş","kas","aegean","bodrum","bosphorus","oludeniz"]):
        dest = "Türkiye"
    elif any(w in b for w in ["sri lanka","srilanka","sigiriya","mirissa","ella","kandy","arugam","galle"]):
        dest = "Sri Lanka"

    # ── Format ───────────────────────────────────────────────────────────────
    fmt = "Reel"
    if any(w in b for w in ["carousel","slides","save this","swipe","itinerary carousel","guide carousel"]):
        fmt = "Carousel"
    elif any(w in b for w in ["story","poll","question box","instagram story"]):
        fmt = "Story"
    elif any(w in b for w in [" photo "," image "," photograph ","static","single image"]):
        fmt = "Static Photo"
    elif any(w in b for w in ["founder story","founder reel","why we started","origin story","why we created"]):
        fmt = "Founder Story"
    elif any(w in b for w in ["destination guide","guide to","things to know","what you need to know about"]):
        fmt = "Destination Guide"

    # ── Emotion ──────────────────────────────────────────────────────────────
    emotion = "curiosity → longing → trust"
    if any(w in b for w in ["intense","intensity","adrenaline","wild","raw","extreme","heart racing"]):
        emotion = "intensity → awe → transformation"
    elif any(w in b for w in ["transform","transformation","change","shift","different person","grew","growth","life changing"]):
        emotion = "curiosity → transformation → belonging"
    elif any(w in b for w in ["peace","calm","still","quiet","serene","meditative","slow travel"]):
        emotion = "peace → stillness → desire for calm"
    elif any(w in b for w in ["aspir","dream","luxury","premium","high-end","bucket list","beautiful"]):
        emotion = "aspiration → desire → trust → inquiry"
    elif any(w in b for w in ["surprise","unexpected","didn't expect","shocked","shocking","unbelievable"]):
        emotion = "surprise → curiosity → delight"
    elif any(w in b for w in ["founder","personal","honest","real","authentic","behind the scenes","personal story"]):
        emotion = "trust → connection → belonging"
    elif any(w in b for w in ["emotional","emotion","deep","moving","touch"]):
        emotion = "emotional depth → wonder → connection"

    # ── Content pillar ───────────────────────────────────────────────────────
    pillar = "Destination Guide"
    if any(w in b for w in ["diving","dive","shark","ocean","underwater","freediving","coral","marine","atoll","manta"]):
        pillar = "Ocean & Island Adventures"
    elif any(w in b for w in ["founder","rafa","sofia","co-founder","why we started","our story","behind the scenes","we created"]):
        pillar = "Founder Story"
    elif any(w in b for w in ["meaning","mythology","celtic","brand","what avalon","why avalon","origin","history of avalon"]):
        pillar = "Brand Mythology"
    elif any(w in b for w in ["colombia","brazil","cartagena","providencia","culture","local","hidden gem","authentic","latin"]):
        pillar = "Latin America & Cultural Discovery"
    elif any(w in b for w in ["türkiye","turkey","istanbul","cappadocia","crossroads","kaş","aegean","ottoman"]):
        pillar = "Türkiye & Crossroads Travel"
    elif any(w in b for w in ["wellness","retreat","mindful","slow travel","mountains","jungle","nature","retreat"]):
        pillar = "Nature & Transformation"
    elif any(w in b for w in ["luxury","boutique","hotel","resort","villa","elevated","curated","bespoke","romantic","honeymoon"]):
        pillar = "Luxury Escapes"
    elif any(w in b for w in ["itinerary","custom","tailor","private tour","group trip","special occasion","honeymoon"]):
        pillar = "Tailor-Made Journeys"
    elif any(w in b for w in ["pov","send this to","invitation","reminder","this is your sign","trend","viral"]):
        pillar = "Viral Travel Inspiration"

    # ── Viral pattern ─────────────────────────────────────────────────────────
    pattern = "Curiosity-Gap Hook"
    if any(w in b for w in ["tiger shark","whale shark","hammerhead","freediving","underwater","ocean","marine","shark dive"]):
        pattern = "Transformation Story + Ocean Authority"
    elif any(w in b for w in ["no one tells","what no one","secret","hidden","most people","what most travelers","nobody talks"]):
        pattern = "Curiosity-Gap Hook + Expectation Flip"
    elif any(w in b for w in ["founder","rafa","sofia","personal story","why we started","origin","we created"]):
        pattern = "Founder POV + Trust Build"
    elif any(w in b for w in ["transform","changed me","different","shift","became","clarity"]):
        pattern = "Transformation Story"
    elif any(w in b for w in ["save","guide","itinerary","list","top","tips","things to know"]):
        pattern = "Saveable Guide"
    elif any(w in b for w in ["meaning","mythology","celtic","brand","what avalon means","origin story"]):
        pattern = "Myth / Meaning"
    elif any(w in b for w in ["before","after","thought","expected","reality check"]):
        pattern = "Before/After Feeling"
    elif any(w in b for w in ["aspir","dream","luxury","premium","beautiful","stunning","escape list","waitlist"]):
        pattern = "Aspirational Soft Sell"
    elif any(w in b for w in ["emotional","emotion","moving","touch","feeling","alive","connection"]):
        pattern = "Emotional Contrast"
    elif any(w in b for w in ["beyond","not just","more than","different side","another side"]):
        pattern = "Expectation Flip + Destination Love"

    # ── Adaptation tier ───────────────────────────────────────────────────────
    tier = "Tier 2 — Structural Replication"
    if any(w in b for w in ["pov","send this to","reminder","comment keyword","type","drop","trend","viral trend","this is your sign"]):
        tier = "Tier 1 — Direct Trend Adaptation"
    elif any(w in b for w in ["founder story","personal story","origin story","mythology","brand story","why we","manifesto"]):
        tier = "Tier 3 — Inspiration Only"
    elif any(w in b for w in ["original","unique","avalon only","not a trend","our own"]):
        tier = "Original Avalon Concept"

    # ── CTA ───────────────────────────────────────────────────────────────────
    cta = "DM us to design your escape"
    m = re.search(r'comment\s+["\']?([a-z0-9_]+)["\']?\s+for', b)
    if m:
        kw = m.group(1).upper()
        cta = f"Comment '{kw}' for the guide"
    elif any(w in b for w in ["dm us","dm me","send us a message","escríbenos","message us","write to us"]):
        cta = "DM us to plan your escape"
    elif any(w in b for w in ["waitlist","escape list","join the list","join avalon","newsletter"]):
        cta = "Join the Avalon Escape List"
    elif any(w in b for w in ["save this","save before","bookmark"]):
        cta = "Save this before planning your trip"
    elif any(w in b for w in ["share","send this to","tag someone"]):
        cta = "Send this to whoever needs this trip"

    # ── Draft hook ────────────────────────────────────────────────────────────
    dest_short = dest.split(" /")[0].rstrip()
    if any(w in b for w in ["tiger shark","whale shark","hammerhead"]):
        hook = f"No one tells you what it feels like to dive with tiger sharks in {dest_short}."
    elif any(w in b for w in ["founder","rafa","sofia","why we started","we created"]):
        hook = "We didn't start a travel agency."
    elif any(w in b for w in ["meaning","mythology","what avalon","why avalon"]):
        hook = "There's a reason we named it Avalon."
    elif "escape list" in b or "waitlist" in b:
        hook = "We don't sell trips. We design escapes."
    elif any(w in b for w in ["beyond","not just","more than","different side"]):
        hook = f"Most people think they know {dest_short}. They've seen the postcard version."
    elif any(w in b for w in ["secret","hidden","no one talks","nobody talks"]):
        hook = f"There's a side of {dest_short} most travelers never find."
    else:
        hook = f"There's a version of {dest_short} most people never see."

    # ── Audience intent ───────────────────────────────────────────────────────
    intent = "Discovery & Inspiration"
    if any(w in b for w in ["book","booking","inquiry","plan","package","itinerary guide","dm"]):
        intent = "Research & Planning → Inquiry"
    elif any(w in b for w in ["save","guide","itinerary","tips","know before"]):
        intent = "Save for Later"
    elif any(w in b for w in ["share","send","tag","viral"]):
        intent = "Share with someone"
    elif any(w in b for w in ["join","waitlist","escape list","community","follow"]):
        intent = "Community / Brand Loyalty"

    # ── Suggested visual direction ────────────────────────────────────────────
    if any(w in b for w in ["tiger shark","whale shark","diving","underwater","ocean","marine","coral","reef","freediving"]):
        visual = "Underwater footage or photo · Close shark approach · Deep blue tones · Minimal text · Audio: ambient ocean depth"
    elif any(w in b for w in ["founder","rafa","sofia","personal"]):
        visual = "Rafa or Sofia on location · Authentic moment, not posed · Short punchy cuts · Navy text overlay"
    elif dest == "Colombia":
        visual = "Providencia turquoise water or Cartagena color · Navy overlay · Gold labels · Warm terracotta contrast"
    elif dest == "Türkiye":
        visual = "Cappadocia sky or Kaş coast · Navy overlay · Gold footer tags · Terracotta + teal palette"
    elif dest == "Maldives":
        visual = "Overwater sunrise or underwater shot · Navy `#0F2649` overlay · White Montserrat Black headline"
    elif dest == "Brazil":
        visual = "Noronha coastline or Rio energy · Navy overlay · Warm color contrast · Ocean blues"
    elif dest == "Sri Lanka":
        visual = "Temple or tea country or Mirissa ocean · Navy overlay · Cultural depth + ocean light"
    else:
        visual = "Strong hero destination shot · Navy `#0F2649` overlay · White Montserrat Black headline · Butterfly isotype top-right"

    # ── Hashtag direction ─────────────────────────────────────────────────────
    hashtag_dir = DESTINATION_HASHTAGS.get(dest, DESTINATION_HASHTAGS["Global / Curated Escapes"])[:8]

    return {
        "idea":        brief,
        "hook":        hook,
        "destination": dest,
        "format":      fmt,
        "emotion":     emotion,
        "caption":     "",
        "cta":         cta,
        "tier":        tier,
        "pattern":     pattern,
        "pillar":      pillar,
        "intent":      intent,
        "visual":      visual,
        "hashtags":    hashtag_dir,
    }


def _save_to_idea_vault(idea_data: dict) -> bool:
    """Append idea to data/content_idea_vault.json. Returns True on success."""
    try:
        vault_path = ROOT / "data" / "content_idea_vault.json"
        vault: list = []
        if vault_path.exists():
            try:
                vault = json.loads(vault_path.read_text(encoding="utf-8"))
                if not isinstance(vault, list):
                    vault = []
            except Exception:
                vault = []
        idea_data["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        vault.append(idea_data)
        vault_path.write_text(json.dumps(vault, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


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
    "🎨  Avalon Content Studio":      "studio",
    "🧠  Frameworks & Prompt Builder":"frameworks",
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

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Top Viral Posts", "📚 Pattern Library", "🔢 Three-Tier Framework", "👥 Creator Authority"])

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

    # ── Tab 4: Creator Authority ───────────────────────────────────────────────
    with tab4:
        st.markdown("### Creator Authority & Reference Strength")
        st.markdown(
            "Each creator is scored 0–100 combining: **viral performance** (35%) · "
            "**follower authority** (25%) · **Avalon fit** (25%) · **replicability** (15%). "
            "Follower count defaults to a mid-range authority value when unknown — "
            "update in `config/reference_creators.json`."
        )

        creator_cfgs  = load_creator_config()
        c_stats       = compute_creator_stats()

        if not creator_cfgs:
            st.warning("Creator config not found at `config/reference_creators.json`.")
        else:
            # ── Summary table ────────────────────────────────────────────────
            rows = []
            for uname, cfg in creator_cfgs.items():
                s        = c_stats.get(uname, {})
                strength = compute_reference_strength(uname, c_stats, creator_cfgs)
                fc       = cfg.get("follower_count")
                rows.append({
                    "Creator":          f"@{uname}",
                    "Followers":        fmt_number(fc) if fc else "—",
                    "Niche":            cfg.get("niche", "—"),
                    "Posts Analyzed":   s.get("total", 0),
                    "Viral Posts (≥3×)": s.get("viral", 0),
                    "Top Format":       (s.get("top_format") or "—").capitalize(),
                    "Best Opportunity": cfg.get("best_avalon_opportunity", "—")[:55],
                    "Strength /100":    strength,
                })
            df_auth = pd.DataFrame(rows).sort_values("Strength /100", ascending=False)
            st.dataframe(df_auth, use_container_width=True, hide_index=True)

            # ── Bar chart ────────────────────────────────────────────────────
            if not df_auth.empty:
                fig = px.bar(
                    df_auth, x="Strength /100", y="Creator", orientation="h",
                    template=PLOTLY_TMPL, color="Strength /100",
                    color_continuous_scale=["#0077b6","#00b4d8","#48cae4"],
                    range_color=[0, 100], text="Strength /100",
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=340, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.markdown("#### Creator Profiles")
            unames = list(creator_cfgs.keys())
            for i in range(0, len(unames), 2):
                row_cols = st.columns(2)
                for j, uname in enumerate(unames[i:i+2]):
                    cfg      = creator_cfgs[uname]
                    s        = c_stats.get(uname, {})
                    strength = compute_reference_strength(uname, c_stats, creator_cfgs)
                    fc       = cfg.get("follower_count")
                    fc_str   = f"{fmt_number(fc)} followers" if fc else "follower count unknown (add to config)"
                    with row_cols[j]:
                        st.markdown(
                            f"<div class='ac'>"
                            f"<h4>@{uname}</h4>"
                            f"<p>"
                            f"<b style='color:#e2e8f0'>Niche:</b> {cfg.get('niche','—')}<br>"
                            f"<b style='color:#e2e8f0'>Followers:</b> {fc_str}<br>"
                            f"<b style='color:#e2e8f0'>Analyzed:</b> {s.get('total',0)} posts · {s.get('viral',0)} viral (≥3×)<br>"
                            f"<b style='color:#e2e8f0'>Reference Strength:</b> {strength}/100<br>"
                            f"<b style='color:#e2e8f0'>Best Avalon opportunity:</b> {cfg.get('best_avalon_opportunity','—')}<br>"
                            f"<span style='color:#64748b;font-size:.8rem'>{cfg.get('why_relevant_to_avalon','')}</span>"
                            f"</p></div>",
                            unsafe_allow_html=True,
                        )

            st.markdown("---")
            st.markdown(
                "<div class='ac'><p>"
                "<b style='color:#e2e8f0'>How to add follower counts:</b> Open "
                "<code>config/reference_creators.json</code>, find each creator's entry, "
                "and set <code>\"follower_count\"</code> to an integer (e.g. <code>450000</code>). "
                "The dashboard will update on next reload.<br><br>"
                "<b style='color:#e2e8f0'>How to add new creators:</b> Add their details to "
                "<code>config/new_reference_creators_to_add.json</code>, then move the entry "
                "into <code>reference_creators.json</code> under <code>viral_reference_group.accounts</code>."
                "</p></div>",
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
        "<p style='color:#64748b;font-size:.88rem'>"
        "Describe a content idea in plain language — the simulator infers everything and scores it against "
        "Avalon's brand standards and the viral influencer reference group.</p>",
        unsafe_allow_html=True,
    )

    # ── Quick Idea Mode: main input ──────────────────────────────────────────
    brief_text = st.text_area(
        "Describe the content idea",
        placeholder=(
            "e.g. Create a Reel idea about diving with tiger sharks in Fuvahmulah. "
            "It should feel intense, emotional, and transformative. "
            "CTA: comment FUVAH for the guide.\n\n"
            "Other examples:\n"
            "• I want a carousel about Colombia beyond Cartagena, focused on hidden islands, culture, and boutique luxury.\n"
            "• Score this: a founder story reel about why Rafa and Sofia created Avalon.\n"
            "• Make a soft sales reel for the Avalon Escape List, inviting people to join without sounding pushy."
        ),
        height=130,
        key="sim_brief_input",
    )

    # ── Auto-parse: update adv-settings when brief changes ──────────────────
    if brief_text.strip() and brief_text != st.session_state.get("_sim_brief_prev", ""):
        st.session_state["_sim_brief_prev"] = brief_text
        _inf = parse_content_idea_brief(brief_text)
        st.session_state["sim_adv_idea"]    = _inf["idea"]
        st.session_state["sim_adv_hook"]    = _inf["hook"]
        st.session_state["sim_adv_dest"]    = _inf["destination"]
        st.session_state["sim_adv_fmt"]     = _inf["format"]
        st.session_state["sim_adv_emotion"] = _inf["emotion"]
        st.session_state["sim_adv_caption"] = _inf["caption"]
        st.session_state["sim_adv_cta"]     = _inf["cta"]
        st.session_state["sim_adv_tier"]    = _inf["tier"]
        st.session_state["sim_adv_pattern"] = _inf["pattern"]

    # ── Inferred summary card ────────────────────────────────────────────────
    if brief_text.strip():
        _idc = parse_content_idea_brief(brief_text)
        _tier_color = {"Tier 1":"#4ade80","Tier 2":"#60a5fa","Tier 3":"#a78bfa","Original":"#f59e0b"}.get(
            _idc["tier"].split("—")[0].strip(), "#64748b")
        st.markdown(
            f"<div style='background:#0a1520;border:1px solid #1a3a5f;border-radius:8px;"
            f"padding:.75rem 1.1rem;margin:.3rem 0 .6rem 0'>"
            f"<p style='color:#60a5fa;font-weight:700;font-size:.78rem;margin:0 0 .45rem 0'>"
            f"✅ Inferred — override in Advanced Settings if needed</p>"
            f"<div style='display:flex;flex-wrap:wrap;gap:.35rem'>"
            f"<span style='background:#1e3a5f;color:#93c5fd;font-size:.74rem;padding:.2rem .55rem;border-radius:20px'>📍 {_idc['destination']}</span>"
            f"<span style='background:#1e3a5f;color:#93c5fd;font-size:.74rem;padding:.2rem .55rem;border-radius:20px'>🎬 {_idc['format']}</span>"
            f"<span style='background:#1a2e1a;color:#86efac;font-size:.74rem;padding:.2rem .55rem;border-radius:20px'>🧭 {_idc['pillar']}</span>"
            f"<span style='background:#2a1a2a;color:#d8b4fe;font-size:.74rem;padding:.2rem .55rem;border-radius:20px'>💫 {_idc['emotion']}</span>"
            f"<span style='background:#2a1a10;color:#fcd34d;font-size:.74rem;padding:.2rem .55rem;border-radius:20px'>🎯 {_idc['cta']}</span>"
            f"<span style='background:#1a1a2a;color:#c4b5fd;font-size:.74rem;padding:.2rem .55rem;border-radius:20px'>📐 {_idc['pattern']}</span>"
            f"<span style='background:#1a1a1a;border:1px solid {_tier_color}44;color:{_tier_color};font-size:.74rem;padding:.2rem .55rem;border-radius:20px'>{_idc['tier']}</span>"
            f"</div>"
            f"<p style='color:#475569;font-size:.73rem;margin:.4rem 0 0 0'>"
            f"<b style='color:#64748b'>Hook:</b> {_idc['hook']}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Seed defaults for adv fields ─────────────────────────────────────────
    _fmt_opts  = ["Reel","Carousel","Static Photo","Story","Founder Story","Destination Guide","Trend Adaptation"]
    _tier_opts = ["Tier 1 — Direct Trend Adaptation","Tier 2 — Structural Replication",
                  "Tier 3 — Inspiration Only","Original Avalon Concept"]
    _sim_defs = {
        "sim_adv_idea": "", "sim_adv_hook": "", "sim_adv_dest": "",
        "sim_adv_fmt": "Reel", "sim_adv_emotion": "curiosity → longing → trust",
        "sim_adv_caption": "", "sim_adv_cta": "",
        "sim_adv_tier": "Tier 2 — Structural Replication", "sim_adv_pattern": "",
    }
    for _k, _v in _sim_defs.items():
        if _k not in st.session_state:
            st.session_state[_k] = _v

    # ── Advanced Settings expander ────────────────────────────────────────────
    with st.expander("⚙️ Advanced Settings — auto-filled from brief, override if needed"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("Content Idea / Concept", key="sim_adv_idea", height=75)
            st.text_input("Destination", placeholder="e.g. Fuvahmulah, Maldives", key="sim_adv_dest")
            _fmt_idx = _fmt_opts.index(st.session_state["sim_adv_fmt"]) if st.session_state["sim_adv_fmt"] in _fmt_opts else 0
            st.selectbox("Format", _fmt_opts, index=_fmt_idx, key="sim_adv_fmt_w")
            st.text_input("Intended Emotion", placeholder="e.g. awe → transformation", key="sim_adv_emotion")
        with col2:
            st.text_area("Draft Hook (first line / first 3 sec)", height=75, key="sim_adv_hook")
            st.text_area("Draft Caption / Script (optional)", height=100, key="sim_adv_caption")
            st.text_input("CTA", placeholder="e.g. Comment 'FUVAH' for the guide", key="sim_adv_cta")
            _tier_idx = _tier_opts.index(st.session_state["sim_adv_tier"]) if st.session_state["sim_adv_tier"] in _tier_opts else 1
            st.selectbox("Adaptation Tier", _tier_opts, index=_tier_idx, key="sim_adv_tier_w")
            st.text_input("Closest Pattern (optional)", placeholder="e.g. Curiosity-Gap Hook", key="sim_adv_pattern")

    # ── Analyze button ────────────────────────────────────────────────────────
    submitted = st.button("🔍 Analyze Content Idea", key="sim_analyze_btn", type="primary")
    if submitted:
        _idea    = st.session_state.get("sim_adv_idea") or brief_text
        _hook    = st.session_state.get("sim_adv_hook", "")
        _dest    = st.session_state.get("sim_adv_dest", "")
        _fmt     = st.session_state.get("sim_adv_fmt_w", st.session_state.get("sim_adv_fmt", "Reel"))
        _emotion = st.session_state.get("sim_adv_emotion", "")
        _caption = st.session_state.get("sim_adv_caption", "")
        _cta     = st.session_state.get("sim_adv_cta", "")
        _tier    = st.session_state.get("sim_adv_tier_w", st.session_state.get("sim_adv_tier", "Tier 2 — Structural Replication"))

        if _idea or _hook:
            _result      = run_scoring(_idea, _dest, _fmt, _emotion, _hook, _caption, _cta, _tier)
            _improvement = generate_improvement(_idea, _hook, _caption, _dest, _fmt, _emotion, _cta, _tier)
            _inferred    = parse_content_idea_brief(brief_text) if brief_text.strip() else {}
            st.session_state.update({
                "_sim_result": _result, "_sim_improvement": _improvement,
                "_sim_inferred": _inferred,
                "_sim_idea": _idea, "_sim_hook": _hook, "_sim_dest": _dest,
                "_sim_fmt": _fmt, "_sim_emotion": _emotion, "_sim_caption": _caption,
                "_sim_cta": _cta, "_sim_tier": _tier,
            })
        else:
            st.warning("Please describe a content idea above, or fill in the Content Idea field in Advanced Settings.")

    # ── Results (persist in session state) ───────────────────────────────────
    if "_sim_result" in st.session_state:
        result      = st.session_state["_sim_result"]
        improvement = st.session_state["_sim_improvement"]
        inferred    = st.session_state.get("_sim_inferred", {})
        idea        = st.session_state.get("_sim_idea", "")
        hook        = st.session_state.get("_sim_hook", "")
        destination = st.session_state.get("_sim_dest", "")
        fmt         = st.session_state.get("_sim_fmt", "Reel")
        emotion     = st.session_state.get("_sim_emotion", "")
        caption     = st.session_state.get("_sim_caption", "")
        cta         = st.session_state.get("_sim_cta", "")
        tier        = st.session_state.get("_sim_tier", "")

        st.markdown("---")

        # ── SECTION 1: Inferred Content Brief ────────────────────────────────
        if inferred:
            _tc = {"Tier 1":"#4ade80","Tier 2":"#60a5fa","Tier 3":"#a78bfa","Original":"#f59e0b"}
            _t_col = _tc.get(inferred.get("tier","").split("—")[0].strip(), "#64748b")
            st.markdown("#### 1. Content Brief")
            st.markdown(
                f"<div style='display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.7rem'>"
                f"<span style='background:#1e3a5f;color:#93c5fd;font-size:.78rem;padding:.25rem .65rem;border-radius:20px'>📍 {inferred.get('destination','—')}</span>"
                f"<span style='background:#1e3a5f;color:#93c5fd;font-size:.78rem;padding:.25rem .65rem;border-radius:20px'>🎬 {inferred.get('format','—')}</span>"
                f"<span style='background:#1a2e1a;color:#86efac;font-size:.78rem;padding:.25rem .65rem;border-radius:20px'>🧭 {inferred.get('pillar','—')}</span>"
                f"<span style='background:#2a1a2a;color:#d8b4fe;font-size:.78rem;padding:.25rem .65rem;border-radius:20px'>💫 {inferred.get('emotion','—')}</span>"
                f"<span style='background:#2a1a10;color:#fcd34d;font-size:.78rem;padding:.25rem .65rem;border-radius:20px'>🎯 {inferred.get('cta','—')}</span>"
                f"<span style='background:#1a1a2a;color:#c4b5fd;font-size:.78rem;padding:.25rem .65rem;border-radius:20px'>📐 {inferred.get('pattern','—')}</span>"
                f"<span style='background:#111;border:1px solid {_t_col}44;color:{_t_col};font-size:.78rem;padding:.25rem .65rem;border-radius:20px'>{inferred.get('tier','—')}</span>"
                f"</div>"
                f"<div style='background:#0a1520;border-left:3px solid #1e3a5f;padding:.55rem .9rem;border-radius:0 6px 6px 0;margin-bottom:.3rem'>"
                f"<span style='color:#64748b;font-size:.75rem;font-weight:600'>HOOK DRAFT · </span>"
                f"<span style='color:#e2e8f0;font-size:.85rem;font-style:italic'>{inferred.get('hook','—')}</span>"
                f"</div>"
                f"<div style='background:#0a1520;border-left:3px solid #1e3a5f;padding:.55rem .9rem;border-radius:0 6px 6px 0'>"
                f"<span style='color:#64748b;font-size:.75rem;font-weight:600'>AUDIENCE INTENT · </span>"
                f"<span style='color:#94a3b8;font-size:.82rem'>{inferred.get('intent','—')}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown("")

        # ── SECTION 2: Score Summary ──────────────────────────────────────────
        score_pct = result["total"]
        _s_color  = "#4ade80" if score_pct >= 80 else "#facc15" if score_pct >= 60 else "#fb923c" if score_pct >= 40 else "#f87171"
        _s_label  = ("Strong viral candidate" if score_pct >= 90
                     else "Good idea — needs tightening" if score_pct >= 75
                     else "Usable but not strong yet" if score_pct >= 60
                     else "Needs rework")
        st.markdown("#### 2. Score Summary")
        score_col, rec_col = st.columns([1, 2])
        with score_col:
            st.markdown(
                f"<div style='background:#111827;border:2px solid {_s_color};border-radius:12px;"
                f"padding:1.5rem;text-align:center'>"
                f"<div style='font-size:3.5rem;font-weight:800;color:{_s_color}'>{score_pct}</div>"
                f"<div style='color:#64748b;font-size:.9rem;margin-top:.25rem'>out of 100</div>"
                f"<div style='color:{_s_color};font-size:.8rem;font-weight:700;margin-top:.4rem;letter-spacing:.03em'>{_s_label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with rec_col:
            st.markdown(
                f"<div style='background:#111827;border:1px solid #1e3a5f;border-radius:12px;"
                f"padding:1.5rem;height:100%'>"
                f"<div style='color:#94a3b8;font-size:.8rem;font-weight:600;letter-spacing:.07em;text-transform:uppercase'>Recommendation</div>"
                f"<div style='font-size:1.3rem;font-weight:700;margin-top:.4rem;color:{result['rec_color']}'>{result['recommendation']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("")
        with st.expander("📊 Criterion Breakdown", expanded=False):
            score_rows = []
            for criterion, (pts, note) in result["scores"].items():
                max_pts = _crit_max(criterion)
                score_rows.append({"Criterion": criterion, "Score": pts, "Max": max_pts, "Notes": note})
            score_df = pd.DataFrame(score_rows)
            fig = px.bar(
                score_df, x="Score", y="Criterion", orientation="h",
                template=PLOTLY_TMPL, color="Score",
                color_continuous_scale=["#f87171","#facc15","#4ade80"],
                range_color=[0, 20], text="Score",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(score_df[["Criterion","Score","Max","Notes"]], use_container_width=True, hide_index=True)

        # ── SECTION 3: Why This Works ─────────────────────────────────────────
        _strengths = [(c, pts, note) for c, (pts, note) in result["scores"].items()
                      if pts >= _crit_max(c) * 0.75]
        _dest_show  = destination or (inferred.get("destination","") if inferred else "this destination")
        _fmt_show   = fmt or (inferred.get("format","") if inferred else "this format")
        _emot_show  = emotion or (inferred.get("emotion","") if inferred else "curiosity and longing")
        _pillar_show = inferred.get("pillar","travel content") if inferred else "travel content"
        st.markdown("#### 3. Why This Works")
        _why_lines = []
        if any("Ocean" in p or "Island" in p for p in [_pillar_show]):
            _why_lines.append(f"**Ocean authority signal** — Sofia's real diving experience in {_dest_show} makes this non-replicable by generic travel accounts.")
        if "Founder" in _pillar_show or "founder" in (idea or "").lower():
            _why_lines.append("**Founder credibility** — personal story format builds trust faster than brand content. Audiences engage with real people, not brands.")
        if "transform" in _emot_show.lower() or "awe" in _emot_show.lower() or "intense" in _emot_show.lower():
            _why_lines.append(f"**High-emotion arc** — `{_emot_show}` is a proven viral emotional structure. Audiences save or share content that gives them a feeling they want to revisit.")
        if "Curiosity" in (inferred.get("pattern","") if inferred else ""):
            _why_lines.append("**Curiosity-gap hook** — creates an information gap that drives swipe/watch behavior. One of the highest-converting hook types in the reference group.")
        if "Carousel" in _fmt_show:
            _why_lines.append("**Carousel format** — saveable content with specific insider knowledge has the highest organic reach potential in Avalon's format mix.")
        if "Reel" in _fmt_show:
            _why_lines.append(f"**Reel format** — first-3-seconds stop-scroll potential. {_dest_show} underwater or dramatic footage can generate replay loops.")
        if _strengths:
            best = max(_strengths, key=lambda x: x[1])
            _why_lines.append(
                f"**Strong scoring signal** — highest-scoring dimension: "
                f"`{best[0]}` ({best[1]}/{_crit_max(best[0])})."
                if best else
                "**Strong scoring signal** — this idea has clear Avalon alignment through its destination, emotion, hook, and CTA."
            )
        if not _why_lines:
            _why_lines.append(f"This idea touches a strong Avalon content pillar ({_pillar_show}). Specificity and a sharper hook will unlock its full potential.")
        for line in _why_lines:
            st.markdown(
                f"<div style='background:#0a1520;border-left:3px solid #1e4d7f;border-radius:0 6px 6px 0;"
                f"padding:.5rem .9rem;margin-bottom:.3rem;font-size:.86rem;color:#94a3b8'>{line}</div>",
                unsafe_allow_html=True,
            )

        # ── SECTION 4: Weak Points ────────────────────────────────────────────
        weak = [(c, pts, note) for c, (pts, note) in result["scores"].items()
                if pts < _crit_max(c) * 0.6]
        st.markdown("#### 4. Weak Points")
        if weak:
            for criterion, pts, note in weak:
                max_pts = _crit_max(criterion)
                st.markdown(
                    f"<div style='background:#1a0e0e;border:1px solid #7f1d1d;border-radius:8px;"
                    f"padding:.6rem 1rem;margin-bottom:.35rem'>"
                    f"<span style='color:#fca5a5;font-size:.77rem;font-weight:700;letter-spacing:.05em'>⚠️ {criterion} — {pts}/{max_pts}</span>"
                    f"<div style='color:#f87171;font-size:.83rem;margin-top:.2rem'>{note}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div style='background:#0a1f0a;border:1px solid #1a4a1a;border-radius:8px;"
                "padding:.6rem 1rem;color:#86efac;font-size:.85rem'>✅ No major weak points. Focus on execution quality and visual specificity.</div>",
                unsafe_allow_html=True,
            )

        # ── SECTION 5: Improved Version ───────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 5. Improved Version")
        proj_score = improvement["projected_score"]
        proj_color = "#4ade80" if proj_score >= 80 else "#facc15" if proj_score >= 60 else "#fb923c"
        st.markdown(
            f"Projected score with improvements: "
            f"<b style='color:{proj_color};font-size:1.1rem'>{proj_score}/100</b>",
            unsafe_allow_html=True,
        )

        imp_t1, imp_t2, imp_t3, imp_t4 = st.tabs(["🪝 5 Hooks", "🎬 Reel / Slide Structure", "📣 3 CTAs", "#️⃣ Hashtags"])

        with imp_t1:
            for i, h in enumerate(improvement["hooks"], 1):
                tn = str(h.get("tier_num", 2))
                tc = f"t{tn}"
                st.markdown(
                    f"<div class='ac'>"
                    f"<h4>Hook {i} &nbsp;<span class='{tc}'>{h['tier']}</span></h4>"
                    f"<p style='color:#e2e8f0;font-size:.97rem;font-style:italic'>"
                    f"&ldquo;{h['text']}&rdquo;</p>"
                    f"<p style='font-size:.78rem;color:#64748b;margin-top:.3rem'>Pattern: {h['pattern']}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        with imp_t2:
            st.markdown("**Best-fit structure based on matched patterns:**")
            st.code(improvement["reel_structure"], language=None)
            if inferred and inferred.get("visual"):
                st.markdown(
                    f"<div style='background:#0f172a;border-left:3px solid #c9a84c;border-radius:0 6px 6px 0;"
                    f"padding:.55rem .9rem;margin-top:.5rem;font-size:.85rem;color:#fde68a'>"
                    f"<b>Suggested visual direction:</b> {inferred['visual']}</div>",
                    unsafe_allow_html=True,
                )

        with imp_t3:
            for c in improvement["ctas"]:
                st.markdown(f"→ {c}")

        with imp_t4:
            hashtag_str = "  ".join(improvement["hashtags"])
            st.text_area("Copy this hashtag set:", value=hashtag_str, height=75, label_visibility="visible")
            st.caption("1–3 highly targeted hashtags often outperform generic hashtag spam.")

        # ── SECTION 6: Save / Use Actions ─────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 6. Save & Use")
        act_col1, act_col2, act_col3 = st.columns(3)

        with act_col1:
            if st.button("♡  Save to Idea Vault", key="sim_save_vault", use_container_width=True):
                _vault_entry = {
                    "title":       (idea or brief_text)[:80],
                    "brief":       brief_text,
                    "format":      fmt or (inferred.get("format","") if inferred else ""),
                    "destination": destination or (inferred.get("destination","") if inferred else ""),
                    "pillar":      inferred.get("pillar","") if inferred else "",
                    "hook":        hook or (inferred.get("hook","") if inferred else ""),
                    "cta":         cta or (inferred.get("cta","") if inferred else ""),
                    "score":       score_pct,
                    "status":      "Liked",
                    "priority":    "Medium",
                    "source":      "Content Simulator",
                    "notes":       "",
                }
                if _save_to_idea_vault(_vault_entry):
                    st.success("Saved to data/content_idea_vault.json ✓")
                else:
                    st.error("Could not save — check data/ folder permissions.")

        with act_col2:
            _dl_content = f"# Avalon Content Idea\n\n**Brief:** {brief_text}\n\n**Score:** {score_pct}/100 — {_s_label}\n\n**Hook:** {hook or (inferred.get('hook','') if inferred else '')}\n\n**CTA:** {cta or (inferred.get('cta','') if inferred else '')}\n\n**Format:** {fmt}\n\n**Destination:** {destination}\n\n## Improved Hooks\n" + "\n".join(f"- {h['text']}" for h in improvement["hooks"]) + f"\n\n## Hashtags\n{hashtag_str if 'hashtag_str' in dir() else ''}\n"
            st.download_button(
                "📋 Download as Markdown",
                data=_dl_content,
                file_name=f"avalon_idea_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                key="sim_dl_md",
                use_container_width=True,
            )

        with act_col3:
            # TODO: "Turn into Carousel" → pre-fill Carousel Builder with these values
            # TODO: "Turn into Reel Script" → generate full Reel script structure
            # TODO: "Add to Weekly Plan" → pre-fill next available day in calendar
            st.markdown(
                "<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;"
                "padding:.5rem .8rem;text-align:center;color:#475569;font-size:.75rem'>"
                "🔜 Turn into Carousel / Reel Script / Add to Plan — coming soon</div>",
                unsafe_allow_html=True,
            )

        # ── Reference-Based Improvement (detailed — collapsible) ──────────────
        st.markdown("---")
        with st.expander("📚 Pattern Reference — Viral Group Analysis", expanded=False):
            st.markdown(
                "<p style='color:#64748b;font-size:.83rem'>"
                "Rule-based analysis from the Viral Influencer Trend Reference Group. "
                "Use these to inform structure — not to copy content.</p>",
                unsafe_allow_html=True,
            )

        matched_pats = improvement["matched_patterns"]
        creators     = improvement["relevant_creators"]

        st.markdown("**Matching Viral Patterns**")
        if matched_pats:
            for pattern, score in matched_pats:
                tc = f"t{pattern['tier']}"
                st.markdown(
                    f"<div class='ac'>"
                    f"<h4><span class='{tc}'>{pattern['tier_label']}</span> &nbsp; {pattern['name']}</h4>"
                    f"<p>{pattern['caption_structure']}</p>"
                    f"<p style='margin-top:.5rem;color:#64748b;font-size:.8rem'>"
                    f"Reference accounts: {', '.join('@'+a for a in pattern['accounts'])}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No strong pattern match. Add more detail to the idea, hook, or caption to get specific suggestions.")

        if creators:
            st.markdown("**Most Relevant Reference Creators**")
            crows = []
            for c in creators:
                crows.append({
                    "Creator":   c["handle"],
                    "Followers": fmt_number(c["follower_count"]) if c["follower_count"] else "—",
                    "Niche":     c["niche"],
                    "Pattern":   c["pattern_name"],
                    "Adaptation": c["tier_label"],
                    "Strength":  c["ref_strength"],
                })
            st.dataframe(pd.DataFrame(crows), use_container_width=True, hide_index=True)
            for c in creators[:2]:
                if c["why_relevant"]:
                    st.markdown(
                        f"<div class='ac'><h4>{c['handle']}</h4>"
                        f"<p>{c['why_relevant']}</p></div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("**How to Adapt for Avalon**")
        guide = improvement["caption_guide"]
        st.markdown(
            f"<div class='ac'>"
            f"<h4>Caption structure — {guide['pattern_used']}</h4>"
            f"<p>{guide['structure']}</p>"
            f"<br><b style='color:#e2e8f0;font-size:.85rem'>Visual direction:</b>"
            f"<p>{guide['visual']}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("**What NOT to Copy**")
        for w in improvement["warnings"]:
            st.markdown(
                f"<div style='background:#1a0e0e;border:1px solid #7f1d1d;border-radius:8px;"
                f"padding:.75rem 1.1rem;margin-bottom:.45rem'>"
                f"<span style='color:#fca5a5;font-size:.78rem;font-weight:700;letter-spacing:.05em'>"
                f"{w['pattern'].upper()}</span><br>"
                f"<span style='color:#f87171;font-size:.86rem'>{w['warning']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── Format-Specific Advice ────────────────────────────────────────────
        st.markdown("---")
        fa = improvement.get("format_advice", {})
        fa_fmt = fa.get("format", "")

        if fa_fmt == "Carousel":
            st.markdown("**Carousel Improvement Ideas**")
            st.caption(
                "⚠️ **Public data note:** Save counts, share counts, reach, and impressions are "
                "not available from public Instagram scraping. Carousel scoring uses text-based "
                "proxies (guide/list keywords, first-slide length). Upload an Instagram analytics "
                "CSV to `data/analytics/` to unlock full carousel performance data."
            )
            cp = fa.get("carousel_plan", {})
            if cp:
                c6a, c6b = st.columns([2, 1])
                with c6a:
                    st.markdown(f"**Type:** {cp.get('type','—')}  &nbsp;·&nbsp;  **Slides:** {cp.get('slide_count','—')}", unsafe_allow_html=True)

                with c6b:
                    st.markdown(
                        f"<div style='background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;"
                        f"padding:.6rem .9rem;font-size:.82rem;color:#64748b'>"
                        f"Reference: @travelcroats — PRIMARY CAROUSEL REFERENCE in the group."
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown("**① First-slide hook**")
                st.markdown(
                    f"<div style='background:#0f2027;border-left:3px solid #00b4d8;border-radius:6px;"
                    f"padding:.65rem 1rem;font-size:.92rem;color:#e2e8f0;font-style:italic'>"
                    f"{cp.get('first_slide_hook','—')}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("**② Suggested slide sequence**")
                for slide in cp.get("slides", []):
                    st.markdown(
                        f"<div style='background:#0f172a;border-radius:6px;padding:.45rem .9rem;"
                        f"margin-bottom:.3rem;font-size:.85rem;color:#94a3b8'>{slide}</div>",
                        unsafe_allow_html=True,
                    )

                col_s, col_sh = st.columns(2)
                with col_s:
                    st.markdown("**③ Save trigger**")
                    st.markdown(
                        f"<div style='background:#0f2027;border-left:3px solid #4ade80;border-radius:6px;"
                        f"padding:.6rem .9rem;font-size:.88rem;color:#86efac'>"
                        f"{cp.get('save_trigger','—')}</div>",
                        unsafe_allow_html=True,
                    )
                with col_sh:
                    st.markdown("**④ Share trigger**")
                    st.markdown(
                        f"<div style='background:#0f2027;border-left:3px solid #a78bfa;border-radius:6px;"
                        f"padding:.6rem .9rem;font-size:.88rem;color:#c4b5fd'>"
                        f"{cp.get('share_trigger','—')}</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown("**⑤ Caption angle**")
                st.markdown(
                    f"<div style='background:#0f172a;border-radius:6px;padding:.6rem .9rem;"
                    f"font-size:.88rem;color:#94a3b8'>{cp.get('caption_angle','—')}</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("**⑥ CTA**")
                st.markdown(f"> {cp.get('cta','—')}")

                st.markdown("**⑦ Why this could work for Avalon**")
                st.markdown(
                    f"<div style='background:#0f2027;border-left:3px solid #c9a84c;border-radius:6px;"
                    f"padding:.65rem 1rem;font-size:.88rem;color:#fde68a'>"
                    f"{cp.get('why_it_works','—')}</div>",
                    unsafe_allow_html=True,
                )

        elif fa_fmt == "Reel":
            st.markdown("**Reel Format Advice**")
            st.caption(
                "⚠️ **Public data note:** Share counts, saves, reach, and impressions are not "
                "available from public scraping. Reel scoring primarily uses plays/views and "
                "comment depth as proxies."
            )
            reel_fields = [
                ("First 3-second hook",   fa.get("first_3s_hook", "—")),
                ("Visual sequence",        fa.get("visual_sequence", "—")),
                ("On-screen text",         fa.get("text_overlay", "—")),
                ("Pacing",                 fa.get("pacing", "—")),
                ("Audio angle",            fa.get("audio_angle", "—")),
                ("Share trigger",          fa.get("share_trigger", "—")),
                ("Key metric to watch",    fa.get("key_metric", "—")),
            ]
            for label, value in reel_fields:
                st.markdown(f"**{label}**")
                if "\n" in value:
                    st.code(value, language=None)
                else:
                    st.markdown(
                        f"<div style='background:#0f172a;border-radius:6px;padding:.5rem .9rem;"
                        f"font-size:.88rem;color:#94a3b8;margin-bottom:.4rem'>{value}</div>",
                        unsafe_allow_html=True,
                    )

        elif fa_fmt == "Photo":
            st.markdown("**Photo Format Advice**")
            st.caption(
                "⚠️ **Public data note:** Save counts, shares, reach, and impressions are not "
                "available from public scraping. Photo scoring uses likes + comments + caption length."
            )
            photo_fields = [
                ("Caption angle",            fa.get("caption_angle", "—")),
                ("Emotional framing",         fa.get("emotional_framing", "—")),
                ("Visual + caption pairing",  fa.get("visual_caption_pairing", "—")),
                ("Comment prompt",            fa.get("comment_prompt", "—")),
                ("Key metric to watch",       fa.get("key_metric", "—")),
            ]
            for label, value in photo_fields:
                st.markdown(f"**{label}**")
                st.markdown(
                    f"<div style='background:#0f172a;border-radius:6px;padding:.5rem .9rem;"
                    f"font-size:.88rem;color:#94a3b8;margin-bottom:.4rem'>{value}</div>",
                    unsafe_allow_html=True,
                )

        else:
            if fa.get("note"):
                st.info(f"Format advice: {fa['note']}")

        # ── Professional Marketing Lens ───────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 7. Professional Marketing Lens")
        st.caption("Which marketing skill applies, how it improves this content, and a GOAL framework diagnosis.")

        _full = " ".join(filter(None, [idea, hook, caption, destination, emotion]))
        skill = match_marketing_skill(fmt, infer_pillar(_full), idea)
        diag  = generate_goal_diagnosis(idea, hook, caption, destination, fmt, cta)

        pm_a, pm_b = st.columns([1, 1])
        with pm_a:
            st.markdown(
                f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;"
                f"padding:.75rem 1rem;height:100%'>"
                f"<div style='font-size:.72rem;color:#475569;letter-spacing:.07em;text-transform:uppercase'>Most Relevant Skill</div>"
                f"<div style='font-size:1rem;font-weight:700;color:#e2e8f0;margin:.3rem 0'>{skill['icon']} {skill['name']}</div>"
                f"<div style='font-size:.83rem;color:#94a3b8'>{skill['one_liner']}</div>"
                f"<div style='font-size:.8rem;color:#475569;margin-top:.5rem'><b style='color:#64748b'>Frameworks:</b> "
                f"{' · '.join(skill['key_frameworks'][:2])}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with pm_b:
            st.markdown(
                f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;"
                f"padding:.75rem 1rem;height:100%'>"
                f"<div style='font-size:.72rem;color:#475569;letter-spacing:.07em;text-transform:uppercase'>Avalon Application</div>"
                f"<div style='font-size:.85rem;color:#94a3b8;margin-top:.3rem'>{skill['avalon_application']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("**GOAL Diagnosis** — how well does this content satisfy each dimension?")
        diag_cols = st.columns(4)
        for col, (dim_key, label) in zip(diag_cols, [("goal","G — Goal"),("objective","O — Obj."),("assets","A — Assets"),("layout","L — Layout")]):
            d = diag[dim_key]
            with col:
                st.markdown(
                    f"<div style='background:#0d1117;border:1px solid {d['color']}44;"
                    f"border-radius:8px;padding:.5rem .65rem;text-align:center'>"
                    f"<div style='font-size:.66rem;color:#475569;text-transform:uppercase'>{label}</div>"
                    f"<div style='font-size:.95rem;font-weight:700;color:{d['color']};margin:.1rem 0'>{d['label']}</div>"
                    f"<div style='font-size:.7rem;color:#64748b'>{d['tip']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Generate GOAL prompt from simulator inputs
        with st.expander("🎯 Generate GOAL prompt from these inputs", expanded=False):
            sim_mode = st.selectbox("Advanced Mode", list(ADVANCED_PROMPT_MODES.keys()), key="sim_goal_mode")
            if st.button("Generate GOAL prompt", key="sim_gen_goal"):
                assets_text = AVALON_CONTEXT_BLOCK + f"\n\nDestination: {destination or 'not specified'}\nFormat: {fmt or 'not specified'}\nEmotion: {emotion or 'not specified'}\nCurrent hook: {hook or 'not specified'}\nCaption draft: {caption or '(none)'}\nCTA: {cta or 'not specified'}"
                prompt = generate_goal_prompt(
                    goal=f"Create a strong, ready-to-post piece of Avalon Escapes Instagram content: {idea or 'content idea'}",
                    objective=f"Format: {fmt or 'not specified'}. Score 80+/100. Keyword CTA. Preserve emotional core.",
                    assets=assets_text,
                    layout="Output: improved hook, caption (short punchy stanzas, 100–130 words), CTA, visual direction, tier label.",
                    mode=sim_mode,
                )
                st.session_state["sim_goal_prompt"] = prompt
            if st.session_state.get("sim_goal_prompt"):
                st.text_area("Copy →", value=st.session_state["sim_goal_prompt"], height=300, key="sim_goal_display", label_visibility="collapsed")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: WEEKLY CONTENT PLAN
# ─────────────────────────────────────────────────────────────────────────────
def page_content_plan():
    st.markdown("## 📅 Weekly Content Calendar")

    # ── Initialise session state ──────────────────────────────────────────────
    _ensure_wc_state()

    # ── Action bar ────────────────────────────────────────────────────────────
    btn1, btn2, btn3, btn4 = st.columns([1, 1.3, 1.5, 1])

    with btn1:
        if st.button("💾 Save plan", use_container_width=True, type="primary"):
            _wc_save_json(_wc_collect())
            st.success("Saved → content_plans/weekly_calendar.json")

    with btn2:
        if st.button("✨ Load sample week", use_container_width=True):
            _wc_load_sample()
            st.rerun()

    with btn3:
        md_data = _wc_export_markdown()
        fname   = f"avalon_weekly_{datetime.now().strftime('%Y%m%d')}.md"
        st.download_button(
            "📋 Export as Markdown",
            data=md_data,
            file_name=fname,
            mime="text/markdown",
            use_container_width=True,
        )

    with btn4:
        if st.button("🗑️ Clear plan", use_container_width=True):
            st.session_state["_wc_pending_clear"] = True

    # Confirmation for clear
    if st.session_state.get("_wc_pending_clear"):
        st.warning("This will erase all 7 days. This cannot be undone unless you saved first.")
        cc1, cc2, _ = st.columns([1, 1, 5])
        with cc1:
            if st.button("✅ Yes, clear", key="_wc_confirm_yes"):
                _wc_load_defaults()
                _wc_save_json(default_weekly_calendar())
                st.session_state["_wc_pending_clear"] = False
                st.rerun()
        with cc2:
            if st.button("Cancel", key="_wc_confirm_no"):
                st.session_state["_wc_pending_clear"] = False
                st.rerun()

    st.markdown("---")

    # ── Weekly overview bar ───────────────────────────────────────────────────
    ov = _wc_overview()
    tp = ov["top_pillar"]
    td = ov["top_dest"]
    ov_cols = st.columns(6)
    for col, (label, val, color) in zip(ov_cols, [
        ("Planned",   str(ov["planned"]),          "#00b4d8"),
        ("Ready",     str(ov["ready"]),             "#4ade80"),
        ("Draft",     str(ov["draft"]),             "#facc15"),
        ("Empty",     str(ov["empty"]),             "#475569"),
        ("Top pillar", tp[:14] + "…" if len(tp) > 15 else tp, "#a78bfa"),
        ("Top dest",  td[:14] + "…" if len(td) > 15 else td,  "#c9a84c"),
    ]):
        with col:
            st.markdown(
                f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;"
                f"padding:.55rem .65rem;text-align:center'>"
                f"<div style='font-size:.68rem;color:#475569;letter-spacing:.07em;"
                f"text-transform:uppercase;margin-bottom:.1rem'>{label}</div>"
                f"<div style='font-size:1.05rem;font-weight:700;color:{color}'>{val or '—'}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── 7-day calendar grid (2-column) ────────────────────────────────────────
    for pair in [(0, 1), (2, 3), (4, 5)]:
        left_col, right_col = st.columns(2, gap="large")
        with left_col:
            _render_wc_day(pair[0])
        with right_col:
            _render_wc_day(pair[1])
        st.markdown("<hr style='border-color:#1e293b;margin:1.2rem 0'>",
                    unsafe_allow_html=True)

    # Day 7 — Sunday (full width)
    _render_wc_day(6)

    st.markdown("---")

    # ── Save reminder ─────────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;"
        "padding:.6rem 1rem;font-size:.82rem;color:#64748b'>"
        "💾 Changes are <b style='color:#e2e8f0'>not saved automatically</b>. "
        "Click <b style='color:#00b4d8'>Save plan</b> above to persist your edits to "
        "<code>content_plans/weekly_calendar.json</code>."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Generated plan notes (legacy) ────────────────────────────────────────
    plan_files = sorted(
        [f for f in CONTENT_PLANS.glob("*.md") if f.name != "template.md"],
        reverse=True,
    )
    if plan_files:
        st.markdown("---")
        with st.expander("📄 Generated Plan Notes (AI-generated Markdown files)", expanded=False):
            plan_labels = [f.stem for f in plan_files]
            selected    = st.selectbox("Select plan", plan_labels, key="legacy_plan_select")
            chosen      = plan_files[plan_labels.index(selected)]
            content     = safe_load_markdown(chosen)
            if content:
                st.markdown(content)
            else:
                st.error("Could not read plan file.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PROFESSIONAL FRAMEWORKS & PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def page_frameworks():
    st.markdown("## 🧠 Professional Frameworks & Prompt Builder")
    st.caption(
        "Combines the **Viral Influencer Trend Reference Group** with the "
        "**Professional Marketing Skills Layer** and the **GOAL Prompt Framework** "
        "to generate structured, brand-aligned prompts you can paste directly into Claude."
    )

    tab_goal, tab_templates, tab_skill, tab_context = st.tabs([
        "🎯 GOAL Prompt Builder",
        "📋 Prompt Templates",
        "🔬 Professional Skill Lens",
        "📘 Avalon Context Builder",
    ])

    # ── Tab 1: GOAL Prompt Builder ────────────────────────────────────────────
    with tab_goal:
        st.markdown("### GOAL Prompt Builder")
        st.markdown(
            "Fill in the four sections of the **GOAL framework** to generate a "
            "structured, Avalon-specific prompt for any content task."
        )
        st.markdown(
            "<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;"
            "padding:.6rem 1rem;margin-bottom:1rem;font-size:.82rem;color:#64748b'>"
            "<b style='color:#e2e8f0'>G</b> = Goal &nbsp;·&nbsp; "
            "<b style='color:#e2e8f0'>O</b> = Objective &nbsp;·&nbsp; "
            "<b style='color:#e2e8f0'>A</b> = Assets &nbsp;·&nbsp; "
            "<b style='color:#e2e8f0'>L</b> = Layout &nbsp;&nbsp; "
            "Vague prompts get generic output. GOAL prompts get Avalon-specific output."
            "</div>",
            unsafe_allow_html=True,
        )

        adv_mode = st.selectbox(
            "Advanced Prompt Mode",
            list(ADVANCED_PROMPT_MODES.keys()),
            key="fw_adv_mode",
        )
        st.caption(f"_{ADVANCED_PROMPT_MODES[adv_mode]['description']}_")

        g_val = st.text_area(
            "🎯 Goal — What outcome are you working toward?",
            key="fw_goal",
            height=80,
            placeholder="e.g. Drive DM inquiries for our Maldives diving trips through a 60-second Reel on @avalon.escapes.",
        )
        o_val = st.text_area(
            "📏 Objective — What does success look like? What must the output satisfy?",
            key="fw_objective",
            height=80,
            placeholder="e.g. Hook under 8 words. Caption 100–130 words. Keyword CTA. Tier 2 pattern. No corporate language.",
        )

        use_default_assets = st.checkbox("Include Avalon default assets block", value=True, key="fw_use_defaults")
        extra_assets = st.text_area(
            "🧰 Assets — Additional context (destination, creator reference, emotion target, notes)",
            key="fw_assets_extra",
            height=120,
            placeholder="e.g. Destination: Fuvahmulah, Maldives. Emotion: awe + FOMO. Reference pattern: curiosity-gap (Tier 2, @noareserrunt + @colinduthie).",
        )
        assets_combined = (AVALON_CONTEXT_BLOCK + "\n\n" + extra_assets if use_default_assets else extra_assets)

        l_val = st.text_area(
            "🖼️ Layout — Format, structure, sections, length, and output style",
            key="fw_layout",
            height=80,
            placeholder="e.g. Output: (1) hook (2) visual sequence with timestamps (3) caption — short stanzas (4) keyword CTA (5) tier label.",
        )

        if st.button("✨ Generate GOAL Prompt", type="primary", key="fw_gen_btn"):
            if not (g_val or o_val or l_val):
                st.warning("Fill in at least Goal and Layout to generate a meaningful prompt.")
            else:
                prompt = generate_goal_prompt(g_val, o_val, assets_combined, l_val, adv_mode)
                st.session_state["fw_generated_prompt"] = prompt

        if st.session_state.get("fw_generated_prompt"):
            st.markdown("---")
            st.markdown("**Generated Prompt — copy and paste into Claude:**")
            st.text_area(
                "Copy this prompt →",
                value=st.session_state["fw_generated_prompt"],
                height=380,
                key="fw_prompt_output",
                label_visibility="collapsed",
            )
            st.caption(
                "Tip: In the terminal, type `! ` followed by this prompt, or paste it into a new Claude conversation. "
                "The more detail you put in Assets, the better the output."
            )

    # ── Tab 2: Prompt Templates ───────────────────────────────────────────────
    with tab_templates:
        st.markdown("### Prompt Templates")
        st.markdown(
            "Pre-built GOAL prompts for the most common Avalon content tasks. "
            "Select one, review and edit the fields, then generate."
        )

        template_names = {t["id"]: f"{t['icon']} {t['name']}" for t in PROMPT_TEMPLATES}
        selected_id = st.selectbox(
            "Select a template",
            list(template_names.keys()),
            format_func=lambda x: template_names[x],
            key="fw_template_select",
        )
        tpl = next(t for t in PROMPT_TEMPLATES if t["id"] == selected_id)

        st.markdown(f"**{tpl['icon']} {tpl['name']}**")

        tpl_goal = st.text_area("🎯 Goal", value=tpl["goal"], height=75, key="fw_tpl_goal")
        tpl_obj  = st.text_area("📏 Objective", value=tpl["objective"], height=75, key="fw_tpl_obj")
        tpl_assets = st.text_area("🧰 Assets (edit to add your specific details)", value=tpl["assets"], height=180, key="fw_tpl_assets")
        tpl_layout = st.text_area("🖼️ Layout", value=tpl["layout"], height=75, key="fw_tpl_layout")

        tpl_mode = st.selectbox("Advanced Mode", list(ADVANCED_PROMPT_MODES.keys()), key="fw_tpl_mode")

        if st.button("✨ Generate from Template", type="primary", key="fw_tpl_gen"):
            prompt = generate_goal_prompt(tpl_goal, tpl_obj, tpl_assets, tpl_layout, tpl_mode)
            st.session_state["fw_tpl_prompt"] = prompt

        if st.session_state.get("fw_tpl_prompt"):
            st.markdown("---")
            st.text_area(
                "Copy this prompt →",
                value=st.session_state["fw_tpl_prompt"],
                height=380,
                key="fw_tpl_output",
                label_visibility="collapsed",
            )

    # ── Tab 3: Professional Skill Lens ────────────────────────────────────────
    with tab_skill:
        st.markdown("### Professional Skill Lens")
        st.markdown(
            "Enter a content idea and select a format — the system identifies which "
            "professional marketing skill applies most and explains how to use it."
        )

        sl_fmt  = st.selectbox("Format", CONTENT_FORMATS[1:], key="sl_fmt")
        sl_dest = st.selectbox("Destination", DESTINATIONS_LIST[1:], key="sl_dest")
        sl_idea = st.text_input("Content idea", key="sl_idea", placeholder="e.g. Show the real Maldives vs the overwater bungalow version")
        sl_hook = st.text_input("Current hook (optional)", key="sl_hook", placeholder="e.g. No one prepares you for Fuvahmulah.")
        sl_cta  = st.text_input("CTA (optional)", key="sl_cta", placeholder="e.g. Comment 'FUVA' for our guide →")
        sl_cap  = st.text_area("Caption draft (optional)", key="sl_cap", height=80, placeholder="Paste your draft caption here...")

        if st.button("🔬 Analyse with Marketing Skill Lens", key="sl_analyse"):
            skill = match_marketing_skill(sl_fmt, "", sl_idea)
            diagnosis = generate_goal_diagnosis(sl_idea, sl_hook, sl_cap, sl_dest, sl_fmt, sl_cta)
            st.session_state["sl_result"] = {"skill": skill, "diagnosis": diagnosis}

        if st.session_state.get("sl_result"):
            skill = st.session_state["sl_result"]["skill"]
            diag  = st.session_state["sl_result"]["diagnosis"]

            st.markdown("---")
            st.markdown(f"#### {skill['icon']} Most Relevant Skill: {skill['name']}")
            st.markdown(
                f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;"
                f"padding:.75rem 1.1rem;margin-bottom:.8rem'>"
                f"<p style='color:#94a3b8;font-size:.88rem;margin:0 0 .5rem'>{skill['one_liner']}</p>"
                f"<p style='color:#64748b;font-size:.78rem;margin:0'>"
                f"<b style='color:#475569'>Avalon application:</b> {skill['avalon_application']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            st.markdown("**Key frameworks to apply:**")
            for fw in skill["key_frameworks"]:
                st.markdown(f"- {fw}")

            st.markdown("**Core principles for this piece:**")
            for p in skill["core_principles"]:
                st.markdown(
                    f"<div style='background:#0d1117;border-left:3px solid #334155;"
                    f"border-radius:0 4px 4px 0;padding:.3rem .75rem;margin-bottom:.25rem;"
                    f"font-size:.85rem;color:#94a3b8'>{p}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("#### 🎯 GOAL Framework Diagnosis")
            st.caption("How well does your current content input satisfy each GOAL dimension?")

            g_cols = st.columns(4)
            for col, (dim_key, label) in zip(g_cols, [("goal","G — Goal"),("objective","O — Objective"),("assets","A — Assets"),("layout","L — Layout")]):
                d = diag[dim_key]
                with col:
                    st.markdown(
                        f"<div style='background:#0f172a;border:1.5px solid {d['color']}44;"
                        f"border-radius:8px;padding:.6rem .7rem;text-align:center'>"
                        f"<div style='font-size:.7rem;color:#475569;text-transform:uppercase;letter-spacing:.06em'>{label}</div>"
                        f"<div style='font-size:1.15rem;font-weight:700;color:{d['color']};margin:.15rem 0'>{d['label']}</div>"
                        f"<div style='font-size:.72rem;color:#64748b;margin-top:.2rem'>{d['tip']}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    # ── Tab 4: Avalon Context Builder ─────────────────────────────────────────
    with tab_context:
        st.markdown("### Avalon Context Builder")
        st.markdown(
            "This is the **Assets (A)** block for every GOAL prompt. "
            "The more accurate it is, the better every AI output becomes."
        )
        ctx_path = ROOT / "reference_frameworks" / "prompting" / "avalon_context_builder.md"
        ctx_content = safe_load_markdown(ctx_path)
        if ctx_content:
            st.markdown(ctx_content)
        else:
            st.warning("Context builder file not found at `reference_frameworks/prompting/avalon_context_builder.md`")

        st.markdown("---")
        st.markdown("**Default Assets Block** (used in every generated GOAL prompt):")
        st.text_area(
            "Copy and customise →",
            value=AVALON_CONTEXT_BLOCK,
            height=200,
            key="fw_ctx_block",
            label_visibility="collapsed",
        )
        st.caption(
            "To update the full context builder, edit "
            "`reference_frameworks/prompting/avalon_context_builder.md` directly."
        )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: AVALON CONTENT STUDIO
# ─────────────────────────────────────────────────────────────────────────────
def page_content_studio():
    st.markdown("## 🎨 Avalon Content Studio")
    st.markdown(
        "<p style='color:#64748b;font-size:.88rem;margin-bottom:1rem'>"
        "Generate carousel copy · improve content ideas · view the weekly plan · "
        "browse Avalon's own post references — all brand-system-first.</p>",
        unsafe_allow_html=True,
    )

    tab_a, tab_b, tab_c, tab_d = st.tabs([
        "🃏 Carousel Builder",
        "✨ Content Improver",
        "📅 Weekly Plan",
        "📁 Own Post References",
    ])

    # ─── A: CAROUSEL BUILDER ─────────────────────────────────────────────────
    with tab_a:
        st.markdown("### 🃏 Carousel Builder — Quick Brief Mode")
        st.markdown(
            "<p style='color:#64748b;font-size:.85rem'>"
            "Describe what you want in plain language — the dashboard infers all parameters automatically.</p>",
            unsafe_allow_html=True,
        )

        brief_text = st.text_area(
            "What carousel do you want to create?",
            placeholder=(
                "e.g. Create a 6-slide Spanish carousel about what Avalon means, "
                "with deep navy ocean overlays, white serif typography, subtle gold details, "
                "mythology, transformation, and a soft CTA to DM us."
            ),
            height=110,
            key="cs_brief_input",
        )

        # ── Auto-parse: update adv-settings session state when brief changes ──
        if brief_text.strip() and brief_text != st.session_state.get("_cs_brief_prev", ""):
            st.session_state["_cs_brief_prev"] = brief_text
            _inf = parse_carousel_brief(brief_text)
            st.session_state["cs_adv_type"]     = _inf["carousel_type"]
            st.session_state["cs_adv_dest"]     = _inf["destination"]
            st.session_state["cs_adv_slides"]   = _inf["slides"]
            st.session_state["cs_adv_goal"]     = _inf["goal"]
            st.session_state["cs_adv_emotion"]  = _inf["emotion"]
            st.session_state["cs_adv_language"] = _inf["language"]
            st.session_state["cs_adv_cta"]      = _inf["cta_style"]
            st.session_state["cs_adv_tags"]     = ", ".join(_inf["photo_tags"][:4])
            st.session_state["cs_adv_needs_ai"] = _inf["needs_ai_brief"]

        # ── Inferred summary card ──────────────────────────────────────────────
        if brief_text.strip():
            _idc = parse_carousel_brief(brief_text)
            st.markdown(
                f"<div style='background:#0a1f0a;border:1px solid #1a4a1a;border-radius:8px;"
                f"padding:.75rem 1.1rem;margin:.3rem 0 .7rem 0'>"
                f"<p style='color:#4ade80;font-weight:700;font-size:.78rem;margin:0 0 .4rem 0'>"
                f"✅ Inferred from your brief — override below if needed</p>"
                f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:.25rem .8rem'>"
                f"<span style='color:#94a3b8;font-size:.78rem'><b style='color:#e2e8f0'>Type:</b> {_idc['carousel_type']}</span>"
                f"<span style='color:#94a3b8;font-size:.78rem'><b style='color:#e2e8f0'>Dest:</b> {_idc['destination']}</span>"
                f"<span style='color:#94a3b8;font-size:.78rem'><b style='color:#e2e8f0'>Slides:</b> {_idc['slides']}</span>"
                f"<span style='color:#94a3b8;font-size:.78rem'><b style='color:#e2e8f0'>Language:</b> {_idc['language']}</span>"
                f"<span style='color:#94a3b8;font-size:.78rem'><b style='color:#e2e8f0'>CTA:</b> {_idc['cta_style']}</span>"
                f"<span style='color:#94a3b8;font-size:.78rem'><b style='color:#e2e8f0'>Goal:</b> {_idc['goal']}</span>"
                f"</div>"
                f"<p style='color:#64748b;font-size:.75rem;margin:.3rem 0 0 0'>"
                f"<b style='color:#94a3b8'>Mood:</b> {_idc['mood']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── Seed defaults for advanced settings on first load ─────────────────
        _type_opts = list(_STUDIO_CAROUSEL_TYPES.keys())
        _dest_opts = list(_STUDIO_DEST_DATA.keys())
        _lang_opts = ["English", "Spanish", "Portuguese"]
        _cta_opts  = list(_CS_CTA_BTNS.keys())
        _adv_defaults = {
            "cs_adv_type":     _type_opts[0],
            "cs_adv_dest":     "Maldives",
            "cs_adv_slides":   6,
            "cs_adv_goal":     "Destination desire + DM inquiry",
            "cs_adv_emotion":  "Curiosity → longing → trust → inquiry",
            "cs_adv_language": "English",
            "cs_adv_cta":      "DM CTA (ESCRÍBENOS)",
            "cs_adv_tags":     "",
            "cs_adv_needs_ai": False,
        }
        for _k, _v in _adv_defaults.items():
            if _k not in st.session_state:
                st.session_state[_k] = _v

        # ── Advanced Settings expander (auto-filled, user-editable) ───────────
        with st.expander("⚙️ Advanced Settings — auto-filled from brief, override if needed"):
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Carousel type", _type_opts, key="cs_adv_type")
                st.selectbox("Destination / category", _dest_opts, key="cs_adv_dest")
                st.slider("Number of slides", min_value=4, max_value=12, key="cs_adv_slides")
            with col2:
                st.selectbox("Language", _lang_opts, key="cs_adv_language")
                st.selectbox("CTA style", _cta_opts, key="cs_adv_cta")
                st.text_input("Goal", key="cs_adv_goal")
                st.text_input("Target emotion", key="cs_adv_emotion")
                st.text_input(
                    "Authorial photo tags (comma-separated)",
                    placeholder="founder_beach_golden_hour, ocean_underwater_coral",
                    key="cs_adv_tags",
                )
                st.checkbox("Include AI image briefs per slide", key="cs_adv_needs_ai")

        # ── Generate button ────────────────────────────────────────────────────
        if st.button("🃏 Generate Carousel Plan", key="cs_gen_btn", type="primary"):
            _type   = st.session_state["cs_adv_type"]
            _dest   = st.session_state["cs_adv_dest"]
            _slides = st.session_state["cs_adv_slides"]
            _goal   = st.session_state["cs_adv_goal"]
            _emot   = st.session_state["cs_adv_emotion"]
            _tags   = st.session_state["cs_adv_tags"]
            _lang   = st.session_state["cs_adv_language"]
            _cta    = st.session_state["cs_adv_cta"]
            _ai     = st.session_state["cs_adv_needs_ai"]

            result = _cs_build_carousel(
                _type, _dest, _goal, _emot, _slides, _tags,
                language=_lang, cta_style=_cta,
            )

            if _ai:
                _arc  = _STUDIO_CAROUSEL_TYPES.get(_type, {}).get("arc", "guide")
                _b    = st.session_state.get("cs_brief_input", "")
                _mood = parse_carousel_brief(_b).get("mood", "Deep navy · premium editorial") if _b.strip() else "Deep navy · premium editorial"
                result += "\n\n---\n\n" + _cs_ai_image_briefs(_slides, _dest, _arc, _mood)

            st.session_state["_cs_result"]    = result
            st.session_state["_cs_dest_slug"] = _dest.lower().replace(" ", "_").replace("/", "_")

        # ── Output area ────────────────────────────────────────────────────────
        if "_cs_result" in st.session_state:
            st.markdown("---")
            st.markdown("#### Generated Carousel Plan")
            st.markdown(st.session_state["_cs_result"])
            st.download_button(
                "📋 Download as Markdown",
                data=st.session_state["_cs_result"],
                file_name=f"avalon_carousel_{st.session_state.get('_cs_dest_slug','custom')}.md",
                mime="text/markdown",
                key="cs_dl",
            )

        st.markdown("---")
        with st.expander("📂 Pre-built carousel drafts (from content_plans/carousel_drafts/)"):
            drafts_dir = CONTENT_PLANS / "carousel_drafts"
            if drafts_dir.exists():
                for f in sorted(drafts_dir.glob("*.md")):
                    if st.button(f"📄 {f.stem.replace('_',' ').title()}", key=f"cs_draft_{f.stem}"):
                        st.session_state["cs_draft_content"] = f.read_text(encoding="utf-8")
                        st.session_state["cs_draft_name"] = f.name
            if "cs_draft_content" in st.session_state:
                st.markdown(f"**{st.session_state.get('cs_draft_name','')}**")
                st.markdown(st.session_state["cs_draft_content"])

    # ─── B: CONTENT IMPROVER ─────────────────────────────────────────────────
    with tab_b:
        st.markdown("### ✨ Content Improver")
        st.markdown(
            "<p style='color:#64748b;font-size:.85rem'>"
            "Paste a content idea → get an Avalon brand fit score, "
            "what's weak, and concrete improvements.</p>",
            unsafe_allow_html=True,
        )

        ci_col1, ci_col2 = st.columns(2)
        with ci_col1:
            ci_idea = st.text_area("Content idea", placeholder="What's the post about?",
                                   height=80, key="ci_idea")
            ci_hook = st.text_input("Draft hook / first line",
                                    placeholder="The first thing someone reads",
                                    key="ci_hook")
            ci_caption = st.text_area("Caption draft (optional)", height=80, key="ci_caption")
        with ci_col2:
            ci_fmt = st.selectbox("Format", ["Carousel","Reel","Photo","Story","Founder Story"],
                                  key="ci_fmt")
            ci_dest = st.selectbox("Destination / category",
                                   ["(none)"] + list(_STUDIO_DEST_DATA.keys()),
                                   key="ci_dest")

        if st.button("✨ Improve This Content", key="ci_gen_btn", type="primary"):
            if not ci_idea.strip():
                st.warning("Add a content idea first.")
            else:
                dest_val = "" if ci_dest == "(none)" else ci_dest
                score, issues, strengths = _cs_brand_fit_score(
                    ci_idea, ci_hook, ci_caption, ci_fmt, dest_val
                )

                # Score display
                score_color = "#16a34a" if score >= 70 else "#d97706" if score >= 50 else "#dc2626"
                st.markdown(
                    f"<div style='background:#111827;border:1px solid #1e3a5f;border-radius:8px;"
                    f"padding:1rem 1.4rem;margin:.8rem 0'>"
                    f"<p style='color:#7ea8c9;font-size:.75rem;font-weight:600;letter-spacing:.07em;"
                    f"text-transform:uppercase;margin:0 0 .4rem 0'>Avalon Brand Fit Score</p>"
                    f"<p style='font-size:2.2rem;font-weight:700;color:{score_color};margin:0'>{score}/100</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                col_s, col_i = st.columns(2)
                with col_s:
                    st.markdown("**✅ Strengths**")
                    if strengths:
                        for s in strengths:
                            st.markdown(f"- {s}")
                    else:
                        st.markdown("*Add more specificity to unlock strengths.*")
                with col_i:
                    st.markdown("**⚠️ Issues to fix**")
                    if issues:
                        for issue in issues:
                            st.markdown(f"- {issue}")
                    else:
                        st.markdown("*No major brand issues detected.*")

                st.markdown("---")
                st.markdown("**Improvement directions:**")

                # Hook improvement
                if ci_hook:
                    st.markdown(f"**Your hook:** *{ci_hook}*")
                    hook_l = ci_hook.lower()
                    if any(w in hook_l for w in ["amazing","magical","stunning","discover","experience"]):
                        dest_str = f" in {dest_val}" if dest_val else ""
                        st.markdown(
                            f"→ **Stronger hook:** Make it specific. "
                            f"Name the place, the detail, the feeling — something only Rafa or Sofia would know{dest_str}."
                        )
                    elif not ci_hook.strip().endswith("?") and len(ci_hook) < 40:
                        st.markdown("→ Hook is short and direct. Consider adding a question or a contrast statement.")

                # Format-specific direction
                st.markdown(f"**Format direction ({ci_fmt}):**")
                fmt_advice = {
                    "Carousel": (
                        "First slide must be a save-worthy hook. "
                        f"Use Montserrat Black + Amore Christmas italic two-layer system. "
                        f"End with full imagotype CTA slide. "
                        f"Caption: personal voice → specific knowledge → save trigger → DM CTA."
                    ),
                    "Reel": (
                        "First 3 seconds are everything. Text overlay + cut to visual impact. "
                        "Audio should support, not compete. "
                        "End with a comment/DM trigger — not a link."
                    ),
                    "Photo": (
                        "One photo, one feeling. Caption should add what the photo can't show — "
                        "the smell, the silence, what happened next. "
                        "End with a question that invites comments."
                    ),
                    "Story": (
                        "Behind-the-scenes energy. Poll or question sticker. "
                        "Speak directly — 'We just landed in...' or 'Sofia is underwater right now.'"
                    ),
                    "Founder Story": (
                        "First person, specific memory. Not 'travel is amazing'. "
                        "The exact thing that happened. The specific place. The exact feeling. "
                        "Only Rafa or Sofia could write this."
                    ),
                }
                st.markdown(fmt_advice.get(ci_fmt, ""))

                # Visual direction
                if dest_val and dest_val in _STUDIO_DEST_DATA:
                    dd = _STUDIO_DEST_DATA[dest_val]
                    st.markdown(f"**Visual direction for {dest_val}:**")
                    st.markdown(
                        f"Navy `#0F2649` overlay on authorial {dest_val} photography. "
                        f"Featured places: {', '.join(dd['places'][:3])}. "
                        f"Suggested photo tags: {', '.join(f'`{t}`' for t in dd['photo_tags'])}."
                    )

                # Brand voice reminder
                st.markdown("**Brand voice check:** Does this sound like Rafa or Sofia wrote it? "
                             "Does it feel like it costs money?")

    # ─── C: WEEKLY PLAN ──────────────────────────────────────────────────────
    with tab_c:
        st.markdown("### 📅 Generated Weekly Content Plan")
        st.markdown(
            "<p style='color:#64748b;font-size:.85rem'>"
            "The plan below is generated from the Avalon Brand System + Own Post References + "
            "Viral Reference Group + Professional Frameworks. "
            "For an editable day-by-day planning board, use the "
            "<strong>📅 Weekly Content Plan</strong> page in the sidebar.</p>",
            unsafe_allow_html=True,
        )
        weekly_plan_file = CONTENT_PLANS / "avalon_weekly_content_plan.md"
        if weekly_plan_file.exists():
            plan_md = weekly_plan_file.read_text(encoding="utf-8")
            # Show overview table first (extract it)
            st.markdown(plan_md)
            st.download_button(
                "📋 Download Weekly Plan",
                data=plan_md,
                file_name="avalon_weekly_content_plan.md",
                mime="text/markdown",
                key="studio_plan_dl",
            )
        else:
            st.info(
                "`content_plans/avalon_weekly_content_plan.md` not found. "
                "The file will be created when you run the full pipeline."
            )
            # Show a sample structure
            st.markdown("""
**Sample weekly structure:**

| Day | Format | Theme | Destination |
|---|---|---|---|
| Monday | Carousel | Brand mythology | Brand |
| Tuesday | Reel | Destination desire | Maldives |
| Wednesday | Photo | Founder moment | Personal |
| Thursday | Carousel | Destination guide | Colombia |
| Friday | Founder Story | Why we travel | Personal |
| Saturday | Carousel | Cultural luxury | Türkiye |
| Sunday | Photo | Soft sales / CTA | Brand |
""")

    # ─── D: OWN POST REFERENCES ───────────────────────────────────────────────
    with tab_d:
        st.markdown("### 📁 Avalon Own Post References")
        st.markdown(
            "<p style='color:#64748b;font-size:.85rem'>"
            "Avalon's own published posts are the <strong>primary visual and copy reference</strong> "
            "for all future content — ranked above influencer references. "
            "Raw images are stored in <code>brand_assets/private/avalon_posts/</code> (gitignored).</p>",
            unsafe_allow_html=True,
        )

        for ref in _STUDIO_OWN_POST_REFS:
            with st.expander(f"📂 {ref['folder']} — {ref['post']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Content type:** {ref['type']}")
                    st.markdown(f"**Mood:** {ref['mood']}")
                    st.markdown(f"**Visual tags:** {ref['visual_tags']}")
                with c2:
                    st.markdown(f"**Reusable pattern:**")
                    st.markdown(f"> {ref['reusable_pattern']}")
                    st.markdown(f"**Best use:** {ref['best_use']}")

        st.markdown("---")
        st.markdown("#### 📋 Pattern Quick Reference")
        pattern_data = [
            {"Pattern": "Navy overlay on authorial photo", "Appears in": "All 3 post sets", "Priority": "Always"},
            {"Pattern": "Montserrat Black + Amore Christmas italic (two-layer)", "Appears in": "All 3 post sets", "Priority": "Always"},
            {"Pattern": "Gold for labels/tags/values only", "Appears in": "All 3 post sets", "Priority": "Always"},
            {"Pattern": "Butterfly isotype whisper (top/bottom right)", "Appears in": "All 3 post sets", "Priority": "Always"},
            {"Pattern": "Full imagotype on end/CTA slide only", "Appears in": "1st Post set", "Priority": "Always"},
            {"Pattern": "◆ WORD · WORD · WORD ◆ footer tag", "Appears in": "Definiton + 1st Post", "Priority": "High"},
            {"Pattern": "Question hook + DESLIZA/SWIPE instruction", "Appears in": "Definiton set", "Priority": "High"},
            {"Pattern": "MEET [NAME] / CO-FOUNDER / circular headshot", "Appears in": "Founders set", "Priority": "High"},
            {"Pattern": "3-beat declaration cover: X. X. X.", "Appears in": "Founders set", "Priority": "High"},
            {"Pattern": "ESCRÍBENOS outlined CTA button", "Appears in": "Definiton set", "Priority": "High"},
            {"Pattern": "Gold headline (rare exception)", "Appears in": "1st Post (slide 7 only)", "Priority": "Rare — impactful"},
            {"Pattern": "Photo collage destination proof", "Appears in": "Founders set", "Priority": "Occasional"},
        ]
        st.dataframe(
            pd.DataFrame(pattern_data),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.markdown("#### 🖼️ Authorial Photo Tags Available")
        photo_tags = [
            {"Tag": "founder_beach_golden_hour", "Destination": "Tropical coast", "Best use": "Founder story, personal content"},
            {"Tag": "founder_diving_gear", "Destination": "Maldives / Ocean", "Best use": "Sofia's story, ocean content, dive travel"},
            {"Tag": "founder_city_monument", "Destination": "Istanbul, Rio, India, Sri Lanka", "Best use": "Cultural content, destination desire"},
            {"Tag": "founder_beach_duo", "Destination": "Tropical beach", "Best use": "Partnership story, two-founders content"},
            {"Tag": "ocean_underwater_coral", "Destination": "Maldives / Ocean", "Best use": "Dive travel, services, ocean pillar"},
            {"Tag": "tropical_boat_beach", "Destination": "Thailand/SE Asia, coastal", "Best use": "Destination desire, world awaits"},
            {"Tag": "maldives_sunset_palms", "Destination": "Maldives", "Best use": "End cards, desire content, luxury"},
            {"Tag": "batu_caves_temple", "Destination": "Malaysia / Sri Lanka", "Best use": "Mission / transformation content"},
            {"Tag": "singapore_night_cityscape", "Destination": "Singapore", "Best use": "Promise / premium content"},
            {"Tag": "christ_redeemer_sky", "Destination": "Brazil", "Best use": "Brand declaration, Latin America pillar"},
        ]
        st.dataframe(
            pd.DataFrame(photo_tags),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "To add new photo tags, update `brand_system/avalon_post_asset_index.md` "
            "and sync new assets to `brand_assets/private/`."
        )


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

    # Public data limitation banner
    st.markdown(
        "<div style='background:#1a1400;border:1.5px solid #78350f;border-radius:10px;"
        "padding:1rem 1.4rem;margin-bottom:1.2rem'>"
        "<p style='color:#fbbf24;font-weight:700;font-size:.95rem;margin:0 0 .5rem 0'>"
        "⚠️ Public Data Limitation — What This Dashboard Can and Cannot See</p>"
        "<p style='color:#fde68a;font-size:.87rem;margin:0 0 .4rem 0'>"
        "This system only collects <strong>publicly visible</strong> Instagram data via Apify. "
        "The following metrics are <strong>never available</strong> from public scraping and "
        "the dashboard will never invent or estimate them:</p>"
        "<ul style='color:#d97706;font-size:.85rem;line-height:1.9;margin:.3rem 0 .5rem 1.2rem;padding:0'>"
        "<li><strong>Saves / Bookmarks</strong> — only visible to the account owner</li>"
        "<li><strong>Shares / Reshares</strong> — only visible to the account owner</li>"
        "<li><strong>Reach</strong> — not publicly exposed by Instagram</li>"
        "<li><strong>Impressions</strong> — not publicly exposed by Instagram</li>"
        "<li><strong>Profile visits from a post</strong> — private analytics only</li>"
        "<li><strong>Follows gained from a post</strong> — private analytics only</li>"
        "</ul>"
        "<p style='color:#fde68a;font-size:.87rem;margin:0'>"
        "Format-adjusted scoring for <strong>Carousels</strong> (save-heavy) and <strong>Reels</strong> "
        "(plays-heavy) uses text-based proxies (caption keywords, caption length) as a stand-in. "
        "To unlock full metric-based scoring, drop an Instagram analytics CSV into "
        "<code>data/analytics/</code>.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

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
elif page == "studio":
    page_content_studio()
elif page == "frameworks":
    page_frameworks()
elif page == "playbook":
    page_playbook()
elif page == "data_quality":
    page_data_quality()
