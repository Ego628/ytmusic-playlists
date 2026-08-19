"""
Classificador de generos musicais.

Fontes (em ordem de prioridade):
1. Overrides manuais (data/genre_overrides.json) - confianca 1.0
2. Cache SQLite (genre_cache)
3. Last.fm web scraping (artist page -> tags)
4. Heurísticas baseadas em titulo/artista (fallback)

Ignora "efeitos" no titulo: slowed, reverb, looped, extended, best part,
super slowed, sped up, bass boosted, nightcore, etc.
"""
import json
import re
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from . import genre_cache

HERE = Path(__file__).parent
DATA_DIR = HERE.parent.parent / "data"
OVERRIDES_PATH = DATA_DIR / "genre_overrides.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

TITLE_NOISE = [
    r"\bsuper\s+slowed\b", r"\bslowed\b", r"\breverb\b", r"\bloops?\b",
    r"\blooped\b", r"\bbest\s+part\b", r"\bsped\s+up\b", r"\bbass\s+boosted\b",
    r"\bnightcore\b", r"\bextended\b", r"\bultra\s+slowed\b", r"\bremix\b",
    r"\bslowed\s*\+\s*reverb\b", r"\bslowed\s*\+\b", r"\[.*?\]", r"\(.*?slowed.*?\)",
    r"\(.*?looped.*?\)", r"\(.*?reverb.*?\)",
]

TITLE_PATTERN_TO_AXIS = {
    "bass_underground": [
        r"\bhardstyle\b", r"\bphonk\b", r"\bdrift\s*phonk\b", r"\bjumpstyle\b",
        r"\bhorrorcore\b", r"\bwitch\s*house\b", r"\bweirdcore\b", r"\bdreamcore\b",
        r"\btrap\b", r"\bdrill\b", r"\bhyperpop\b", r"\bglitchcore\b",
        r"\bsematary\b", r"\bhussvrx\b", r"\bhaunted\s*mound\b",
        r"\bphonk\s*house\b", r"\bslap\s*house\b", r"\bjersey\s*club\b",
    ],
    "classic_timeless": [
        r"\bjazz\b", r"\bbossa\s*nova\b", r"\bclassical\b", r"\borchestral\b",
        r"\bdream\s*pop\b", r"\bshoegaze\b", r"\bnew\s*wave\b",
        r"\bcalifornia\s*dreamin\b", r"\bmamas\s*[&+]\s*(the\s*)?papas\b",
    ],
    "chicano_soul": [
        r"\bthee\s*sacred\s*souls\b", r"\bthee\s*sinseers\b", r"\bchicano\b",
        r"\blowrider\b",
    ],
}

SLOWED_AS_BASS_KEYWORDS = [
    r"\bslowed\b", r"\bsuper\s*slowed\b", r"\bultra\s*slowed\b",
    r"\bbass\s*boosted\b", r"\bnightcore\b",
]

AXIS_KEYWORDS = {
    "bass_underground": {
        "phonk", "drift phonk", "hardstyle", "jumpstyle", "horrorcore", "witch house",
        "weirdcore", "dreamcore", "trap", "drill", "hyperpop", "glitchcore",
        "dark trap", "cloud rap", "underground rap", "rage", "jersey club",
        "phonk house", "slap house", "brazilian phonk",
    },
    "classic_timeless": {
        "jazz", "big band", "swing", "orchestral", "dream pop", "shoegaze",
        "new wave", "post-punk", "art pop", "experimental", "indie rock",
        "trip hop", "indietronica", "lo-fi indie", "baroque pop",
        "chamber pop", "neo-psychedelia", "psychedelic rock", "singer-songwriter",
        "folk", "classic rock",
    },
    "chicano_soul": {
        "chicano soul", "lowrider", "oldies", "doo-wop", "soul", "r&b",
        "chicano rap", "brown-eyed soul", "quiet storm",
    },
    "electronic_dance": {
        "edm", "house", "techno", "trance", "dubstep", "drum and bass", "dnb",
        "garage", "uk garage", "ambient", "idm",
    },
    "pop_mainstream": {
        "pop", "k-pop", "latin pop", "reggaeton", "dance-pop", "teen pop",
    },
    "hip_hop": {
        "hip hop", "hip-hop", "rap", "trap rap", "west coast", "east coast",
        "gangsta rap", "conscious hip hop",
    },
    "rock_metal": {
        "rock", "metal", "heavy metal", "hard rock", "punk", "grunge",
        "alternative rock", "post-rock", "nu metal", "thrash", "black metal",
        "death metal", "doom metal",
    },
}


def _clean_title(title: str) -> str:
    if not title:
        return ""
    out = title
    for pat in TITLE_NOISE:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip()
    out = out.strip("-–— ")
    return out


def _normalize_text(s: str) -> str:
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _axis_from_title_pattern(title: str, artist: str) -> tuple[str, float] | None:
    blob = _normalize_text(f"{artist} {title}").lower()
    for axis, patterns in TITLE_PATTERN_TO_AXIS.items():
        for pat in patterns:
            if re.search(pat, blob, re.IGNORECASE):
                return (axis, 0.65)
    for pat in SLOWED_AS_BASS_KEYWORDS:
        if re.search(pat, blob, re.IGNORECASE):
            return ("bass_underground", 0.55)
    return None


def _load_overrides() -> dict:
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        return json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _override_key(artist: str, title: str | None) -> str | None:
    overrides = _load_overrides()
    if not overrides:
        return None
    a = _normalize_text((artist or "").strip()).lower()
    t = _normalize_text((title or "").strip()).lower()
    combined = f"{a} - {t}" if t else a
    for key, value in overrides.items():
        kl = _normalize_text(key).lower()
        if kl == a or kl == t or kl == combined:
            return value
    for key, value in overrides.items():
        kl = _normalize_text(key).lower()
        if len(kl) < 3:
            continue
        if kl in a or kl in t or kl in combined:
            return value
    return None


def _scrape_lastfm_artist(artist: str, timeout: float = 10.0) -> dict:
    norm = _normalize_text(artist).strip()
    url = f"https://www.last.fm/music/{requests.utils.quote(norm)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 406:
            time.sleep(3)
            r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code != 200:
            return {"ok": False, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    soup = BeautifulSoup(r.text, "lxml")
    tags = [a.get_text(strip=True).lower() for a in soup.select(".catalogue-tags a[href*='/tag/']")]
    tags = [t for t in tags if t and t != "+ add tag"][:15]
    listeners = 0
    try:
        hdr = soup.select_one(".header-info-description") or soup.select_one("[data-js-listener-badge]")
        if hdr:
            m = re.search(r"([\d,]+)\s*listener", hdr.get_text())
            if m:
                listeners = int(m.group(1).replace(",", ""))
    except Exception:
        pass
    return {"ok": True, "tags": tags, "listeners": listeners, "url": url}


def _axis_from_tags(tags: list[str]) -> tuple[str, float]:
    if not tags:
        return ("uncategorized", 0.0)
    scores = {axis: 0 for axis in AXIS_KEYWORDS}
    for t in tags:
        tl = t.lower()
        for axis, kws in AXIS_KEYWORDS.items():
            for kw in kws:
                if kw in tl or tl in kw:
                    scores[axis] += 1
    best_axis = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    if scores[best_axis] == 0:
        return ("uncategorized", 0.0)
    return (best_axis, scores[best_axis] / total)


def classify_track(artist: str, title: str, *, use_cache: bool = True) -> dict:
    override = _override_key(artist, title)
    if override:
        return {
            "artist": artist,
            "title": title,
            "clean_title": _clean_title(title),
            "axis": override,
            "genres": [override],
            "tags": [],
            "confidence": 1.0,
            "source": "override",
            "listeners": 0,
        }

    if use_cache:
        cached = genre_cache.get(artist, title) or genre_cache.get(artist)
        if cached:
            return {
                "artist": artist,
                "title": title,
                "clean_title": _clean_title(title),
                "axis": (json.loads(cached["genres"]) or ["uncategorized"])[0],
                "genres": json.loads(cached["genres"]),
                "tags": json.loads(cached["tags"]),
                "confidence": cached["confidence"],
                "source": f"cache:{cached['source']}",
                "listeners": cached["listeners"],
            }

    result = _scrape_lastfm_artist(artist)
    if not result.get("ok"):
        heuristic = _axis_from_title_pattern(title, artist)
        if heuristic:
            axis, conf = heuristic
            genre_cache.put(
                artist, title,
                genres=[axis],
                tags=[],
                confidence=conf,
                source="title_pattern",
                listeners=0,
            )
            return {
                "artist": artist,
                "title": title,
                "clean_title": _clean_title(title),
                "axis": axis,
                "genres": [axis],
                "tags": [],
                "confidence": conf,
                "source": "title_pattern",
                "listeners": 0,
            }
        return {
            "artist": artist,
            "title": title,
            "clean_title": _clean_title(title),
            "axis": "uncategorized",
            "genres": [],
            "tags": [],
            "confidence": 0.0,
            "source": f"lastfm_error:{result.get('status', result.get('error','?'))}",
            "listeners": 0,
        }

    axis, conf = _axis_from_tags(result["tags"])
    if axis == "uncategorized":
        heuristic = _axis_from_title_pattern(title, artist)
        if heuristic:
            axis, conf = heuristic
    genres = result["tags"][:5]
    genre_cache.put(
        artist, title,
        genres=genres if axis != "uncategorized" else [axis],
        tags=result["tags"],
        confidence=conf,
        source="lastfm" if axis != "uncategorized" else "title_pattern_fallback",
        listeners=result.get("listeners", 0),
    )
    return {
        "artist": artist,
        "title": title,
        "clean_title": _clean_title(title),
        "axis": axis,
        "genres": genres if axis != "uncategorized" else [axis],
        "tags": result["tags"],
        "confidence": conf,
        "source": "lastfm" if axis != "uncategorized" else "title_pattern_fallback",
        "listeners": result.get("listeners", 0),
        "lastfm_url": result.get("url"),
    }
