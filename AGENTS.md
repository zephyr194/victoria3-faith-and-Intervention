# Development rules

- Runtime content lives in `mod/`; keep identifiers prefixed `fia_`, `fia.` or `je_fia_`.
- Preserve vanilla files. Add a child on-action; do not replace vanilla monthly effects.
- Balance/localization source of truth: `balance.json`, `localization.json`. Run `python3 tools/build_content.py` after changes. Keep event/localization BOMs.
- Run `python3 tools/validate.py`, `python3 -m unittest discover -s tests -v`, and both `tools/package.py --game-version` variants before committing runtime changes.
- Recheck scope identity and all cleanup paths when changing cross-country effects. `possible` may check transient eligibility; `valid` must not erase active goals because a timer or demographic value changed.
- No instant pop conversion, silent law activation, or territory transfer in the religious-guarantee goal.
- Tests execute a finite script subset, not the game engine. Do not label a version compatible, a multiplayer save safe, or AI functional without a recorded game run.
- Keep DESIGN.md aligned with the actual implementation; future features must be explicitly marked as future.
