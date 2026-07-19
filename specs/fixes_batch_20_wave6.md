# Fixes batch 20 — ledger 136 (scenario-conditional mission briefings)

arkham/game.py _write_campaign_mission: replace the hardcoded Devourer
briefing with a per-scenario block chosen by the scenario being launched
(self.state.scenario or the equivalent field available there):
- Gathering family: 3-4 advisory bullets in the same voice (agenda pace,
  the Study/gateway structure, act-3 Lita parley option, resign
  unavailable — check scenario_reference.md for accuracy).
- Midnight Masks family: bullets covering the cultist/clue economy, doom
  clock across agendas 1-2, and that RESIGN IS OFFERED from R1 and ends
  safely at R1 with information gathered.
- Devourer family: keep the existing four bullets verbatim.
Source facts from docs_agent/scenario_reference.md — every claim must be
true for that scenario; do not spoil hidden setup beyond what the reference
already states. Tests in tests/test_fixes_batch_20.py: mission.md for a
campaign Gathering run contains the Gathering block and NOT "Devourer Below
briefing"; MM run mentions resign-offered; DB run unchanged.
