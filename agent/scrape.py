"""Playwright scraper. One page per (wine, shop); reads product cards with extract.js.

A shop that shows a bot-verification page is reported as BLOCKED and left alone (after 3 blocked
searches in a row we stop asking that shop). We never try to get around such a page.
A search that simply finds nothing is a normal, empty result.
"""
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

EXTRACT_JS = (Path(__file__).parent / "extract.js").read_text(encoding="utf-8")
BLOCK_RE = re.compile(
    r"just a moment|attention required|access denied|security verification|verify you are human|captcha"
    r"|pardon our interruption|request blocked|are you a human|checking your browser|temporarily blocked"
    r"|robot challenge", re.I)
MAX_BLOCKS = 3


class Blocked(RuntimeError):
    pass


def search_shop(page, shop: dict, query: str, timeout_ms: int = 25000) -> list[dict]:
    url = shop["search"].format(q=quote_plus(query))
    resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    time.sleep(1.0)
    status = resp.status if resp else 0
    title = page.title()
    body = page.inner_text("body")[:300].replace("\n", " ")
    if status in (403, 429) or BLOCK_RE.search(title + " " + body):
        raise Blocked(f"BLOCKED (HTTP {status}, title={title!r})")
    items = page.evaluate(EXTRACT_JS)
    if not items and status >= 400:
        raise RuntimeError(f"HTTP {status}: search address not found (title={title!r})")
    return items


def scrape(watch: list[dict], shops: dict, queries: dict, polite_delay: float = 2.0):
    """Yield (wine, shop_key, items, error). Never raises for one bad page."""
    from playwright.sync_api import sync_playwright
    blocks = {k: 0 for k in shops}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(locale="en-GB", user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"))
        page = ctx.new_page()
        for wine in watch:
            for key, shop in shops.items():
                if blocks[key] >= MAX_BLOCKS:
                    yield wine, key, [], "BLOCKED (skipped: shop already refused 3 searches)"
                    continue
                try:
                    yield wine, key, search_shop(page, shop, queries[wine["id"]]), None
                    blocks[key] = 0
                except Blocked as e:
                    blocks[key] += 1
                    yield wine, key, [], str(e)
                except Exception as e:  # noqa: BLE001 - report and continue
                    yield wine, key, [], f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
                time.sleep(polite_delay)
        browser.close()
