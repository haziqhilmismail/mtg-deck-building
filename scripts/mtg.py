"""Usage (run where ck.json lives):
  mtg.py price  <deckfile>         CK cheapest in-stock legal printing per card + total
  mtg.py text   <deckfile>         Scryfall oracle text, MV, Commander legality, game-changer flag
  mtg.py search '<query>' [limit] [deckfile]  Scryfall search (EDHREC order) with CK prices; with a deckfile, marks each hit have/MISSING
  mtg.py check  <deckfile> '<Commander Name>'   100 cards, singleton, legality, colour identity
  mtg.py edhrec '<Commander Name>' [deckfile]   EDHREC's cards for that commander by synergy, with CK prices; marks cards MISSING from the deck
                                                 partners: 'Tymna the Weaver + Thrasios, Triton Hero'
ck.json: curl -sSL -A "Mozilla/5.0" -o ck.json https://api.cardkingdom.com/api/v2/pricelist
"""
import json, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from collections import Counter
from typing import NamedTuple, Optional

BAD = ("World Championship", "Collectors", "30th Anniversary Edition", "Art Series", "Oversize", "Token", "Memorabilia")
OWNED_BASICS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
HEADERS = {"User-Agent": "deckcheck/1.0", "Accept": "application/json", "Content-Type": "application/json"}

def parse(path):
    return [(int(m.group(1)), m.group(2)) for l in open(path) if (m := re.match(r"\s*(\d+)x?\s+(.+?)\s*$", l))]

_ck = None
def ck():
    global _ck
    if _ck is None:
        _ck = {}
        for x in json.load(open("ck.json"))["data"]:
            if not any(b in x["edition"] for b in BAD):
                _ck.setdefault(x["name"].lower(), []).append(x)
    return _ck

class Price(NamedTuple):
    price: float
    edition: str
    in_stock: bool

def front(name): return name.split(" // ")[0].lower()

def owned(path): return {front(n) for _, n in parse(path)}

def mark(name, have, sep=""): return "" if have is None else ("have    " if front(name) in have else "MISSING ") + sep

def slug(name):
    ascii_name = unicodedata.normalize("NFKD", name.split(" // ")[0]).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 -]", "", ascii_name).strip().replace(" ", "-")

def price(name) -> Optional["Price"]:
    """CK lists double-faced cards by front face."""
    rows = ck().get(name.lower()) or ck().get(name.split(" // ")[0].lower()) or []
    if not rows: return None
    stock = [r for r in rows if r["qty_retail"] > 0]
    r = min(stock or rows, key=lambda r: float(r["price_retail"]))
    return Price(float(r["price_retail"]), r["edition"] + (" foil" if r["is_foil"] == "true" else ""), bool(stock))

def get(url, body=None):
    time.sleep(0.5)  # Scryfall rate limit
    try: return json.load(urllib.request.urlopen(urllib.request.Request(url, body, HEADERS)))
    except urllib.error.HTTPError as e: sys.exit(f"HTTP {e.code} (404 on search means no results): {url}")

def scry(names):
    cards = []
    for i in range(0, len(names), 75):
        d = get("https://api.scryfall.com/cards/collection",
                json.dumps({"identifiers": [{"name": n.split(" // ")[0]} for n in names[i:i+75]]}).encode())
        cards += d["data"]
        for nf in d.get("not_found", []): print("NOT FOUND", nf)
    return cards

def text(c):
    return " // ".join(f"{f.get('mana_cost','')} {f.get('type_line','')}: {f.get('oracle_text','')}"
                       for f in c.get("card_faces") or [c]).replace("\n", " | ")

def line(c):
    return f"{c['name']} | MV{int(c['cmc'])} | id:{''.join(c['color_identity']) or 'C'} | cmdr:{c['legalities']['commander']} | GC:{c.get('game_changer')} | {text(c)}"

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "price":
        tot = n = 0
        for q, name in parse(arg):
            n += q
            if name in OWNED_BASICS: continue
            p = price(name)
            if not p: print(f"  ??.??  {name}  (NOT ON CK)"); continue
            tot += q * p.price
            print(f"{p.price:7.2f}  {name}  [{p.edition}]{'' if p.in_stock else '  OUT OF STOCK'}")
        print(f"TOTAL {tot:.2f}  cards {n}")
    elif cmd == "text":
        for c in scry([n for _, n in parse(arg)]): print(line(c) + "\n")
    elif cmd == "check":
        deck = parse(arg); cards = {c["name"]: c for c in scry([n for _, n in deck])}
        cmdr = next((c for n, c in cards.items() if front(n) == front(sys.argv[3])), None)
        if not cmdr: sys.exit(f"commander '{sys.argv[3]}' is not in {arg}")
        copies = Counter()
        for q, name in deck: copies[front(name)] += q
        allowed, bad = set(cmdr["color_identity"]), []
        total = sum(q for q, _ in deck)
        if total != 100: bad.append(f"{total} cards, need 100")
        for q, name in deck:
            c = next((c for n, c in cards.items() if front(n) == front(name)), None)
            if not c: bad.append(f"{name}: not found"); continue
            off = set(c["color_identity"]) - allowed  # hybrid and rules-text mana symbols count
            if off: bad.append(f"{name}: colour identity {''.join(c['color_identity'])} is outside {''.join(sorted(allowed)) or 'C'}")
            if c["legalities"]["commander"] != "legal": bad.append(f"{name}: {c['legalities']['commander']} in Commander")
            n = copies.pop(front(name), 1)  # pop so a card listed on two lines is reported once
            if n > 1 and "Basic" not in c["type_line"] and not re.search(r"A deck can have (any number|up to)", c.get("oracle_text", "")):
                bad.append(f"{name}: {n} copies")
        print("\n".join(bad) if bad else f"OK: 100 cards, all legal, all inside {''.join(sorted(allowed)) or 'C'}")
        sys.exit(1 if bad else 0)
    elif cmd == "search":
        limit, n = int(sys.argv[3]) if len(sys.argv) > 3 else 60, 0
        have = owned(sys.argv[4]) if len(sys.argv) > 4 else None
        url = "https://api.scryfall.com/cards/search?" + urllib.parse.urlencode({"q": arg, "order": "edhrec"})
        while url and n < limit:
            d = get(url)
            for c in d["data"][:limit - n]:
                n += 1; p = price(c["name"])
                print(f"{mark(c['name'], have, '| ')}${p.price if p else '?'} | {line(c)[:380]}")
            url = d.get("next_page")
    elif cmd == "edhrec":
        have = owned(sys.argv[3]) if len(sys.argv) > 3 else None
        page = "-".join(slug(n) for n in arg.split(" + "))
        cards = {}
        d = get(f"https://json.edhrec.com/pages/commanders/{page}.json")
        if "redirect" in d: d = get(f"https://json.edhrec.com/pages{d['redirect']}.json")  # partner pairs have one canonical order
        for cl in d["container"]["json_dict"]["cardlists"]:
            for cv in cl["cardviews"]: cards.setdefault(cv["name"], cv)
        for name, cv in sorted(cards.items(), key=lambda kv: -kv[1].get("synergy", 0)):
            if name in OWNED_BASICS: continue
            p = price(name)
            print(f"{mark(name, have)}syn {cv.get('synergy', 0):+.2f}  in {100 * cv['num_decks'] // max(cv['potential_decks'], 1):3d}%  ${p.price if p else '?'}  {name}")
    else: sys.exit(__doc__)
