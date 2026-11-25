"""Honest goldfish dealer. The library order lives in gf.json and is never printed;
only cards that are drawn or legitimately looked at are shown.
  goldfish.py split <tagged deckfile>               99 cards tagged `1 Card Name # role` -> third-A/B/C.txt, flags uneven roles
  goldfish.py new <deckfile> '<Commander>' [seed]   shuffle, draw 7 (seed is random unless given; '' if the file has no commander)
  goldfish.py mull                                  reshuffle, draw 7 (London: then `put bottom` N cards)
  goldfish.py draw [n]                              draw n (default 1)
  goldfish.py peek <n>                              look at top n (scry, surveil, Ponder, Brainstorm planning)
  goldfish.py put top|bottom '<Card>'               hand/looked-at card back onto the library
  goldfish.py take '<Card>'                         remove from library to hand (tutor), no shuffle; from top n after peek
  goldfish.py bury <n>                              move the top n to the bottom (scry/surveil-style bottoming after `peek`)
  goldfish.py shuffle                               shuffle the library
  goldfish.py mill <n>                              top n to graveyard (printed)
  goldfish.py status                                library size and draw count only
  goldfish.py react counter|removal [key] [storm] [ward=N]   roll whether an opponent answers this spell/permanent
  goldfish.py odds [name=value ...]                 show or change this game's odds (counter removal key storm ward answers)
"""
import json, random, re, sys
F = "gf.json"
# Opponent interaction for `react`. counter/removal are the static chance per spell/permanent; key is added for an
# engine or win piece, storm is added when you are going off; ward is the multiplier per {2} of ward (removal only).
# ponytail: one shared pool of `answers` for the whole table and no board wipes; split per opponent if that matters.
ODDS = {"counter": 0.05, "removal": 0.08, "key": 0.10, "storm": 0.15, "ward": 0.5, "answers": 6}
def load(): return json.load(open(F))
def save(s): json.dump(s, open(F, "w"))
def find(lib, name):
    i = next((i for i, c in enumerate(lib) if c.lower() == name.lower() or c.split(" // ")[0].lower() == name.lower()), None)
    if i is None: sys.exit(f"'{name}' is not in the library")
    return i
cmd, a = sys.argv[1], sys.argv[2:]
if cmd == "split":
    roles = {}
    for l in open(a[0]):
        if m := re.match(r"\s*(\d+)\s+(.+?)\s*#\s*(\S+)\s*$", l):
            roles.setdefault(m.group(3), []).extend([m.group(2)] * int(m.group(1)))
        elif l.strip(): sys.exit(f"untagged line: {l.strip()}")
    thirds, i = [[], [], []], 0
    print(f"{'role':12} total  A  B  C")
    for role, cards in roles.items():  # round-robin, rotation carries across roles so thirds stay equal
        got = [0, 0, 0]
        for c in cards: thirds[i % 3].append(c); got[i % 3] += 1; i += 1
        flag = "  <- ONE-OFFS, cut or commit to 3" if len(cards) < 3 else "  <- UNEVEN" if len(cards) % 3 else ""
        print(f"{role:12} {len(cards):5} {got[0]:2} {got[1]:2} {got[2]:2}{flag}")
    for t, name in zip(thirds, "ABC"):
        open(f"third-{name}.txt", "w").write("".join(f"1 {c}\n" for c in t))
    print("sizes", [len(t) for t in thirds], "-> third-A.txt third-B.txt third-C.txt")
elif cmd == "new":
    seed = a[2] if len(a) > 2 else str(random.SystemRandom().randrange(10**9))
    lib = [n for l in open(a[0]) if (m := re.match(r"\s*(\d+)\s+(.+?)\s*$", l)) for n in [m.group(2)] * int(m.group(1))]
    if len(a) > 1 and a[1]: lib.pop(find(lib, a[1]))  # commander starts in the command zone
    random.Random(seed).shuffle(lib)
    s = {"seed": seed, "lib": lib, "drawn": 7, "mulls": 0}
    print(f"seed {seed} | library {len(lib) - 7}\nOPENING HAND:", *lib[:7], sep="\n  "); s["hand7"] = lib[:7]; s["lib"] = lib[7:]; save(s)
else:
    s = load(); lib = s["lib"]
    if cmd == "mull":
        lib += s.pop("hand7"); s["mulls"] += 1
        random.Random(f"{s['seed']}-m{s['mulls']}").shuffle(lib)
        s["hand7"] = lib[:7]; s["lib"] = lib[7:]
        print(f"MULLIGAN {s['mulls']} (bottom {max(0, s['mulls'] - 1)} after the free one):", *s["hand7"], sep="\n  ")
    elif cmd == "draw":
        n = int(a[0]) if a else 1
        print("DRAW:", *lib[:n], sep="\n  "); s["lib"] = lib[n:]; s["drawn"] += n
    elif cmd == "peek": print(f"TOP {a[0]}:", *lib[:int(a[0])], sep="\n  ")
    elif cmd == "mill": print("MILLED:", *lib[:int(a[0])], sep="\n  "); s["lib"] = lib[int(a[0]):]
    elif cmd == "put": s["lib"] = [a[1]] + lib if a[0] == "top" else lib + [a[1]]; print(f"put {a[1]} on {a[0]}")
    elif cmd == "take": print("TOOK:", lib.pop(find(lib, a[0])))
    elif cmd == "bury": n = int(a[0]); s["lib"] = lib[n:] + lib[:n]; print(f"moved top {n} to bottom")
    elif cmd == "shuffle": random.Random(f"{s['seed']}-s{len(lib)}-{s['drawn']}").shuffle(lib); print("shuffled")
    elif cmd == "status": pass
    elif cmd == "odds":
        s["odds"] = {**ODDS, **s.get("odds", {}), **{k: float(v) for k, v in (x.split("=") for x in a)}}
        if any(x.startswith("answers=") for x in a): s["answers"] = int(s["odds"]["answers"])  # setting the pool refills it
        print("odds", s["odds"], "| answers left", s.get("answers", int(s["odds"]["answers"])))
    elif cmd == "react":
        o = {**ODDS, **s.get("odds", {})}; left = s.get("answers", int(o["answers"]))
        if a[0] not in ("counter", "removal"): sys.exit(__doc__)
        p = o[a[0]] + o["key"] * ("key" in a) + o["storm"] * ("storm" in a)
        ward = next((int(x[5:]) for x in a if x.startswith("ward=")), 0)
        if a[0] == "removal": p *= o["ward"] ** (ward / 2)
        p = min(p, 0.9) if left > 0 else 0.0
        hit = random.SystemRandom().random() < p
        if hit: s["answers"] = left = left - 1
        print(f"REACT {' '.join(a)}: chance {p:.0%} -> {'ANSWERED (' + ('countered' if a[0] == 'counter' else 'removed') + ')' if hit else 'no response'} | answers left {left}")
    else: sys.exit(__doc__)
    save(s); print(f"[library {len(s['lib'])} | seed {s['seed']}]")
