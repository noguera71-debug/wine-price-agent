# Wine price agent

Weekly scan of EU wine shops for the wines on 'data/watchlist.csv' (Ramon's personal Vivino rating above 4.0,
scanned since 2021-11-25, plus hand-picked producers). Every Monday a GitHub Action opens each shop's search page in a
headless browser, reads the product cards, keeps a price history and writes 'reports/YYYY-MM-DD.md'.

## What it does and does not do
- Reads price and stock from **live shop pages**, never from search-engine snippets (those were stale in the first manual pass).
- Matches by winery + wine name + vintage. Other vintages of the same wine go in their own section. Cuvée mix-ups are
  blocked with the 'match' words in 'config/overrides.yaml'.
- Flags an offer when a listing is 10% or more below the median of the listings found that day (needs 2+ shops) or
  10% or more below its own earlier low. Lists wines that are newly in stock.
- **Shipping is not added to prices.** No address is ever entered. Each shop's published shipping note is printed at
  the bottom of the report.
- Wines not found in stock are listed, not hidden.

## Shops
See 'config/shops.yaml'. Only shops with 'enabled: true' are scanned. A shop is enabled only after its search URL has
been checked in a real browser and the extractor returned the right cards. Currently only Vins et Millésimes is verified.
To add a shop: open its search page, copy the URL with '{q}' where the query goes, run
'python -m agent.run --limit 3 --dry' locally (needs 'pip install -r requirements.txt' and
'python -m playwright install chromium'), and check the output against the page.

## Run it
- Manually: GitHub > Actions > "Weekly wine price scan" > Run workflow ('limit' = 3 for a quick test).
- Locally: 'python -m agent.run --limit 3 --dry'.
- Tests: 'python -m pytest -q'.

## Known risks
- Some shops block data-centre traffic (GitHub runners). If a shop returns nothing, the report lists it under "Run problems".
- The generic extractor ('agent/extract.js') finds product cards by looking for links next to prices. It matched the live
  page exactly on Vins et Millésimes; other shops must be checked one by one.
- If the watchlist changes, replace 'data/watchlist.csv' (same columns) and commit.
