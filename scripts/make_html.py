#!/usr/bin/env python3
"""spec.py -> single-file HTML (inline SVG, 1280x720) + PNG screenshot (2x).

usage: python3 make_html.py --spec page_spec.py --out out.html [--png out.png] [--source source_text.txt]
"""
import argparse, importlib.util, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_lib as L
from render_svg import page_html

def load_spec(path):
    s = importlib.util.spec_from_file_location('page_spec', path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m

def header(m):
    x, y, w, h = getattr(m, 'TITLE_BOX', (58, 38, 940, 32))
    size = getattr(m, 'TITLE_SIZE', 24)
    return [L.R(40, y - 4, 5, h + 16, fill=L.C('orange'), rx=1, name='Title bar'),
            L.T(x, y, w, [L.line1(m.TITLE, size, L.C('ink'), True, h)], name='Title')]

SHOT = r'''
import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 720}, device_scale_factor=2)
    pg.goto('file://' + sys.argv[1]); pg.wait_for_timeout(400)
    pg.locator('svg').screenshot(path=sys.argv[2]); b.close()
'''
LIBPKG = {'libXdamage.so.1': 'libxdamage1', 'libXcomposite.so.1': 'libxcomposite1', 'libXrandr.so.2': 'libxrandr2',
          'libgbm.so.1': 'libgbm1', 'libxkbcommon.so.0': 'libxkbcommon0', 'libasound.so.2': 'libasound2',
          'libatk-1.0.so.0': 'libatk1.0-0', 'libatk-bridge-2.0.so.0': 'libatk-bridge2.0-0', 'libcups.so.2': 'libcups2',
          'libnss3.so': 'libnss3', 'libnspr4.so': 'libnspr4', 'libXfixes.so.3': 'libxfixes3', 'libdrm.so.2': 'libdrm2',
          'libatspi.so.0': 'libatspi2.0-0', 'libwayland-server.so.0': 'libwayland-server0'}
LIBDIR = '/tmp/slide-remix-libs'

def screenshot(html_path, png_path):
    """Headless Chromium screenshot. Self-heals the usual sandbox gaps: missing playwright, missing
    browser, missing shared libraries (downloaded with apt-get download, extracted locally, no root)."""
    try:
        import playwright  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'playwright', '--break-system-packages'], check=False)
    script = os.path.join(tempfile.gettempdir(), 'slide_remix_shot.py'); open(script, 'w').write(SHOT)
    env = dict(os.environ); libpath = os.path.join(LIBDIR, 'usr/lib/x86_64-linux-gnu')
    env['LD_LIBRARY_PATH'] = libpath + ':' + env.get('LD_LIBRARY_PATH', '')
    for _ in range(8):
        r = subprocess.run([sys.executable, script, os.path.abspath(html_path), os.path.abspath(png_path)],
                           capture_output=True, text=True, env=env)
        if r.returncode == 0: return True
        err = r.stdout + r.stderr
        if "Executable doesn't exist" in err or 'playwright install' in err:
            subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], capture_output=True); continue
        miss = [lib for lib in LIBPKG if f'{lib}: cannot open shared object file' in err]
        if miss:
            d = tempfile.mkdtemp()
            subprocess.run(['apt-get', 'download', LIBPKG[miss[0]]], cwd=d, capture_output=True)
            for f in os.listdir(d):
                if f.endswith('.deb'): subprocess.run(['dpkg', '-x', os.path.join(d, f), LIBDIR])
            continue
        print('[shot] failed:\n' + err[-1500:]); return False
    return False

def text_check(spec_texts, source_path):
    norm = lambda s: ''.join(s.replace('‑', '-').split())
    src = [l.strip() for l in open(source_path, encoding='utf-8') if l.strip() and not l.startswith('#')]
    blob_spec = norm(''.join(spec_texts)); blob_src = norm(''.join(src))
    missing = [s for s in src if norm(s) not in blob_spec]
    import re
    added = [t for t in spec_texts if norm(t) and not re.fullmatch(r'[\W\d_]+', norm(t)) and norm(t) not in blob_src]
    print('[text check] missing from page:', missing or 'none')
    print('[text check] on page but not in source (report these as added text):', added or 'none')
    return missing, added

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--png'); ap.add_argument('--source', help='source text list, one item per line')
    a = ap.parse_args()
    m = load_spec(a.spec)
    P = header(m) + m.build_spec()
    ymax = max((p.get('y', 0) + p.get('h', 0)) if p['k'] == 'rect' else 0 for p in P)
    dy = getattr(m, 'HTML_DY', max(0, min(18, round((720 - ymax - 34) / 2))))
    open(a.out, 'w', encoding='utf-8').write(page_html(P, m.TITLE, dy))
    print('[html]', a.out, f'(content bottom {ymax:.0f}px, shifted {dy}px)')
    if a.png:
        print('[png]', a.png if screenshot(a.out, a.png) else 'FAILED')
    if a.source: text_check(L.all_text(P), a.source)

if __name__ == '__main__':
    main()
