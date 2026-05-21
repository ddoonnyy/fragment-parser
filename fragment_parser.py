import argparse, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://fragment.com"
HERE = Path(__file__).parent

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

SORTS = ["price_asc", "price_desc", "listed", "ending"]
FAREND = datetime.max.replace(tzinfo=timezone.utc)  # bucket for missing end times


def grab(sess, filt, sort):
    r = sess.get(f"{BASE}/?sort={sort}&filter={filt}", timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    out = []
    for tr in soup.select("tr.tm-row-selectable"):
        name  = tr.select_one("td .tm-value")
        price = tr.select_one("td .tm-value.icon-ton")
        link  = tr.select_one("a[href^='/username/']")
        if not (name and price and link):
            continue

        digits = re.sub(r"\D", "", price.get_text(strip=True))
        if not digits:
            continue

        # there are two <time> tags per row; short-text is the compact one
        t = tr.select_one('time[data-relative="short-text"]') or tr.find("time")
        ends = FAREND
        if t and t.has_attr("datetime"):
            try:
                ends = datetime.fromisoformat(t["datetime"])
            except ValueError:
                pass

        out.append({
            "tag":   name.get_text(strip=True),
            "price": int(digits),
            "link":  BASE + link["href"],
            "left":  t.get_text(strip=True) if t else "",
            "ends":  ends,
        })
    return out


def sweep(sess, filt):
    seen, total = {}, 0
    for sort in SORTS:
        rows = grab(sess, filt, sort)
        total += len(rows)
        for r in rows:
            seen.setdefault(r["tag"], r)  # first hit wins
    print(f"  {filt:8} {total} rows / {len(SORTS)} sorts -> {len(seen)} unique")
    return list(seen.values())


def read_keywords():
    p = HERE / "keywords.txt"
    if not p.exists():
        return []
    kw = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            kw.append(line.lower())
    return kw


def hits(tag, keywords):
    h = tag.lstrip("@").lower()
    return [k for k in keywords if k in h]


def sale_line(d):    return f"{d['tag']} - {d['price']} TON - {d['link']}"
def auc_line(d):     return f"{d['tag']} - {d['price']} TON - {d['left'] or '?'} - {d['link']}"


def banner(text, w=40):
    text = f" {text.upper()} "
    pad = max(w - len(text), 4)
    return "=" * (pad // 2) + text + "=" * (pad - pad // 2)


def dump(path, lines):
    body = "\n".join(lines)
    path.write_text(body + ("\n" if body else ""), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="cheap fragment.com listings sweeper")
    ap.add_argument("--cap", type=int, default=15, metavar="TON",
                    help="max price in TON, exclusive (default: 15)")
    args = ap.parse_args()
    cap = args.cap
    if cap <= 0:
        sys.exit("--cap must be positive")

    sess = requests.Session()
    sess.headers["User-Agent"] = UA

    print(f"Sweeping (cap = {cap} TON)...")
    sales    = sweep(sess, "sale")
    auctions = sweep(sess, "auction")
    if not sales and not auctions:
        sys.exit("nothing parsed — fragment markup probably changed")

    # cheapest first for sales, soonest-ending first for auctions
    cheap_sales = sorted([d for d in sales    if d["price"] < cap],
                         key=lambda d: (d["price"], d["tag"].lower()))
    cheap_aucs  = sorted([d for d in auctions if d["price"] < cap],
                         key=lambda d: (d["ends"], d["price"], d["tag"].lower()))

    dump(HERE / "deals.txt",   [sale_line(d) for d in cheap_sales])
    dump(HERE / "auction.txt", [auc_line(d)  for d in cheap_aucs])

    # group cool tags by which keyword they matched. a tag can land in many buckets.
    keywords = read_keywords()
    buckets = defaultdict(lambda: {"sale": [], "auc": []})
    n_sale = n_auc = 0

    for d in cheap_sales:
        ks = hits(d["tag"], keywords)
        if ks:
            n_sale += 1
            for k in ks:
                buckets[k]["sale"].append(d)
    for d in cheap_aucs:
        ks = hits(d["tag"], keywords)
        if ks:
            n_auc += 1
            for k in ks:
                buckets[k]["auc"].append(d)

    cool = []
    for kw in keywords:  # keep user's order from keywords.txt
        b = buckets.get(kw)
        if not b:
            continue
        if cool:
            cool.append("")
        cool.append(banner(f"{kw} ({len(b['sale']) + len(b['auc'])})"))
        if b["sale"]:
            cool.append("-- for sale --")
            cool += [sale_line(d) for d in b["sale"]]
        if b["auc"]:
            if b["sale"]:
                cool.append("")
            cool.append("-- auction --")
            cool += [auc_line(d) for d in b["auc"]]

    dump(HERE / "cooltags.txt", cool)

    print(f"Under {cap} TON: {len(cheap_sales)} for-sale, {len(cheap_aucs)} auction; "
          f"cool: {n_sale} + {n_auc} ({len(keywords)} keywords).")
    print("Wrote deals.txt, auction.txt, cooltags.txt.")


if __name__ == "__main__":
    main()
