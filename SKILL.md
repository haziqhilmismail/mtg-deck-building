---
name: mtg-deck-building
description: Build, analyze, cut, or upgrade Magic: The Gathering Commander (EDH) decks using a distilled deck-building knowledge base plus live card text and Card Kingdom prices. Use when the user shares a decklist or commander and asks to analyze, improve, rebuild, budget, or "be brutal" with a deck, asks what to cut or add, or asks to add a new video/article to the deck-building knowledge.
---

# MTG deck building

Two jobs: **(A) work on a deck**, **(B) add new knowledge**.

## A. Work on a deck

Read every file in `knowledge/` first. They are the rules you judge the deck by. Where two files disagree, the newer file wins unless the user's bracket or goal says otherwise (power advice for high brackets, fun/novelty advice for casual).

1. **Get the inputs. Ask before touching a card.** If the decklist is missing, ask for it; do not guess. Then ask every intake question the request has not already answered, in one message, and skip the ones it has.

   Ask every time:
   - **Job:** tune (more reliable, same strength), power up (higher ceiling, speed or resilience; may change bracket), re-theme, or build from scratch? See `knowledge/2026-07-04-optimizing-vs-upgrading.md`.
   - **Bracket, and the turn games should end by.** Sets the mana the win may cost (`knowledge/2026-04-24-build-backwards-end-in-mind.md`).
   - **How it should win, and what is off the table:** infinite combos, tutors, poison, land destruction, extra turns.
   - **Budget:** the cap, whose prices, whole deck or new purchases only, and whether owned cards are preferred.
   - **What must stay and what they already dislike:** tagged packages, pet cards, staples they want regardless (Sol Ring) or are tired of.

   Ask when the list does not make it obvious:
   - **What goes wrong in play:** stuck on colours, too slow, out of cards, folds to a wipe, cannot close, boring.
   - **Fun or strongest:** novel on-theme cards, or the best card for the slot.
   - **The table:** how much removal, wipes, graveyard hate, fast decks.
   - **The commander's role:** engine, enabler or payoff, and how early it should land.
   - **Same game every time, or variety:** sets tutor and redundancy counts.

   Ask before delivering:
   - **Playtest, and how many games.**
   - **Report format:** changes and new total only, or the full list each time.

   Defaults when unanswered: Card Kingdom, cheapest in-stock legal printing, basics free; budget covers the whole deck; every tagged package in the original list stays; no game changers added without asking.

   Why this step exists: a Witherbloom rebuild skipped "what must stay" and cut the owner's two-mana draw creatures, mana elves and a token spell from their tagged package; each had to be put back one message at a time. Before cutting, re-read the original list's tags and say which package each cut belongs to.
2. **Get real data. Never trust memory for card text, legality, or price.**
   - `curl -sSL -A "Mozilla/5.0" -o ck.json https://api.cardkingdom.com/api/v2/pricelist` (about 70 MB, run once per session in the working directory)
   - `python3 ~/.claude/skills/mtg-deck-building/scripts/mtg.py text deck.txt` prints oracle text, mana value, colour identity (`id:`), Commander legality, game-changer flag
   - `python3 ~/.claude/skills/mtg-deck-building/scripts/mtg.py price deck.txt` prints cheapest price per card and the total
   - `python3 ~/.claude/skills/mtg-deck-building/scripts/mtg.py check deck.txt 'Commander Name'` fails on wrong card count, off-colour cards, banned cards, or duplicates
   - `python3 ~/.claude/skills/mtg-deck-building/scripts/mtg.py search '<scryfall query>' 60 deck.txt` finds candidates with prices, sorted by EDHREC rank; the optional deck file marks each hit `have` or `MISSING`
   - `python3 ~/.claude/skills/mtg-deck-building/scripts/mtg.py edhrec '<Commander Name>' deck.txt` lists EDHREC's cards for that commander by synergy with prices, and marks each one `have` or `MISSING` against the deck file
   - `scripts/` is inside this skill's directory; call it by absolute path from the working directory that holds `ck.json`. Deck files are `1 Card Name` per line.
3. **Write the game plan in three lines** before touching a card: how the deck wins, what the ideal turns 1 to 4 look like, which turn it needs each piece by.
4. **Pattern pass. Never build a candidate pool from memory.** Do all four before choosing a single card:
   - **Name the patterns.** Read the commander's oracle text from `mtg.py text` and write one line per clause: which card property does this clause reward? Example, Ral, Monsoon Mage: "instant and sorcery spells cost {1} less" rewards spells with generic mana in their cost, so a `{1}{R}` draw-two beats a `{U}` cantrip that gets no discount; "flip a coin" rewards coin-flip payoffs.
   - **Search each pattern on Scryfall. This is the main source; EDHREC is only a cross-check.** Run at least two queries per pattern, one with an oracle tag and one with oracle text, always with the identity (`id<=ur`), and pass the deck file so hits are marked: `mtg.py search '<query>' 40 deck.txt`. Read every `MISSING` hit. Tags that work: `otag:rummage` (discard, draw two), `otag:impulsive-draw` (exile and play), `otag:impulse` (look at top cards), `otag:draw`, `otag:ritual`, `otag:coin-flip`, `otag:cost-reducer`; also `keyword:storm`, `mv=2`, `t:instant`, `usd<5`. A tag that returns nothing is probably misspelled: fall back to `o:"..."`. Scryfall finds on-pattern cards that are new or unpopular, which EDHREC under-ranks.
   - **Then cross-check with `mtg.py edhrec`** for the commander against the deck file. Every `MISSING` card with synergy +0.30 or more is either added or gets a one-line reason in the report (price, bracket, off-plan). A card EDHREC shows that no Scryfall query found means a pattern was missed: name the pattern and search it.
   - **Re-test each generic staple against the patterns.** A draw, ramp or interaction card the commander does not improve loses its slot to an on-pattern card of similar quality.

   Why this step exists: a Ral list built from recalled blue-red staples missed Tavern Scoundrel (in 70% of Ral decks on EDHREC) and eight discounted draw spells, and the owner found the deck boring because the commander did nothing.
5. **Tag every card** with its job (land, ramp, card advantage, interaction, protection, wipe, engine/payoff, finisher) and count each group against the knowledge files' numbers.
6. **Cut.** Challenge every card's right to its slot: off-plan, win-more, "maybe great", autopilot staple, too expensive for its effect in mana or in dollars.
7. **Add.** Take candidates from the pattern pass, not from recall, and put the commander's identity in every query (`id<=ur` for blue-red). Prefer cheap, flexible, double-duty cards that fit this commander. Verify text and legality of every add.
8. **Check colour identity. Never skip this.** Run `mtg.py check` on every list before showing it, including after a one-card swap, and fix anything it prints. A card's colour identity is every mana symbol on it: the cost, hybrid symbols (`{R/G}` is red and green, so Manamorphose is illegal in a blue-red deck), Phyrexian symbols, symbols in the rules text, and both faces of a double-faced card. Being "legal in Commander" does not mean legal in this deck.
9. **Check the rest:** total under budget, all adds in stock, land count, curve and average mana value, each group's count.
10. **Report:** verdict on the current list, the commander's patterns with the queries run for each, cuts with one-line reasons, adds with price and job, the high-synergy EDHREC cards left out and why, the final list grouped by job, the turn-by-turn plan, the philosophy, and every place you deviated from the knowledge on purpose and why. State what was not verified (no playtesting).

**The deck file is the only source of truth.** Save the user's list to a file as soon as they give it. Make every change by editing that file, run `check` and `price` on the file, and print lists by reading the file. Never retype a decklist from memory or from earlier in the conversation. Tell the user the file path whenever it changes.

**After every change to a list** (a swap, a budget change, a fix, however small): say what changed and the new total, then ask the user whether they want the full list. Do not print the full list unprompted. When they say yes, print it as one plain block, `1 Card Name` per line, ready to paste into Archidekt or Moxfield.

## B. Add new knowledge

When the user gives a new video or article:

1. Get the content. Video: use the `watch` skill with `--detail transcript`. Auto-captions repeat each line three times; de-duplicate before reading.
2. Write `knowledge/<yyyy-mm-dd>-<short-slug>.md` using the same shape as the existing files: source line, then rules as short imperative bullets, with every number kept exact.
3. Keep only what changes a deck-building decision. Drop intros, sponsor reads, and anecdotes.
4. If a new rule contradicts an existing file, add a `Conflicts with:` line naming the file and rule. Do not edit or delete the older file.

## C. Playtest (goldfish)

Use after building a list, or when the user asks to playtest. `scripts/goldfish.py` shuffles with a real random seed and keeps the library order in `gf.json`. **Never read `gf.json`, and never choose a seed after seeing a hand.** Only use cards the script has printed.

1. `goldfish.py new deck.txt 'Commander Name'` deals seven. Decide keep or mulligan and say why (lands, a play for turns 1 to 3, a route to the commander). `mull` reshuffles; the first is free, then `put bottom` one card per extra mulligan.
2. Play the number of turns the target bracket's game lasts (see `knowledge/2026-04-24-build-backwards-end-in-mind.md`), and ask for the bracket if it is not stated:

   | Bracket | Turns to play |
   |---|---|
   | 1 to 2 | 10 |
   | 3 | 8 |
   | 4 to 5 | 5 |

   Each turn is its own `draw` call made before deciding anything. Skip the turn-1 draw only if the user says they are on the play in a 1v1; Commander draws on turn 1.
3. For every turn show, in this order: the card drawn, hand, battlefield, mana available, the options considered, the play chosen and why, and the running damage or progress towards the win.
4. Enforce the rules yourself: one land per turn, tapped lands, exact colours, summoning sickness, sorcery timing, commander cost. Look up oracle text with `mtg.py text` instead of recalling it.
5. Card effects go through the script: draws use `draw`; scry, surveil, Ponder and Brainstorm use `peek` then `bury`, `put` or `draw`; tutors use `take` then `shuffle`; self-mill uses `mill`.
6. Play at least 3 games with different seeds before judging, and report per game: the seed, mulligans, lands by turn 5, the turn the commander came down, dead cards in hand, and damage or board on the last turn played. Say whether the deck could have won by the bracket's last turn. Then list what the games suggest changing.
7. Append every game to `playtest-log.md` beside the deck file (seed, mulligans, commander turn, opponents' life after each of the last two turns, win turn, one-line note), and read that log before judging so results from earlier sessions count. When the user asks for a win turn, play one turn past it and report wins by each turn out of the total.
8. Sequencing rules learned in play: cast impulse-draw spells (Jeska's Will, Light Up the Stage, Expressive Iteration) before the land drop; play tapped lands on the turns you have nothing to cast; only target your own spell with Pact of Negation when it wins that turn.
9. **Opponent interaction (use when the user wants a realistic test, and always for bracket 3 and up once the solo games are done).** `goldfish.py react` rolls whether the table answers; never decide this yourself and never re-roll.
   - Every spell that matters: `react counter`. A countered spell goes to the graveyard, its mana is spent, and it still counts for storm and cast triggers.
   - Every engine permanent when it resolves, and the commander at the start of each of your turns while it is out: `react removal`. A removed commander returns to the command zone and costs {2} more.
   - Add `key` when the play is game-changing: the commander's engine piece (for example Curiosity landing on Ghyrson), a tutor fetching the win, the combo piece itself, or the commander once its engine is attached.
   - Add `storm` when you are visibly going off: from the third spell in one turn, or when lethal is on the stack.
   - Add `ward=N` for a target with ward {N}; removal odds are halved per {2} of ward. Hexproof or a held protection spell you can pay for: skip the roll and spend the protection instead when the roll says ANSWERED.
   - Defaults per roll: counter 5%, removal 8%, +10% for `key`, +15% for `storm`, 6 answers shared by the whole table per game (when they run out, nothing more is answered). Change them with `goldfish.py odds name=value` to match the pod, and report the odds used.
   - Your own counterspells answer an ANSWERED roll: cast one (pay its cost) and the original play goes through.
   - Report solo and with-interaction results separately.
10. State the limits every time: solo games have no opponents, so no removal, counterspells, blockers, or opposing triggers; `react` games add counterspells and spot removal by odds only, with no board wipes, blockers, or opposing clocks. Give opponent-dependent cards zero value unless the user sets an assumption (for example "each opponent casts one spell of mana value 3 or less per turn").

### 33-card thirds (see `knowledge/2025-04-27-33-card-deck-method.md`)

Run this before full-deck goldfishing when reviewing or building a list.

1. Tag all 99 non-commander cards with one role each in a file: `1 Card Name # role`. Use the deck's own roles (for example land, engine, payoff, mana, advantage, cantrip, tutor, counter, removal, protection, wipe, finisher). Within a role, list cards cheapest first so each third gets a mix.
2. `goldfish.py split tagged.txt` writes `third-A.txt`, `third-B.txt`, `third-C.txt` and prints the role table. Report every flag: `UNEVEN` means one third is short of that role; `ONE-OFFS` means fewer than three, so at least one third has none.
3. Goldfish each third once for 5 turns, each in its own directory: `goldfish.py new ../third-A.txt ''`. The commander is still castable from the command zone.
4. Compare the three games. A third that cannot function shows which role is thin. Fix the counts, not the single card.

Limits found in use:
- A 33-card library runs out fast with a draw engine (one test had 2 cards left on turn 5). Stop at turn 5, decline optional draws when the library is under 5, and say so. Judge draw engines on the full 99.
- One game per third is three games total. Do not draw conclusions about land count from them alone; compute the odds (hypergeometric) and report those next to what happened.
