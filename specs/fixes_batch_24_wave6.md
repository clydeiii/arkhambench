# Fixes batch 24 — ledger 154 (play-side foreign-pointer guard)

Tests in tests/test_fixes_batch_24.py. Full suite green.

arkham/cli.py resolve_run_dir: when AHLCG_CAMPAIGN is set and resolution
falls through to the global .current_run pointer, REFUSE (EngineError
naming both paths) if the pointed run dir is not inside the campaign dir —
same guard record_current_run has. Explicit --run and AHLCG_RUN stay
unrestricted. The campaign active_run branch is unaffected.

Tests: (a) AHLCG_CAMPAIGN set + global pointer at a foreign campaign's run
-> EngineError; (b) pointer inside the campaign -> resolves; (c) no
AHLCG_CAMPAIGN -> legacy behavior unchanged; (d) AHLCG_RUN still outranks.
