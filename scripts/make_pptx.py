#!/usr/bin/env python3
"""spec.py + ANY template.pptx -> editable one-slide PPTX (native shapes, scheme colours) + stress-render QA.

usage: python3 make_pptx.py --spec page_spec.py --template T.pptx|demo --out OUT.pptx --qa-dir QA_DIR
                            [--ea-font "PingFang SC" | "Microsoft YaHei"] [--layout NAME] [--source source_text.txt]
exit codes: 0 ok (read [WARN] lines) · 1 [FAIL] — the PPTX is missing or must not be delivered
Steps: template_probe (cached as OUT.probe.json) -> title fit -> vendor/build_slide.py (validate, diff vs template,
lint, 6 % stress render) -> text checks.
"""
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_lib as L
from make_html import load_spec, build_primitives, text_check, fail
from template_probe import resolve_pptx_skill, resolve_template

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True); ap.add_argument('--template', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--qa-dir', required=True); ap.add_argument('--ea-font'); ap.add_argument('--layout'); ap.add_argument('--source')
    ap.add_argument('--reprobe', action='store_true')
    ap.add_argument('--color', action='append', default=[], metavar='ROLE=SCHEME',
                    help='override the automatic mapping, e.g. --color orange=accent1 (repeatable)')
    a = ap.parse_args()
    a.template = resolve_template(a.template)
    import zipfile
    if not os.path.isfile(a.template): fail(f'template not found: {a.template}')
    try:
        zipfile.ZipFile(a.template).read('ppt/presentation.xml')
    except (zipfile.BadZipFile, KeyError):
        fail(f'{a.template} is not a .pptx (PowerPoint) file — .potx/.key/.pdf are not supported; save it as .pptx')
    out_dir = os.path.dirname(os.path.abspath(a.out))
    if not os.path.isdir(out_dir) or not os.access(out_dir, os.W_OK): fail(f'output folder not writable: {out_dir}')
    build_primitives(load_spec(a.spec), a.spec)        # fail fast on spec problems, before the slow probe
    skill = resolve_pptx_skill()
    probe_path = os.path.splitext(a.out)[0] + '.probe.json'
    if a.reprobe or not os.path.exists(probe_path) or json.load(open(probe_path)).get('template') != os.path.abspath(a.template) \
            or (a.layout and json.load(open(probe_path)).get('layout') != a.layout):
        cmd = [sys.executable, os.path.join(HERE, 'template_probe.py'), a.template, '--out', probe_path]
        if a.layout: cmd += ['--layout', a.layout]
        r = subprocess.run(cmd, capture_output=True, text=True)
        for line in (r.stdout + r.stderr).splitlines():
            if line.startswith('[WARN]'): print(line)
        if r.returncode:
            err = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
            fail(next((l[7:] for l in err if l.startswith('[FAIL]')), 'template probe failed: ' + (err[-1] if err else '?')))
    probe = json.load(open(probe_path))
    for ov in a.color:
        if '=' not in ov or ov.split('=')[1] not in probe['theme'] or ov.split('=')[0] not in L.ROLES:
            fail(f'--color {ov}: expected ROLE=accentN, ROLE in {", ".join(L.ROLES)}, scheme in {", ".join(probe["theme"])}')
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
    P = build_primitives(m, a.spec); texts = L.all_text(P) + [m.TITLE]
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
           '--page', os.path.join(HERE, 'to_pptx.py'), '--out', a.out, '--layout', probe['layout'], '--qa-dir', a.qa_dir,
           '--pptx-skill', skill or 'none']
    if cjk: cmd += ['--lang', 'zh', '--ea-font', a.ea_font]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    log = r.stdout + r.stderr
    for line in log.splitlines():
        if line.startswith('[') and not line.startswith(('[text on slide]', '[validate:basic] ISSUES')): print(line)
    if r.returncode:
        err = [l for l in log.splitlines() if l.strip()]
        fail(next((l[7:] for l in err if l.startswith('[FAIL]')), 'PPTX build failed: ' + (err[-1] if err else '?'))
             + ' (if this names your spec, fix the spec; otherwise rerun doctor.py)')
    vline = next((l for l in log.splitlines() if l.startswith('[validate')), '')
    if vline.startswith('[validate:basic]') and 'PASSED' not in vline:
        # built-in check: judge only issues our build added (some templates trip it already, e.g. attribute order)
        sys.path.insert(0, os.path.join(HERE, 'vendor')); import build_slide as BS
        new = sorted(set(BS.basic_validate(a.out)) - set(BS.basic_validate(a.template)))
        vline = ('[validate:basic] PASSED (pre-existing template findings ignored)' if not new
                 else '[validate:basic] new issues: ' + '; '.join(new[:3]))
        print(vline)
    if not ('PASSED' in vline):
        fail(f'validate: {vline or "no validation result"} — do not deliver this file; rerun doctor.py and check the template')
    if '[qa render] [' not in log or "[qa render] []" in log:
        import shutil
        why = ('LibreOffice not installed' if 'LibreOffice not found' in log or not (shutil.which('soffice') or shutil.which('libreoffice')) else 'pdftoppm not installed' if 'pdftoppm not found' in log
               else 'LibreOffice timed out' if 'timed out' in log else 'render produced no image')
        print(f'[WARN] no preview render: {why}; visual QA skipped — tell the user and ask them to check the slide in PowerPoint')
    slide_txt = log.split('[text on slide]', 1)[-1]
    norm = lambda s: ''.join(s.replace('‑', '-').split())
    lost = [t for t in texts if norm(t) and norm(t) not in norm(slide_txt)]
    print('[text check] spec text missing in PPTX:', lost or 'none')
    if a.source: text_check(texts, a.source)

if __name__ == '__main__':
    main()
