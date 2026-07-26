## 2026-07-25T09:55:45+00:00
- Round: 2
- Phase: Investigation
- Description: The compact status line shown after do/actions commands (e.g. '[R2·Investigation ... Act1 Agd1 doom2/3]') displays agenda doom as 2/3, but the authoritative './ahlcg state' command shows the actual agenda doom is only 1/3. The compact line appears to be summing the agenda's real doom (1) with the separate doom counter placed on Arcane Initiate (1, from its own 'place 1 doom on it' forced ability) into a single 'doom' figure, mislabeling it as the agenda's doom. This is purely a display bug in the compact status line (state/score are unaffected) but could mislead an agent tracking doom-to-threshold timing under pressure. Steps to reproduce: play Arcane Initiate (places 1 doom on itself), then any Mythos phase that places 1 doom on the agenda; compact line reads doom2/3 while './ahlcg state' correctly reads doom 1/3.

