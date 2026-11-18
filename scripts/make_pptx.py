#!/usr/bin/env python3
"""spec.py + ANY template.pptx -> editable one-slide PPTX (native shapes, scheme colours) + stress-render QA.

usage: python3 make_pptx.py --spec page_spec.py --template T.pptx --out OUT.pptx --qa-dir QA_DIR
                            [--ea-font "PingFang SC" | "Microsoft YaHei"] [--layout NAME] [--source source_text.txt]
Steps: template_probe (cached as OUT.probe.json) -> title fit -> vendor/build_slide.py (validate, diff vs template,
lint, 6 % stress render) -> text checks.
"""
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_lib as L
from make_html import load_spec, text_check

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True); ap.add_argument('--template', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--qa-dir', required=True); ap.add_argument('--ea-font'); ap.add_argument('--layout'); ap.add_argument('--source')
    ap.add_argument('--reprobe', action='store_true')
    ap.add_argument('--color', action='append', default=[], metavar='ROLE=SCHEME',
                    help='override the automatic mapping, e.g. --color orange=accent1 (repeatable)')
    a = ap.parse_args()
    probe_path = os.path.splitext(a.out)[0] + '.probe.json'
    if a.reprobe or not os.path.exists(probe_path) or json.load(open(probe_path)).get('template') != os.path.abspath(a.template) \
            or (a.layout and json.load(open(probe_path)).get('layout') != a.layout):
        cmd = [sys.executable, os.path.join(HERE, 'template_probe.py'), a.template, '--out', probe_path]
        if a.layout: cmd += ['--layout', a.layout]
        subprocess.run(cmd, check=True, capture_output=True)
    probe = json.load(open(probe_path))
    for ov in a.color:
        role, sch = ov.split('=')
        import colorsys
        from template_probe import rel_lum, hue_word
        hx = probe['theme'][sch]; r, g, b = [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        h, l, _ = colorsys.rgb_to_hls(r, g, b); lum = rel_lum(hx)
        probe['colors'][role] = dict(scheme=sch, hex=hx, word=hue_word(h * 360, l),
                                     base='<a:lumMod val="60000"/>' if lum > .55 else ('<a:lumMod val="75000"/>' if lum > .35 else ''))
        probe['color_notes'] = [n for n in probe['color_notes'] if not n.startswith(role + ':')] + [f'{role}: overridden -> {sch} #{hx}']
    if a.color:
        probe_path = probe_path.replace('.probe.json', '.probe.override.json'); json.dump(probe, open(probe_path, 'w'), ensure_ascii=False)
    print('[layout]', probe['layout'])
    words = {}
    for r in ('orange', 'blue', 'purple', 'green', 'teal'):
        words.setdefault(probe['colors'][r].get('word'), []).append(r)
    for w_, rs in words.items():
        if len(rs) > 1: print(f'[WARN] roles {rs} all map to "{w_}" — if the page uses more than one of them, tell them apart by icon/label or pass --color')
    for n in probe['color_notes']: print('[colors]', n)

    m = load_spec(a.spec)
    L.COLOR_WORDS.update({r: probe['colors'][r].get('word', L.COLOR_WORDS[r]) for r in L.ROLES if r in probe['colors']})
    P = m.build_spec(); texts = L.all_text(P) + [m.TITLE]
    cjk = any(L.is_cjk(ch) for t in texts for ch in t)
    if cjk and not a.ea_font:
        sys.exit('[FAIL] page has Chinese text: ask the user which CJK font to use, then pass --ea-font')

    # ---- title fit ----
    tb = getattr(m, 'TITLE_BOX', (58, 38, 940, 32)); sub_top = getattr(m, 'SUBTITLE_TOP', 84)
    ti, pt_px = probe.get('title'), probe['canvas']['pt_per_px']
    title = {}
    size_pt = ti['size_pt'] if ti else 28
    if ti:
        bx, by, bw, bh = ti['box_px']; ins = ti['ins_px']
        tx = bx + ins['l']; bottom = by + ins['t'] + size_pt / pt_px * 1.25
        if bottom > sub_top + 2 or ti['anchor'] not in ('t', None) and by + bh > sub_top + 2:
            title['box'] = list(tb); tx = tb[0]
            print(f'[title] layout title area ends at {bottom:.0f}px > SUBTITLE_TOP {sub_top}px -> title moved to TITLE_BOX on this slide')
    else:
        title['box'] = list(tb); tx = tb[0]; print('[title] layout has no title placeholder position -> using TITLE_BOX')
    avail = tb[0] + tb[2] - tx
    need = L.est_w(m.TITLE, size_pt / pt_px) * 1.10
    if need > avail:
        sz = size_pt * avail / need
        sz = max(round(size_pt * .7), int(sz // 2 * 2))
        title['sz'] = sz
        print(f'[title] {size_pt:g}pt would run ~{need:.0f}px > {avail:.0f}px available -> {sz}pt on this slide')

    if not title: print('[title] no change (inherits the template title placeholder)')
    # ---- safe area ----
    sb = probe.get('safe_bottom_px')
    if sb:
        bottoms = [p['y'] + p['h'] for p in P if p['k'] == 'rect'] + \
                  [p['y'] + sum(l[2] for l in p['lines']) for p in P if p['k'] == 'text']
        low = max(bottoms)
        if low > sb - 4:
            print(f'[WARN] content reaches {low:.0f}px but the template decoration starts at {sb:.0f}px: compress the spec vertically')
        else:
            print(f'[safe area] content bottom {low:.0f}px < template decoration {sb:.0f}px  OK')

    env = dict(os.environ, SLIDE_REMIX_SPEC=os.path.abspath(a.spec), SLIDE_REMIX_PROBE=os.path.abspath(probe_path),
               SLIDE_REMIX_TITLE=json.dumps(title))
    cmd = [sys.executable, os.path.join(HERE, 'vendor', 'build_slide.py'), '--template', a.template,
           '--page', os.path.join(HERE, 'to_pptx.py'), '--out', a.out, '--layout', probe['layout'], '--qa-dir', a.qa_dir]
    if cjk: cmd += ['--lang', 'zh', '--ea-font', a.ea_font]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    log = r.stdout + r.stderr
    for line in log.splitlines():
        if line.startswith('[') and not line.startswith('[text on slide]'): print(line)
    if r.returncode: print(log[-2000:]); sys.exit('[FAIL] build_slide failed')
    slide_txt = log.split('[text on slide]', 1)[-1]
    norm = lambda s: ''.join(s.replace('‑', '-').split())
    lost = [t for t in texts if norm(t) and norm(t) not in norm(slide_txt)]
    print('[text check] spec text missing in PPTX:', lost or 'none')
    if a.source: text_check(texts, a.source)

if __name__ == '__main__':
    main()
