import feedparser
import datetime
import requests
import os
import html
from urllib.parse import urlparse

# --- RSS FEEDS (add more sources as you discover them) ---
FEEDS = [
    "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
    "https://www.thehindu.com/news/national/kerala/feeder/default.rss",
    "https://english.mathrubhumi.com/news/kerala/rss",
    "https://www.manoramaonline.com/news/kerala/rssfeed.rss",
]

# --- Pest/disease/agriculture keywords ---
PEST_KEYWORDS = [
    # English agri terms
    "crop", "plant", "farmer", "agriculture", "horticulture", "farming",
    "pest", "disease", "wilt", "blast", "fungus", "insect", "infestation",
    "aphid", "bollworm", "armyworm", "mite", "stem borer", "leaf spot", "rot", "blight",

    # Malayalam terms
    "കൃഷി", "വിള", "കർഷകൻ", "കർഷക", "പുഴുപ്പ്", "വാടൽ", "രോഗം",

    # Tamil terms
    "விவசாயி", "பயிர்", "விவசாய", "பூச்சி", "நோய்", "வாடுதல்"
]

# --- Region keywords ---
REGION_KEYWORDS = {
    "kerala": [
        "kerala", "കേരളം",
        "thiruvananthapuram", "trivandrum", "kozhikode", "calicut",
        "alappuzha", "alleppey", "kollam", "kottayam", "ernakulam",
        "palakkad", "thrissur", "malappuram", "kasaragod",
        "wayanad", "idukki"
    ],
    "tamilnadu": [
        "tamil nadu", "tamilnadu", "தமிழ்நாடு",
        "chennai", "madurai", "coimbatore", "tiruchirappalli",
        "tirunelveli", "salem", "vellore", "thanjavur", "thoothukudi"
    ]
}

# normalize string
def norm(s: str):
    if not s:
        return ""
    return html.unescape(s).lower()

def entry_text_fields(entry):
    parts = []
    parts.append(entry.get("title", ""))
    parts.append(entry.get("summary", entry.get("description", "")))
    tags = entry.get("tags", [])
    if tags:
        try:
            for t in tags:
                if isinstance(t, dict):
                    parts.append(t.get("term", ""))
                else:
                    parts.append(str(t))
        except Exception:
            pass
    return norm(" ".join(parts))

def feed_region_from_url(url: str):
    p = urlparse(url)
    u = (p.path + " " + p.netloc).lower()
    if "kerala" in u:
        return "kerala"
    if "tamil" in u or "tamil-nadu" in u or "tamilnadu" in u:
        return "tamilnadu"
    return None

# ✅ NEW helper to filter only agri-related news
def is_relevant_agri_news(txt: str) -> bool:
    return any(k in txt for k in PEST_KEYWORDS)

def fetch_rss_pest_news(region: str = "Kerala", max_items: int = 40):
    region_key = (region or "kerala").strip().lower()
    region_tokens = REGION_KEYWORDS.get(region_key, [region_key, region_key.replace(" ", "")])
    region_tokens = [norm(t) for t in region_tokens]

    reports = []
    seen = set()

    for url in FEEDS:
        try:
            d = feedparser.parse(url)
            for entry in d.entries:
                txt = entry_text_fields(entry)

                # ✅ keep only agri + pest/disease related news
                if not is_relevant_agri_news(txt):
                    continue

                # check region match
                matched_region = False
                if any(tok in txt for tok in region_tokens):
                    matched_region = True
                feed_region = feed_region_from_url(url)
                if feed_region and feed_region == region_key:
                    matched_region = True
                if not matched_region:
                    continue

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                pub = entry.get("published", entry.get("pubDate", "")) or ""
                published = pub

                key = (title, link)
                if key in seen:
                    continue
                seen.add(key)

                reports.append({
                    "title": title,
                    "link": link,
                    "date": published or str(datetime.date.today()),
                    "source": url
                })
        except Exception:
            continue

    # sort by date
    def sort_key(it):
        try:
            return datetime.datetime.fromisoformat(it.get("date","").replace("Z",""))
        except Exception:
            return datetime.datetime.min
    try:
        reports.sort(key=sort_key, reverse=True)
    except Exception:
        pass

    return reports[:max_items]
# --- Additional filters ---
AGRI_POLITICAL_KEYWORDS = [
    "farmer", "farmers", "agrarian", "protest", "strike", "subsidy",
    "loan", "msp", "market", "agriculture", "crop", "yield", "farm"
]

IGNORE_KEYWORDS = [
    "film", "movie", "actor", "actress", "cinema", "cricket", "match",
    "celebrity", "festival", "song", "dance", "music"
]

def is_relevant(txt: str):
    """Keep only agricultural + political farmer news, ignore entertainment."""
    # must have either pest/ disease keyword OR agriculture/political keyword
    if any(k in txt for k in PEST_KEYWORDS) or any(k in txt for k in AGRI_POLITICAL_KEYWORDS):
        # remove entertainment/funny news
        if not any(k in txt for k in IGNORE_KEYWORDS):
            return True
    return False

