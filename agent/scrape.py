"""Playwright scraper. One page per (wine, shop); reads product cards with extract.js."""
import json
import time
from pathlib import Path
from urllib.parse import quote_plus

EXTRACT_JS = (Path(__file__).parent / "extract.js").read_text(encoding="utf-8")


def search_shop(page, shop: dict, query: str, timeout_ms: int = 25000) -> list[dict]:
    url = shop["search"].format(q=quote_plus(query))
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    time.sleep(1.0)
    return page.evaluate(EXTRACT_JS)


def scrape(watch: list[dict], shops: dict, queries: dict, polite_delay: float = 2.0):
    """Yield (wine, shop_key, items, error). Never raises for one bad page."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(locale="en-GB", user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"))
        page = ctx.new_page()
        for wine in watch:
            for key, shop in shops.items():
                try:
                    yield wine, key, search_shop(page, shop, queries[wine["id"]]), None
                except Exception as e:  # noqa: BLE001 - report and continue
                    yield wine, key, [], f"{type(e).__name__}: {str(e)[:160]}"
                time.sleep(polite_delay)
        browser.close()
