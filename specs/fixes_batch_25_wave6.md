# Fixes batch 25 — ledger 155 (slot overflow at entry time)

Single fix; tests in tests/test_fixes_batch_25.py; full suite green.
When an asset that occupies a slot enters play OUTSIDE the play action
(weakness revelation like The Necronomicon 01009, story/gain-control
entries), enforce_slot_capacity / the overflow decision must run
immediately as part of the entry, before the enclosing step continues
(upkeep resource gain, next revelation, etc.). Find the upkeep draw path
that puts 01009 into the threat area and hook the check there (and any
sibling entry points that defer it). Test: Daisy with 2 hand assets draws
the Necronomicon in upkeep -> overflow decision presented BEFORE the
resource gain; resource granted after resolution; no double-gain.
