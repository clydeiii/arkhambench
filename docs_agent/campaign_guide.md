# Campaign Guide

Campaign mode plays Night of the Zealot as a persistent sequence:

```
./ahlcg campaign new --dir campaigns/<name> --investigator roland --difficulty standard --seed 42
./ahlcg deckbuild options
./ahlcg deckbuild swap --in <code> --out <code>
./ahlcg deckbuild done
./ahlcg campaign next
./ahlcg state
./ahlcg do <n> --why "..."
./ahlcg campaign record
./ahlcg upgrade options
./ahlcg upgrade buy <code> --replace <old-code>
./ahlcg upgrade buy <code> --remove <old-code>
./ahlcg upgrade done
./ahlcg campaign next
```

`campaign new` creates `campaign.json` and sets `.current_campaign`. Return to Night of
the Zealot is the default; add `--original` for the original campaign. Scenario runs are
created under the campaign directory and `.current_run` is updated for normal play.

## Before the First Scenario

New campaigns start in a free `deckbuild` phase before the first scenario. Use
`./ahlcg deckbuild options` to see legal implemented level-0 swap-ins and the current
deck list, then use `./ahlcg deckbuild swap --in <code> --out <code>` as often as needed.
Swaps cost 0 XP and are only available at campaign start. Run `./ahlcg deckbuild done`
to lock the deck; `./ahlcg campaign next` also locks it automatically.

Once the campaign has started, level-0 additions happen through the normal upgrade
window and cost 1 XP under the Rules Reference. Sidegrading level-0 cards during upgrade
phases is usually XP-inefficient; do that work in the free opening deckbuild window.

## Flow

1. Before the first scenario, optionally use `deckbuild ...` to make free level-0 swaps.
2. `campaign next` starts the current scenario with the campaign deck, trauma, seed, and
   campaign log inputs.
3. Play until `GAME OVER`.
4. `campaign record` ingests the run's `result.json`, adds earned XP, carries trauma,
   updates the campaign log, and moves to the upgrade phase.
5. If Lita was earned, choose `./ahlcg campaign lita --include` or `--skip`. Lita does
   not count toward the 30-card deck size.
6. Spend or bank XP with `upgrade ...`, then run `upgrade done`.
7. Repeat `campaign next`.

The Devourer Below slot exists for campaign continuity, but the scenario is not playable
until phase C3. Starting it raises a clear not-implemented error.

## XP Rules

- New cards cost `max(1, level)`.
- Same-title upgrades use `--replace`; cost is the level difference, minimum 1.
- A second copy of an XP card you already own is a new purchase at full cost.
- You may bank XP by buying nothing and running `upgrade done`.
- Deck size must be exactly 30 counted cards at `upgrade done`.
- Signatures, weaknesses, and story assets cannot be removed.
- Max two copies by title across all levels.

Examples:

```
./ahlcg upgrade buy 50002 --replace 01024
```

Upgrades Dynamite Blast(0) to Dynamite Blast(2), costs 2 XP, and keeps deck size stable.

```
./ahlcg upgrade buy 01026 --remove 01087
```

Adds Extra Ammunition(1), costs 1 XP, and removes Flashlight because the deck was already
at 30 counted cards.

## Warnings

Trauma persists and starts future scenarios as damage or horror. If an investigator is
killed or driven insane, they are added to the killed list and must be replaced:

```
./ahlcg campaign replace --investigator daisy
```

The replacement starts with a fresh killbray deck, 0 XP, and 0 trauma. Earned story
assets such as Lita transfer.

Campaign weaknesses persist in the campaign deck. Do not remove them during upgrades.
