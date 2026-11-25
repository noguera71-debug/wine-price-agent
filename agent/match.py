"""Match scraped listings to watchlist wines. Pure functions, unit-tested."""
import re
import unicodedata

STOP = {"de", "du", "la", "le", "les", "des", "di", "da", "del", "the", "and", "et", "y", "e", "1er", "cru",
        "wines", "wine", "vino", "vin", "domaine", "domain", "bodegas", "bodega", "champagne", "brut"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def tokens(s: str) -> list[str]:
    return [t for t in norm(s).split() if len(t) >= 3 and t not in STOP and not re.fullmatch(r"(19|20)\d\d", t)]


def vivino_id(link: str) -> str:
    m = re.search(r"/wines/(\d+)", link or "")
    return m.group(1) if m else norm(link)


def listing_vintage(name: str) -> str:
    m = re.search(r"\b((?:19|20)\d\d)\b", name or "")
    return m.group(1) if m else ""


def default_query(wine: dict) -> str:
    words = tokens(wine["winery"])[:2] + tokens(wine["wine"])[:2]
    return " ".join(dict.fromkeys(words))


def match_listing(wine: dict, listing_name: str, extra: list[str] | None = None) -> str | None:
    """Return 'exact', 'other_vintage', 'no_vintage_listed', or None if it is not this wine.

    exact: same vintage (or the watchlist wine has no vintage and the listing has one -> 'any_vintage')
    """
    n = norm(listing_name)
    w_tokens = tokens(wine["winery"])
    c_tokens = tokens(wine["wine"])
    if w_tokens and sum(t in n for t in w_tokens) / len(w_tokens) < 0.5:
        return None
    if c_tokens and sum(t in n for t in c_tokens) / len(c_tokens) < 0.5:
        return None
    if any(norm(x) not in n for x in (extra or [])):
        return None
    want, got = (wine.get("vintage") or "").strip(), listing_vintage(listing_name)
    if not want:
        return "any_vintage"
    if not got:
        return "no_vintage_listed"
    return "exact" if got == want else "other_vintage"
