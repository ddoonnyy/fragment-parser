# FragmentParser

A small command-line tool that scrapes [fragment.com](https://fragment.com)
Telegram-username listings, picks out the cheap ones, and writes them to plain
text files. It covers both **"for sale"** lots and **auction** lots, and can
flag any tag whose handle contains keywords you care about.

---

## What it does

For each run it produces three files in the project folder:

| File           | Contents                                                | Sort order                                  |
| -------------- | ------------------------------------------------------- | ------------------------------------------- |
| `deals.txt`    | "For sale" listings under the price cap                 | Cheapest first                              |
| `auction.txt`  | Auction listings under the price cap                    | Ending soonest first, then cheapest         |
| `cooltags.txt` | Subset of the above whose handle matches `keywords.txt` | Grouped by keyword, each in its native sort |

**Line formats**

```
deals.txt        @tag - 5 TON - https://fragment.com/username/tag
auction.txt      @tag - 5 TON - 2 days 16 hours - https://fragment.com/username/tag
```

---

## Requirements

- Python 3.9 or newer
- Internet access to fragment.com
- Dependencies: `requests`, `beautifulsoup4` (installed via `requirements.txt`)

---

## Installation

```bash
git clone https://github.com/ddoonnyy/fragment-parser.git
cd fragment-parser
pip install -r requirements.txt
```

On Windows you can skip the `pip install` step — `run.bat` installs the
dependencies the first time it runs.

---

## Usage

### Run from a terminal

```bash
python fragment_parser.py
```

With a custom price cap (in TON):

```bash
python fragment_parser.py --cap 8
```

See all options:

```bash
python fragment_parser.py --help
```

Each run overwrites `deals.txt`, `auction.txt`, and `cooltags.txt`.

### Windows

Run **`run.bat`**.

You can also pass arguments through it:

```bat
run.bat --cap 8
```

### Sample output

```
Sweeping (cap = 15 TON)...
  sale     2000 rows / 4 sorts -> 1987 unique
  auction  1951 rows / 4 sorts -> 1730 unique
Under 15 TON: 1211 for-sale, 956 auction; cool: 180 + 186 (134 keywords).
Wrote deals.txt, auction.txt, cooltags.txt.
```

---

## Configuration

### Price cap

Pass `--cap N` on the command line, or change `default=15` in the
`argparse` block at the top of `main()` in `fragment_parser.py` to set a new
permanent default.

### Keywords (`keywords.txt`)

One substring per line. Lines starting with `#` are comments. Matching is
**case-insensitive** and **substring-based** — `vip` matches anywhere inside a
handle, so `@vipbot`, `@thevip`, and `@vipstar` all qualify.

Sample:

```text
# cool words
vip
king
ninja

# numbers
666
777
1337

# slang
crypto
nft
ai
```

In `cooltags.txt` each section is labeled with the matched keyword:

```
=============== VIP (6) ================
-- for sale --
@vipbot - 5 TON - https://fragment.com/username/vipbot
@vipclub - 7 TON - https://fragment.com/username/vipclub
-- auction --
@vipworld - 9 TON - 1 day 4 hours - https://fragment.com/username/vipworld
```

If a tag matches multiple keywords, it appears in every matching section.

### Other tunables

In `fragment_parser.py`:

- `SORTS` — which Fragment sort orders to hit. Removing any will reduce
  coverage but speed up runs. Defaults to all four:
  `price_asc, price_desc, listed, ending`.
- `UA` — User-Agent string sent on every request.

---

## How it works

Fragment serves at most **~500 listings per query**, regardless of how you
paginate. There is no public API and the unauthenticated `/api?hash=…`
endpoint hard-caps empty-query browsing at the same 500 rows.

To get more than 500, the parser hits four different sort orders for each
filter (`price_asc`, `price_desc`, `listed`, `ending`), deduplicates by
handle, and merges. In practice this lifts coverage to **~1800–2000 unique
listings per filter** instead of 500.
```

---
## License

MIT — do whatever you want, no warranty.
