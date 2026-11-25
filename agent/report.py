"""History update, offer detection, and the weekly Markdown report. Pure functions, unit-tested."""
from statistics import median

OFFER_PCT = 0.10


def update_history(history: dict, rows: list[dict], today: str) -> dict:
    """history[key] = [{date, price, in_stock}], key = shop|wine_id|url. One entry per key per day."""
    for r in rows:
        key = f"{r['shop']}|{r['wine_id']}|{r['url']}"
        h = history.setdefault(key, [])
        h[:] = [e for e in h if e["date"] != today]
        h.append({"date": today, "price": r["price"], "in_stock": r["in_stock"]})
    return history


def prior_low(history: dict, row: dict, today: str):
    key = f"{row['shop']}|{row['wine_id']}|{row['url']}"
    p = [e["price"] for e in history.get(key, []) if e["date"] != today and e["in_stock"]]
    return min(p) if p else None


def was_in_stock_before(history: dict, row: dict, today: str) -> bool:
    key = f"{row['shop']}|{row['wine_id']}|{row['url']}"
    return any(e["in_stock"] for e in history.get(key, []) if e["date"] != today)


def classify(rows: list[dict], history: dict, today: str) -> dict:
    """Split today's in-stock listings into offers / newly available / the rest."""
    live = [r for r in rows if r["in_stock"] and r["match"] in ("exact", "any_vintage", "no_vintage_listed")]
    by_wine: dict[str, list[dict]] = {}
    for r in live:
        by_wine.setdefault(r["wine_id"], []).append(r)
    offers, new = [], []
    for wid, rs in by_wine.items():
        shops_priced = {r["shop"] for r in rs}
        for r in rs:
            reasons = []
            others = [x["price"] for x in rs if x["shop"] != r["shop"]]
            if len(shops_priced) >= 2 and others:
                m = median([x["price"] for x in rs])
                if r["price"] <= m * (1 - OFFER_PCT):
                    reasons.append(f"{round((1 - r['price'] / m) * 100)}% below the median of {len(rs)} listings ({m:.2f} EUR)")
            low = prior_low(history, r, today)
            if low is not None and r["price"] <= low * (1 - OFFER_PCT):
                reasons.append(f"{round((1 - r['price'] / low) * 100)}% below its own earlier low ({low:.2f} EUR)")
            if reasons:
                offers.append({**r, "reasons": reasons})
            elif not was_in_stock_before(history, r, today) and history:
                new.append(r)
    return {"offers": offers, "new": new}


def render(today: str, watch: list[dict], rows: list[dict], result: dict, shops: dict, errors: list[str]) -> str:
    L = [f"# Wine price report, {today}", ""]
    L.append(f"{len(watch)} wines checked in {len(shops)} shop(s): " + ", ".join(s['name'] for s in shops.values()) + ".")
    L += ["Prices are per bottle as shown on the shop page, VAT included, shipping NOT included "
          "(no address is ever entered). Only listings found on live pages today are shown.", ""]
    L.append("## Offers (10% or more below the median or the listing's own earlier low)")
    if result["offers"]:
        L += ["| Wine | Vintage in shop | Shop | Price | Why | Link |", "|---|---|---|---|---|---|"]
        for o in result["offers"]:
            L.append(f"| {o['wine_label']} | {o['listing_vintage'] or '-'} | {shops[o['shop']]['name']} | {o['price']:.2f} EUR | "
                     f"{'; '.join(o['reasons'])} | [page]({o['url']}) |")
    else:
        L.append("None this week. (Offers need at least two shops listing the wine, or a price history.)")
    L += ["", "## Newly in stock since the last run"]
    if result["new"]:
        for r in result["new"]:
            L.append(f"- {r['wine_label']} ({r['listing_vintage'] or 'no vintage'}), {shops[r['shop']]['name']}, {r['price']:.2f} EUR: [page]({r['url']})")
    else:
        L.append("Nothing new.")
    L += ["", "## All matching listings in stock"]
    live = sorted((r for r in rows if r["in_stock"] and r["match"] in ("exact", "any_vintage", "no_vintage_listed")),
                  key=lambda r: (r["wine_label"], r["price"]))
    if live:
        L += ["| Wine | Vintage in shop | Shop | Price | Link |", "|---|---|---|---|---|"]
        for r in live:
            L.append(f"| {r['wine_label']} | {r['listing_vintage'] or '-'} | {shops[r['shop']]['name']} | {r['price']:.2f} EUR | [page]({r['url']}) |")
    else:
        L.append("None.")
    L += ["", "## Other vintages of watchlist wines (not the vintage you rated)"]
    other = sorted((r for r in rows if r["in_stock"] and r["match"] == "other_vintage"), key=lambda r: (r["wine_label"], r["price"]))
    if other:
        for r in other:
            L.append(f"- {r['wine_label']}: {r['listing_vintage']} at {shops[r['shop']]['name']}, {r['price']:.2f} EUR: [page]({r['url']})")
    else:
        L.append("None.")
    found = {r["wine_id"] for r in rows if r["in_stock"]}
    missing = [w for w in watch if w["id"] not in found]
    L += ["", f"## Not found in stock anywhere ({len(missing)} of {len(watch)})"]
    L.append(", ".join(f"{w['winery']} {w['wine']} {w['vintage']}".strip() for w in missing) or "None.")
    L += ["", "## Run problems"]
    L += [f"- {e}" for e in errors[:30]] or ["None."]
    L += ["", "## Shipping published by each shop"]
    L += [f"- {s['name']}: {s['shipping']}" for s in shops.values()]
    return "\n".join(L) + "\n"
