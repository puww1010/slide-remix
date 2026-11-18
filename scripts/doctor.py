#!/usr/bin/env python3
"""slide-remix pre-run check: which outputs can this machine produce?

usage: python3 doctor.py [--need html,png,pptx,preview] [--template T.pptx] [--fix]
  capabilities:  html    = HTML file (always possible with Python + Pillow-free stdlib)
                 png     = PNG screenshot of the HTML (playwright + Chromium)
                 pptx    = editable PPTX on a template (zip, template readable)
                 preview = PPTX stress-render preview for visual QA (LibreOffice + pdftoppm)
  exit 1 only when a capability listed in --need is unavailable. --fix tries the installs that need no root.
"""
import argparse, importlib.util, os, re, shutil, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
MAC = sys.platform == 'darwin'

def hint(mac, apt):
    return f'macOS: {mac} · Debian/Ubuntu: {apt}'

rows, broken = [], set()
def row(level, item, affects, detail='', fix=''):
    rows.append((level, item, affects, detail, fix))
    if level == 'FAIL': broken.update(affects.split('+'))

def check_png(fix):
    from make_html import screenshot
    d = tempfile.mkdtemp(); h = os.path.join(d, 't.html'); p = os.path.join(d, 't.png')
    open(h, 'w').write('<html><body><svg viewBox="0 0 10 10" width="10" height="10"><rect width="10" height="10"/></svg></body></html>')
    return screenshot(h, p, install=fix, budget=180 if fix else 25)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--need', default='')
    ap.add_argument('--template'); ap.add_argument('--fix', action='store_true'); a = ap.parse_args()
    if a.template:
        from template_probe import resolve_template
        a.template = resolve_template(a.template)
    need = {n.strip() for n in a.need.split(',') if n.strip()}
    bad = need - {'html', 'png', 'pptx', 'preview'}
    if bad: sys.exit(f'[FAIL] unknown --need value(s): {", ".join(sorted(bad))} (use html, png, pptx, preview)')

    v = sys.version_info
    row('OK' if v >= (3, 8) else 'FAIL', f'Python {v.major}.{v.minor}', 'html+png+pptx+preview', '', 'install Python 3.8+')
    if importlib.util.find_spec('PIL'):
        row('OK', 'Pillow', 'pptx')
    else:
        row('WARN', 'Pillow missing', 'pptx', 'template safe-area detection falls back to 680 px; crop.py unavailable',
            'pip install Pillow')

    ok, why = check_png(a.fix)
    row('OK' if ok else 'FAIL', 'playwright + Chromium screenshot', 'png', '' if ok else why,
        '' if ok else 'python3 scripts/doctor.py --fix   (or: pip install playwright && python3 -m playwright install chromium)')

    row('OK' if shutil.which('zip') else 'FAIL', 'zip', 'pptx', '', hint('preinstalled', 'apt-get install zip'))
    so = shutil.which('soffice') or shutil.which('libreoffice') or (
        '/Applications/LibreOffice.app/Contents/MacOS/soffice' if MAC and os.path.exists('/Applications/LibreOffice.app') else None)
    row('OK' if so else 'FAIL', 'LibreOffice', 'preview', '' if so else 'no visual QA of the PPTX; the PPTX itself still builds',
        '' if so else hint('brew install --cask libreoffice', 'apt-get install libreoffice-impress'))
    pd = shutil.which('pdftoppm')
    row('OK' if pd else 'FAIL', 'pdftoppm (poppler)', 'preview', '', '' if pd else hint('brew install poppler', 'apt-get install poppler-utils'))
    if MAC:
        row('OK', 'CJK font', 'preview', 'macOS ships PingFang SC')
    elif shutil.which('fc-list'):
        zh = subprocess.run(['fc-list', ':lang=zh', 'family'], capture_output=True, text=True).stdout.strip()
        row('OK' if zh else 'WARN', 'CJK font for preview render', 'preview', '' if zh else 'Chinese text renders as boxes in the preview',
            '' if zh else hint('n/a', 'apt-get install fonts-noto-cjk'))
    from template_probe import resolve_pptx_skill
    sk = resolve_pptx_skill()
    row('OK' if sk else 'WARN', 'Anthropic pptx skill (optional)', 'validate',
        sk or 'not found: built-in basic validation is used instead (package structure only, no schema check)')

    if a.template:
        t = a.template
        try:
            z = zipfile.ZipFile(t); z.read('ppt/presentation.xml')
            names = ' '.join(re.findall(r'(?:matchingName|<p:cSld name)="([^"]*)"',
                             ' '.join(z.read(n).decode('utf-8', 'ignore') for n in z.namelist()
                                      if re.match(r'ppt/slideLayouts/slideLayout\d+\.xml$', n)))).lower()
            ok = 'title only' in names or 'blank' in names or re.search(r'type="(titleOnly|blank)"', ' '.join(
                z.read(n).decode('utf-8', 'ignore')[:600] for n in z.namelist() if n.startswith('ppt/slideLayouts/slideLayout')))
            row('OK' if ok else 'WARN', f'template {os.path.basename(t)}', 'pptx',
                '' if ok else 'no "Title Only" / "Blank" layout found: pass --layout "<name>" to make_pptx.py')
        except FileNotFoundError:
            row('FAIL', f'template {t}', 'pptx', 'file not found')
        except (zipfile.BadZipFile, KeyError):
            row('FAIL', f'template {t}', 'pptx', 'not a .pptx (PowerPoint) file — .potx/.key/.pdf are not supported; save as .pptx')

    for level, item, affects, detail, fix in rows:
        print(f'[{level:4}] {item:38} affects: {affects:22} {detail}' + (f'\n         fix: {fix}' if fix and level != 'OK' else ''))
    caps = {'html': 'html' not in broken, 'png': 'png' not in broken and 'html' not in broken,
            'pptx': 'pptx' not in broken, 'preview': 'preview' not in broken and 'pptx' not in broken}
    print('[summary] ' + ' · '.join(f'{c} {"yes" if ok else "NO"}' for c, ok in caps.items()))
    missing = [c for c in need if not caps[c]]
    if missing:
        print(f'[FAIL] requested capability unavailable: {", ".join(sorted(missing))} — tell the user, offer the other outputs')
        sys.exit(1)

if __name__ == '__main__':
    main()
