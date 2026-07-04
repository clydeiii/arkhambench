# Fixes Batch 3 Report

Implemented the batch 3 engine fixes and tests.

## Rule/conflict notes

- Locked Door tie handling matches `docs_agent/rules_reference.md`: tied "most clues" locations are chosen by the investigator, including the all-zero case.
- No conflicts found between `specs/fixes_batch_3.md`, the Rules Reference, and card JSON.

## Verification

- `python3 -m unittest discover -s tests` — OK, 149 tests.
- `python3 -m arkham.fuzz --games 50 --scenario the_gathering --investigator roland` — OK.
- `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --investigator roland` — OK.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator daisy` — OK.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator skids` — OK.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator agnes` — OK.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator wendy` — OK.
