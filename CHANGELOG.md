# Changelog

## v1.1 — 2026-11-18
Hardening after a first external review ("核心能力无法直接使用、环境兼容与失败提示不够完善").

**Added**
- `scripts/doctor.py`: pre-run check (Python, Pillow, playwright/Chromium, LibreOffice, pdftoppm, zip, CJK font, optional pptx skill, template). Reports which outputs this machine can produce (HTML / PNG / PPTX / preview) with macOS and Debian/Ubuntu install hints; `--need` sets the exit code, `--fix` tries installs.
- Bundled demo template (fictional ACME brand): `--template demo`. Stored as base64 text and decoded once into the temp dir, so the skill folder can stay read-only.
- `scripts/crop.py`: zoom / tile screenshots for slide forensics (mode A).
- `examples/simple_steps.source.txt`: sample source-text list for the text check.

**Changed**
- Clear one-line `[FAIL]` / `[WARN]` messages instead of tracebacks: missing or non-.pptx template, missing spec, spec errors (unknown colour role, bad icon kind, with file and line).
- Exit codes: `0` ok · `1` `[FAIL]`, do not deliver · `2` (make_html) HTML ok, PNG failed.
- Validation: works without the Anthropic pptx skill (`PPTX_SKILL=none` or not installed) using the built-in check, comparing only issues added on top of the template; any failure now stops the build.
- No LibreOffice / pdftoppm: explicit warning that the preview render and visual QA were skipped; footer safe-area detection falls back to 680 px with a warning.
- Screenshot: 120 s overall budget, per-step timeouts, quick offline detection, no apt-get outside Debian/Ubuntu. Offline it now fails in about a second instead of hanging for minutes.
- `tests/run_examples.sh`: runs doctor first, defaults to the demo template, accepts the built-in validation, reports PNG/preview gaps as warnings.
- SKILL.md: step 0 "run doctor", a "common failures" table, demo-template usage.

## v1.0 — 2026-11-18
First release: slide forensics, flat HTML/PNG redraw, any-template editable PPTX from one px spec.
