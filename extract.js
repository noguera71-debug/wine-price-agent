// Generic product-card extractor, run inside the page. No shop-specific selectors:
// for every link, climb to the largest ancestor that still holds only 1-3 prices (one product card).
(() => {
  const EX_VAT = /ex-?\s?vat|excl|\bHT\b|sin iva|netto|ex tax/i;
  const OUT = /out of stock|sold out|agotado|sin stock|nicht verf|nicht lieferbar|not available|épuisé|indisponible|esaurito|non disponibile|ausverkauft/i;
  const PRICE = /(?:€\s?(\d{1,3}(?:[.,\s]\d{3})*[.,]\d{2})|(\d{1,3}(?:[.,\s]\d{3})*[.,]\d{2})\s?€)/g;
  const num = s => { s = s.replace(/\s/g, ''); const c = s.lastIndexOf(','), d = s.lastIndexOf('.');
    const dec = Math.max(c, d); return parseFloat(s.slice(0, dec).replace(/[.,]/g, '') + '.' + s.slice(dec + 1)); };
  const prices = t => { const out = []; let m; PRICE.lastIndex = 0;
    while ((m = PRICE.exec(t))) { const ctx = t.slice(m.index + m[0].length, m.index + m[0].length + 16);
      if (!EX_VAT.test(ctx)) out.push(num(m[1] || m[2])); } return out; };
  const seen = new Set(), items = [];
  for (const a of document.querySelectorAll('a[href]')) {
    if (!/^https?:/.test(a.href) || a.href.includes('#') && a.href.split('#')[0] === location.href.split('#')[0]) continue;
    let el = a, best = null;
    for (let i = 0; i < 8 && el && el !== document.body; i++, el = el.parentElement) {
      const t = el.innerText || ''; if (t.length > 700) break;
      const p = prices(t); if (p.length >= 1 && p.length <= 3) best = el; else if (p.length > 3) break;
    }
    if (!best || seen.has(best)) continue; seen.add(best);
    const text = best.innerText.replace(/\s+/g, ' ').trim();
    const h = best.querySelector('h1,h2,h3,h4,[class*=title i],[class*=name i]');
    const name = ((h && h.innerText) || a.getAttribute('title') || a.innerText || '').replace(/\s+/g, ' ').trim();
    const all = prices(text).filter(x => x > 0); if (!all.length || !name) continue;
    items.push({ url: a.href, name, price: all[0], all_prices: all, in_stock: !OUT.test(text), text: text.slice(0, 300) });
  }
  return items.slice(0, 40);
})()
