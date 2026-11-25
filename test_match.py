from agent import match

W = {"winery": "Albert Grivault", "wine": "Clos du Murger Meursault", "vintage": "2014"}


def test_exact_vintage():
    assert match.match_listing(W, "ALBERT GRIVAULT MEURSAULT CLOS DU MURGER 2014") == "exact"


def test_other_vintage_is_separate():
    assert match.match_listing(W, "Albert Grivault Meursault Clos du Murger 2021") == "other_vintage"


def test_other_cuvee_same_winery_rejected():
    assert match.match_listing(W, "ALBERT GRIVAULT POMMARD 1ER CRU CLOS BLANC 2022 ROUGE") is None


def test_extra_words_block_cuvee_mixups():
    w = {"winery": "Chevreux-Bournazel La Parcelle", "wine": "Champagne", "vintage": "2020"}
    assert match.match_listing(w, "Chevreux-Bournazel La Capella 2020", ["parcelle"]) is None
    assert match.match_listing(w, "Chevreux-Bournazel La Parcelle 2020", ["parcelle"]) == "exact"


def test_no_vintage_on_watchlist_wine():
    w = {"winery": "Aci Urbajs", "wine": "Organic Anarchy", "vintage": ""}
    assert match.match_listing(w, "Aci Urbajs Organic Anarchy 2025") == "any_vintage"


def test_vivino_id_and_query():
    assert match.vivino_id("https://www.vivino.com/wines/156748447") == "156748447"
    assert match.default_query({"winery": "Oxer Wines", "wine": "Suzzane Rioja"}) == "oxer suzzane rioja"
