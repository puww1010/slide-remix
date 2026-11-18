"""slide-remix PPTX renderer — used as the --page module of vendor/build_slide.py.
Reads SLIDE_REMIX_SPEC (spec .py), SLIDE_REMIX_PROBE (probe.json), SLIDE_REMIX_TITLE (json: sz / box override)."""
import importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'vendor')); sys.path.insert(0, HERE)
from slidekit import *          # noqa: F401,F403  (same module instance build_slide uses)
import slidekit as sk
import spec_lib as L

TINTS = {'fill': '<a:lumMod val="7000"/><a:lumOff val="93000"/>', 'bg': '<a:lumMod val="10000"/><a:lumOff val="90000"/>',
         'border': '<a:lumMod val="40000"/><a:lumOff val="60000"/>', 'dark': '<a:lumMod val="50000"/>'}

def load(path):
    s = importlib.util.spec_from_file_location('page_spec', path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m

class Ctx:
    def __init__(self, probe):
        self.p = probe; c = probe['canvas']
        self.ppi, self.ptpx = c['px_per_in'], c['pt_per_px']
    def I(self, v): return v / self.ppi
    def PT(self, v): return round(v * self.ptpx, 2)
    def cs(self, c):
        role, var = c; r = self.p['colors'][role]
        if var == 'base': return r['scheme'], r.get('base', '')
        if role in ('line', 'zone', 'white'): return r['scheme'], r.get('base', '')
        return r['scheme'], TINTS[var]
    def fill(self, c):
        return None if c is None else sk.sf(*self.cs(c))
    def ln(self, c, w, dash=None, head=False, tail=False, cap=False):
        sch, m = self.cs(c)
        d = {'dash': '<a:prstDash val="dash"/>', 'dot': '<a:prstDash val="sysDot"/>'}.get(dash, '')
        h = '<a:headEnd type="triangle" w="med" len="med"/>' if head else ''
        t = '<a:tailEnd type="triangle" w="med" len="med"/>' if tail else ''
        cp = ' cap="rnd"' if cap else ''
        return f'<a:ln w="{int(self.PT(w) * 12700)}"{cp}>{sk.sf(sch, m)}{d}<a:round/>{h}{t}</a:ln>'
    def run(self, t, px, c, b):
        sch, m = self.cs(c)
        r = sk.run(t, self.PT(px), sch, b=b)
        return r.replace(f'<a:schemeClr val="{sch}"></a:schemeClr>', f'<a:schemeClr val="{sch}">{m}</a:schemeClr>') if m else r
    def recolor(self, xml, c):
        sch, m = self.cs(c)
        return xml.replace(f'<a:schemeClr val="{sch}"></a:schemeClr>', f'<a:schemeClr val="{sch}">{m}</a:schemeClr>') if m else xml

def conv(X, p):
    I, k = X.I, p['k']
    if k == 'rect':
        mn = max(min(p['w'], p['h']), 1)
        geom, av = ('roundRect', {'adj': min(50000, int(p['rx'] / mn * 100000))}) if p['rx'] > 1 else ('rect', None)
        return [sk.shape(p['name'], I(p['x']), I(p['y']), I(p['w']), I(p['h']), geom, fill=X.fill(p['fill']),
                         line=X.ln(p['stroke'], p['sw'], p['dash']) if p['stroke'] else None, av=av)]
    if k == 'poly':
        pts = [('M' if i == 0 else 'L', I(x), I(y)) for i, (x, y) in enumerate(p['pts'])]
        return [sk.pathabs(p['name'], pts, line=X.ln(p['color'], p['sw'], p['dash'], p['head'], p['tail']))]
    if k == 'tri':
        pts = [('M' if i == 0 else 'L', I(x), I(y)) for i, (x, y) in enumerate(p['pts'])]
        return [sk.pathabs(p['name'], pts, closed=True, fill=X.fill(p['color']))]
    if k == 'num':
        cx, cy, r = p['cx'], p['cy'], p['r']; fs = p['size'] - (1 if len(p['n']) > 1 else 0)
        return [sk.shape(f'Badge {p["n"]}', I(cx - r), I(cy - r), I(2 * r), I(2 * r), 'ellipse', fill=X.fill(p['color']),
                         paras=[sk.para([X.run(p['n'], fs, L.C('white'), True)], algn='ctr')], anchor='ctr')]
    if k == 'check':
        cx, cy, r = p['cx'], p['cy'], p['r']; f = r / 10
        tick = f'<a:ln w="{int(X.PT(2.2 * f) * 12700)}" cap="rnd">{sk.sf("lt1")}<a:round/></a:ln>'
        return [sk.group(p['name'], I(cx - r), I(cy - r), I(2 * r), I(2 * r), [
            sk.shape(p['name'] + ' circle', I(cx - r), I(cy - r), I(2 * r), I(2 * r), 'ellipse', fill=X.fill(L.C('green'))),
            sk.pathabs(p['name'] + ' tick', [('M', I(cx - 4.5 * f), I(cy + .5 * f)), ('L', I(cx - 1.2 * f), I(cy + 3.8 * f)),
                                              ('L', I(cx + 4.8 * f), I(cy - 3 * f))], line=tick)])]
    if k == 'icon':
        cx, cy, s = p['cx'], p['cy'], p['s']; col = p['color']
        if p['kind'] == 'person':
            return [sk.group(p['name'], I(cx - s * .42), I(cy - s * .44), I(s * .84), I(s * .9), [
                sk.shape('head', I(cx - s * .22), I(cy - s * .44), I(s * .44), I(s * .44), 'ellipse', fill=X.fill(col)),
                sk.pathabs('shoulders', [('M', I(cx - s * .42), I(cy + s * .45)),
                                         ('C', I(cx - s * .42), I(cy + s * .1), I(cx - s * .2), I(cy + s * .05), I(cx), I(cy + s * .05)),
                                         ('C', I(cx + s * .2), I(cy + s * .05), I(cx + s * .42), I(cy + s * .1), I(cx + s * .42), I(cy + s * .45))],
                           closed=True, fill=X.fill(col))])]
        sch, _ = X.cs(col)
        return [X.recolor(sk.icon(p['kind'], I(cx), I(cy), I(s), sch, X.PT(max(1.4, s / 20))), col)]
    if k == 'text':
        paras = []
        for runs, size, lh in p['lines']:
            pct = max(60, min(250, lh / (1.2 * size) * 100))
            paras.append(sk.para([X.run(t, size, c, b) for t, c, b in runs], algn='ctr' if p['align'] == 'c' else 'l', lnpct=round(pct)))
        h = sum(l[2] for l in p['lines'])
        slack = p['w'] * .06                      # PowerPoint fonts run a little wider than the browser's
        x = p['x'] - slack / 2 if p['align'] == 'c' else p['x']
        return [sk.text(p['name'], I(x), I(p['y']), I(p['w'] + slack), I(h), paras)]
    if k == 'bullets':
        s, ind = p['size'], p['size'] * 1.6
        pct = max(60, min(250, p['lh'] / (1.2 * s) * 100))
        paras = []
        for i, item in enumerate(p['items']):
            runs = '<a:br><a:rPr lang="en-US" dirty="0"/></a:br>'.join(X.run(ln, s, p['color'], False) for ln in item)
            sch, m = X.cs(p['color'])
            paras.append(f'<a:p><a:pPr marL="{sk.emu(I(ind))}" indent="{-sk.emu(I(ind))}"><a:lnSpc><a:spcPct val="{int(pct * 1000)}"/></a:lnSpc>'
                         f'<a:spcBef><a:spcPts val="{int(X.PT(p["gap"]) * 100) if i else 0}"/></a:spcBef>'
                         f'<a:buClr><a:schemeClr val="{sch}">{m}</a:schemeClr></a:buClr><a:buFont typeface="Arial"/><a:buChar char="•"/></a:pPr>{runs}</a:p>')
        h = sum(len(it) for it in p['items']) * p['lh'] + p['gap'] * (len(p['items']) - 1)
        return [sk.text(p['name'], I(p['x']), I(p['y']), I(p['w'] * 1.06), I(h), paras)]
    raise ValueError(k)

def build():
    probe = json.load(open(os.environ['SLIDE_REMIX_PROBE']))
    L.COLOR_WORDS.update({r: probe['colors'][r].get('word', L.COLOR_WORDS[r]) for r in L.ROLES if r in probe['colors']})
    m = load(os.environ['SLIDE_REMIX_SPEC'])
    X = Ctx(probe)
    tt = json.loads(os.environ.get('SLIDE_REMIX_TITLE', '{}'))
    if tt.get('box'):
        bx, by, bw, bh = tt['box']
        S = [sk.title_ph(m.TITLE, X.I(bx), X.I(by), X.I(bw), X.I(bh), sz=tt.get('sz'))]
    else:
        S = [sk.title_ph(m.TITLE, sz=tt.get('sz'))]
    for p in m.build_spec():
        S += conv(X, p)
    return S
