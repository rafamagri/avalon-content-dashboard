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
        "#maldives", "#fuvahmulah", "#divingmaldives", "#tigersh ark",
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

        # ── Reference-Based Improvement ────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🔍 Reference-Based Improvement")
        st.markdown(
            "<div class='ac'><p>Suggestions below are rule-based, drawn from the "
            "<b style='color:#00b4d8'>Viral Influencer Trend Reference Group</b> pattern library. "
            "They show which viral patterns match your idea and how to adapt the structure into Avalon's voice — "
            "without copying any creator's exact content.</p></div>",
            unsafe_allow_html=True,
        )

        improvement = generate_improvement(idea, hook, caption, destination, fmt, emotion, cta, tier)
        matched_pats = improvement["matched_patterns"]
        creators     = improvement["relevant_creators"]

        # ── 1. Matched patterns ────────────────────────────────────────────────
        st.markdown("#### 1. Matching Viral Patterns")
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

        # ── 2. Relevant creators ───────────────────────────────────────────────
        if creators:
            st.markdown("#### 2. Most Relevant Reference Creators")
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

        # ── 3. How to adapt for Avalon ─────────────────────────────────────────
        st.markdown("#### 3. How to Adapt for Avalon")
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

        # ── 4. What NOT to copy ────────────────────────────────────────────────
        st.markdown("#### 4. What NOT to Copy")
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

        # ── 5. Improved version ────────────────────────────────────────────────
        st.markdown("#### 5. Improved Version")
        proj_score = improvement["projected_score"]
        proj_color = "#4ade80" if proj_score >= 80 else "#facc15" if proj_score >= 60 else "#fb923c"
        st.markdown(
            f"Projected score with improved hook: "
            f"<b style='color:{proj_color};font-size:1.1rem'>{proj_score}/100</b>",
            unsafe_allow_html=True,
        )

        imp_t1, imp_t2, imp_t3, imp_t4 = st.tabs(["🪝 5 Hooks", "🎬 Reel Structure", "📣 3 CTAs", "#️⃣ Hashtags"])

        with imp_t1:
            for i, h in enumerate(improvement["hooks"], 1):
                tn  = str(h.get("tier_num", 2))
                tc  = f"t{tn}"
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
            st.markdown("**Best-fit Reel structure based on matched patterns:**")
            st.code(improvement["reel_structure"], language=None)

        with imp_t3:
            for c in improvement["ctas"]:
                st.markdown(f"→ {c}")

        with imp_t4:
            hashtag_str = "  ".join(improvement["hashtags"])
            st.text_area("Copy this hashtag set:", value=hashtag_str, height=75, label_visibility="visible")
            st.caption("Edit as needed. 1–3 highly targeted hashtags often outperform generic hashtag spam.")

        # ── 6. Format-Specific Advice ─────────────────────────────────────────
        st.markdown("---")
        fa = improvement.get("format_advice", {})
        fa_fmt = fa.get("format", "")

        if fa_fmt == "Carousel":
            st.markdown("#### 6. Carousel Improvement Ideas")
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
            st.markdown("#### 6. Reel Format Advice")
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
            st.markdown("#### 6. Photo Format Advice")
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

    elif submitted:
        st.warning("Please fill in at least the Content Idea field.")


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
elif page == "playbook":
    page_playbook()
elif page == "data_quality":
    page_data_quality()
