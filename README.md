# slide-remix

A Claude skill that turns a slide screenshot, an article diagram or rough notes into a clean, flat 16:9 diagram — as **HTML + PNG** and, from the same layout spec, as an **editable PPTX on any .pptx template** (native shapes, template theme colours).

It also does **slide forensics**: what a screenshot was probably made with, which inputs you need, and how to rebuild it.

## How it works
- One spec file (`spec.py`, 1280×720 px) describes the page with a few primitives (boxes, text, connectors, badges, icons, bullets) and **semantic colours** (`C('orange')` = enforcement, `C('blue')` = call path, …).
- `scripts/make_html.py` renders it to inline-SVG HTML and a 2× PNG (headless Chromium, self-installing).
- `scripts/make_pptx.py` probes the template (canvas, hue-based colour mapping, layout, title placeholder, footer safe area), fits the title, builds the slide and runs QA: validate, diff vs template, lint, 6 % stress render, text check.
- Legend colour words follow the template mapping automatically (`cw('purple')` becomes "青" when the template has no purple).

## Install
Zip this folder as `slide-remix.skill` (`zip -r slide-remix.skill slide-remix`) and add it in Claude → Skills. Then just ask, e.g. "把这张图做成 html 和 pptx" or "分析这个 slide 是用什么做的".

## Quick start (CLI)
```bash
python3 scripts/make_html.py --spec examples/steps_pipeline.py --out out.html --png out.png
python3 scripts/make_pptx.py --spec examples/steps_pipeline.py --template YourTemplate.pptx \
    --out out.pptx --qa-dir QA --ea-font "Microsoft YaHei"
bash tests/run_examples.sh /tmp/reg YourTemplate.pptx      # regression over all examples
```
Requirements: Python 3, Pillow, LibreOffice + pdftoppm (for the PPTX QA render), playwright (auto-installed).

## Layout
`SKILL.md` (instructions) · `scripts/` · `examples/` (three-zone architecture, phase pipeline, simple N-step flow, card grid) · `references/` (design system, layout patterns, analysis checklist, lessons) · `tests/`.

## Credits
`scripts/vendor/` (slidekit.py, build_slide.py, list_layouts.py) comes from [screenshot-to-template-slide](https://github.com/puww1010/screenshot-to-template-slide), MIT License — see `scripts/vendor/LICENSE-screenshot-to-template-slide`. Example names and content are fictional or generic.

## License
MIT — see [LICENSE](LICENSE).
