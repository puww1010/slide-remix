#!/usr/bin/env python3
"""spec.py -> single-file HTML (inline SVG, 1280x720) + PNG screenshot (2x).

usage: python3 make_html.py --spec page_spec.py --out out.html [--png out.png] [--source source_text.txt] [--no-install]
exit codes: 0 ok · 1 [FAIL] (spec / output problem, nothing usable) · 2 HTML written but PNG screenshot failed
"""
import argparse, importlib.util, os, shutil, subprocess, sys, tempfile, time, traceback
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec_lib as L
from render_svg import page_html

def fail(msg, code=1):
    print('[FAIL] ' + msg); sys.exit(code)

def load_spec(path):
    """Import a spec module; any problem becomes a one-line [FAIL] with a hint (no traceback)."""
    if not os.path.isfile(path):
        fail(f'spec file not found: {path} (pass the path of your page spec .py, e.g. examples/simple_steps.py)')
    try:
        s = importlib.util.spec_from_file_location('page_spec', path); m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
    except Exception as e:
        fail(f'spec {path} failed to import: {spec_error(e)}')
    if not hasattr(m, 'build_spec') or not hasattr(m, 'TITLE'):
        fail(f'spec {path} must define TITLE and build_spec() (see SKILL.md "spec API")')
    return m

def spec_error(e):
    """Short, actionable description of an exception raised inside a spec."""
    tb = traceback.extract_tb(e.__traceback__)
    where = next((f'{os.path.basename(f.filename)}:{f.lineno}' for f in reversed(tb) if 'spec_lib' not in f.filename), '')
    msg = f'{type(e).__name__}: {e}'
    if isinstance(e, AssertionError) and 'colour role' in str(e):
        msg += f' — use one of {", ".join(L.ROLES + L.NEUTRALS)}'
    elif isinstance(e, AssertionError) and 'ICON kind' in str(e):
        msg += f' — use one of {", ".join(L.ICON_KINDS)}'
    elif isinstance(e, KeyError):
        msg += ' — unknown colour variant? use base / fill / bg / border / dark'
    return f'{msg} (at {where})' if where else msg

def build_primitives(m, path):
    try:
        return m.build_spec()
    except Exception as e:
        fail(f'spec {path} build_spec() raised {spec_error(e)}')

def header(m):
    x, y, w, h = getattr(m, 'TITLE_BOX', (58, 38, 940, 32))
    size = getattr(m, 'TITLE_SIZE', 24)
    return [L.R(40, y - 4, 5, h + 16, fill=L.C('orange'), rx=1, name='Title bar'),
            L.T(x, y, w, [L.line1(m.TITLE, size, L.C('ink'), True, h)], name='Title')]

# ---------------- screenshot (also used by doctor.py) ----------------
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

def net_ok(timeout=4):
    """True if HTTPS works (respects HTTPS_PROXY). Used to skip installs quickly when offline."""
    import urllib.request
    try:
        urllib.request.urlopen('https://pypi.org/simple/pip/', timeout=timeout).read(64); return True
    except Exception:
        return False

def _run(cmd, timeout, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=max(1, timeout), **kw)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, '', f'timed out after {int(timeout)} s')
    except FileNotFoundError as e:
        return subprocess.CompletedProcess(cmd, 127, '', str(e))

def screenshot(html_path, png_path, install=True, budget=120):
    """Headless Chromium screenshot. Returns (ok, reason). Self-heals the usual sandbox gaps when install=True:
    missing playwright (pip), missing browser (playwright install), missing shared libraries (Linux: apt-get download,
    extracted locally, no root). Every step has a timeout; the whole thing stays inside `budget` seconds."""
    t0 = time.time(); left = lambda: budget - (time.time() - t0)
    online = None
    def can_install():
        nonlocal online
        if not install: return False
        if online is None: online = net_ok()
        return online
    if importlib.util.find_spec('playwright') is None:
        if not can_install():
            return False, 'python package "playwright" is not installed' + (' and the network is unreachable' if install else '')
        r = _run([sys.executable, '-m', 'pip', 'install', '-q', 'playwright', '--break-system-packages'], min(90, left()))
        if r.returncode or importlib.util.find_spec('playwright') is None:
            r = _run([sys.executable, '-m', 'pip', 'install', '-q', 'playwright'], min(90, left()))
        importlib.invalidate_caches()
        if importlib.util.find_spec('playwright') is None:
            return False, 'pip install playwright failed: ' + (r.stderr.strip().splitlines() or ['?'])[-1][:160]
    script = os.path.join(tempfile.gettempdir(), 'slide_remix_shot.py'); open(script, 'w').write(SHOT)
    env = dict(os.environ); libpath = os.path.join(LIBDIR, 'usr/lib/x86_64-linux-gnu')
    env['LD_LIBRARY_PATH'] = libpath + ':' + env.get('LD_LIBRARY_PATH', '')
    tried = set(); last = ''
    while left() > 5:
        r = _run([sys.executable, script, os.path.abspath(html_path), os.path.abspath(png_path)], min(60, left()), env=env)
        if r.returncode == 0 and os.path.exists(png_path): return True, ''
        err = (r.stdout or '') + (r.stderr or ''); last = err
        if r.returncode == 124: return False, 'Chromium did not finish within the time limit'
        if "Executable doesn't exist" in err or 'playwright install' in err:
            if 'browser' in tried or not can_install():
                return False, 'Chromium for playwright is not installed' + \
                       (' and the network is unreachable' if install and online is False else '')
            tried.add('browser')
            r2 = _run([sys.executable, '-m', 'playwright', 'install', 'chromium'], min(150, left()))
            if r2.returncode: return False, 'playwright install chromium failed: ' + ((r2.stderr or r2.stdout).strip().splitlines() or ['?'])[-1][:160]
            continue
        miss = [lib for lib in LIBPKG if f'{lib}: cannot open shared object file' in err]
        if miss:
            lib = miss[0]
            if lib in tried or not sys.platform.startswith('linux') or not shutil.which('apt-get') or not can_install():
                return False, f'system library {lib} is missing (Debian/Ubuntu: apt-get install {LIBPKG[lib]}, or run: python3 -m playwright install-deps)'
            tried.add(lib); d = tempfile.mkdtemp()
            _run(['apt-get', 'download', LIBPKG[lib]], min(60, left()), cwd=d)
            for f in os.listdir(d):
                if f.endswith('.deb'): _run(['dpkg', '-x', os.path.join(d, f), LIBDIR], 30)
            continue
        break
    tail = [l for l in last.strip().splitlines() if l.strip()]
    return False, ('screenshot failed: ' + tail[-1][:200]) if tail else 'screenshot time budget exhausted'

def text_check(spec_texts, source_path):
    if not os.path.isfile(source_path):
        print(f'[WARN] source text file not found: {source_path} — text check skipped'); return [], []
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
    ap.add_argument('--no-install', action='store_true', help='never try to install playwright / Chromium / libraries')
    ap.add_argument('--budget', type=int, default=120, help='max seconds for the PNG screenshot (incl. self-healing)')
    a = ap.parse_args()
    m = load_spec(a.spec)
    P = header(m) + build_primitives(m, a.spec)
    try:
        ymax = max((p.get('y', 0) + p.get('h', 0)) if p['k'] == 'rect' else 0 for p in P)
        dy = getattr(m, 'HTML_DY', max(0, min(18, round((720 - ymax - 34) / 2))))
        html = page_html(P, m.TITLE, dy)
    except Exception as e:
        fail(f'rendering {a.spec} failed: {spec_error(e)}')
    try:
        open(a.out, 'w', encoding='utf-8').write(html)
    except OSError as e:
        fail(f'cannot write {a.out}: {e.strerror}')
    print('[html]', a.out, f'(content bottom {ymax:.0f}px, shifted {dy}px)')
    code = 0
    if a.png:
        ok, why = screenshot(a.out, a.png, install=not a.no_install, budget=a.budget)
        if ok: print('[png]', a.png)
        else:
            print(f'[png] FAILED: {why}. HTML is fine: open it in a browser and screenshot, or run doctor.py --fix'); code = 2
    if a.source: text_check(L.all_text(P), a.source)
    sys.exit(code)

if __name__ == '__main__':
    main()
