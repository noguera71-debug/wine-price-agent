from agent import report


def row(shop, price, url="u", stock=True, match="exact", wid="1"):
    return {"shop": shop, "wine_id": wid, "wine_label": "W", "match": match, "price": price, "in_stock": stock,
            "url": url + shop, "listing_vintage": "2020", "listing_name": "n"}


def test_median_offer_needs_ten_percent_and_two_shops():
    rows = [row("a", 100), row("b", 120), row("c", 130)]
    res = report.classify(rows, {}, "2026-12-01")
    assert [o["shop"] for o in res["offers"]] == ["a"]  # median 120 -> 100 is 17% below
    one = report.classify([row("a", 50)], {}, "2026-12-01")
    assert one["offers"] == []  # single listing, no history: nothing to compare with


def test_own_history_low():
    hist = {"a|1|ua": [{"date": "2026-11-24", "price": 100, "in_stock": True}]}
    res = report.classify([row("a", 85, url="u")], hist, "2026-12-01")
    assert len(res["offers"]) == 1 and "earlier low" in res["offers"][0]["reasons"][0]


def test_out_of_stock_and_other_vintage_never_offers():
    rows = [row("a", 10, stock=False), row("b", 10, match="other_vintage"), row("c", 100)]
    assert report.classify(rows, {}, "d")["offers"] == []


def test_newly_in_stock_only_after_first_run():
    assert report.classify([row("a", 100)], {}, "d")["new"] == []
    hist = {"x|9|u": [{"date": "2026-11-24", "price": 5, "in_stock": True}]}
    assert len(report.classify([row("a", 100)], hist, "d")["new"]) == 1


def test_history_one_entry_per_day():
    h = report.update_history({}, [row("a", 100)], "2026-12-01")
    h = report.update_history(h, [row("a", 90)], "2026-12-01")
    assert len(h["a|1|ua"]) == 1 and h["a|1|ua"][0]["price"] == 90


def test_render_smoke():
    shops = {"a": {"name": "A", "shipping": "s"}}
    rows = [row("a", 99.5)]
    res = report.classify(rows, {}, "2026-12-01")
    txt = report.render("2026-12-01", [{"id": "1", "winery": "x", "wine": "y", "vintage": ""}], rows, res, shops, [])
    assert "Wine price report" in txt and "99.50 EUR" in txt
