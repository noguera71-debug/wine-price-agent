"""Entry point: python -m agent.run [--limit N] [--dry]"""
import argparse
import csv
import json
from datetime import date
from pathlib import Path

import yaml

from . import match, report

ROOT = Path(__file__).resolve().parent.parent


def load_watch():
    with open(ROOT / "data/watchlist.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["id"] = match.vivino_id(r["vivino_link"])
    return rows


def label(w):
    return f"{w['winery']} {w['wine']}" + (f" {w['vintage']}" if w["vintage"] else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the first N wines (testing)")
    ap.add_argument("--dry", action="store_true", help="do not write history or reports")
    args = ap.parse_args()

    today = date.today().isoformat()
    watch = load_watch()[: args.limit or None]
    cfg = yaml.safe_load(open(ROOT / "config/shops.yaml", encoding="utf-8"))["shops"]
    shops = {k: v for k, v in cfg.items() if v.get("enabled")}
    over = yaml.safe_load(open(ROOT / "config/overrides.yaml", encoding="utf-8")) or {}
    queries = {w["id"]: (over.get(w["id"], {}).get("query") or match.default_query(w)) for w in watch}

    hist_path = ROOT / "data/prices.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else {}

    from .scrape import scrape
    rows, errors, cards = [], [], {k: 0 for k in shops}
    for wine, shop, items, err in scrape(watch, shops, queries):
        if err:
            errors.append(f"{wine['winery']} {wine['wine']} @ {shop}: {err}")
            continue
        cards[shop] += len(items)
        extra = over.get(wine["id"], {}).get("match")
        for it in items:
            m = match.match_listing(wine, it["name"], extra)
            if m:
                rows.append({"shop": shop, "wine_id": wine["id"], "wine_label": label(wine), "match": m,
                             "listing_name": it["name"], "listing_vintage": match.listing_vintage(it["name"]),
                             "price": it["price"], "in_stock": it["in_stock"], "url": it["url"]})
    for shop, n in cards.items():
        errors.append(f"Info: {shops[shop]['name']} returned {n} product cards across {len(watch)} searches"
                      + (" - ZERO: the shop may be blocking GitHub's servers, or its search page changed" if n == 0 else ""))
    # same product can appear twice on one page; keep one row per url
    rows = list({(r["shop"], r["wine_id"], r["url"]): r for r in rows}.values())

    result = report.classify(rows, history, today)
    text = report.render(today, watch, rows, result, shops, errors)
    if args.dry:
        print(text)
        return
    (ROOT / "reports").mkdir(exist_ok=True)
    report.update_history(history, rows, today)
    hist_path.write_text(json.dumps(history, indent=1, ensure_ascii=False))
    (ROOT / f"reports/{today}.md").write_text(text, encoding="utf-8")
    with open(ROOT / "data/latest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["shop"])
        w.writeheader()
        w.writerows(rows)
    print(text)


if __name__ == "__main__":
    main()
