<p align="center"><img src="logo.svg" width="128" alt="mtg-deck-building logo"></p>

# mtg-deck-building

A Claude Code skill for Magic: The Gathering Commander (EDH) decks. Claude uses it to analyze, cut, upgrade, budget, and playtest a deck. It judges each deck against a small knowledge base of deck-building rules. It gets card text, legality, and prices from live data, not from memory.

## What it does

- Analyzes a decklist and gives cuts and adds, each with a reason and a price.
- Checks the card count, colour identity, bans, and duplicates.
- Gets oracle text from Scryfall, synergy data from EDHREC, and prices from Card Kingdom.
- Plays solo test games (goldfish) with a real random shuffle and optional opponent interaction.
- Adds a new video or article to the knowledge base as short rules.

## Install

1. Clone the repo into your skills folder:

   ```sh
   git clone https://github.com/haziqhilmismail/mtg-deck-building ~/.claude/skills/mtg-deck-building
   ```

2. Start Claude Code. The skill loads from this path.
3. Give Claude a decklist or a commander, and ask it to analyze or build the deck.

Requirements: Python 3.8 or later (standard library only), `curl`, and internet access. There are no API keys and no env vars.

## How it runs

Claude runs the scripts when a task needs them. There is no service, timer, or cron job. Before the first price lookup in a session, Claude downloads the Card Kingdom price list (about 70 MB) to `ck.json` in the working directory:

```sh
curl -sSL -A "Mozilla/5.0" -o ck.json https://api.cardkingdom.com/api/v2/pricelist
python3 ~/.claude/skills/mtg-deck-building/scripts/mtg.py check deck.txt 'Commander Name'
```

A deck file has one card per line, in the form `1 Card Name`.

## Folder layout

```
SKILL.md              Instructions that Claude follows
scripts/mtg.py        Card text, price, legality check, Scryfall search, EDHREC lookup
scripts/goldfish.py   Shuffle, draw, mulligan, opponent interaction rolls, 33-card split
knowledge/            Deck-building rules, one file for each source video
logo.svg              Logo
LICENSE               MIT license
```

## Knowledge sources

The files in `knowledge/` are short rule summaries of public videos by Based Deck Department and The Trinket Mage. They do not quote the videos. Each file links to its source video.

## License

MIT. See `LICENSE`.
