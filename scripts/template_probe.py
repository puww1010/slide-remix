#!/usr/bin/env python3
"""Probe ANY .pptx template for slide-remix -> probe.json

  canvas      : width/height in inches, px->inch factor (spec canvas is 1280 px wide)
  colors      : semantic role -> theme scheme colour + lumMod/lumOff modifiers, chosen by hue;
                substitutions (e.g. no purple in the theme) and the Chinese colour word actually used
  layout      : best 'Title Only' (light) layout name, else 'Blank'
  title       : title placeholder box (px), insets, default size (pt), anchor
  safe_bottom : first decorated row from the bottom (footer band / logo / page number), from a render of the empty layout

usage: python3 template_probe.py Template.pptx [--layout NAME] [--out probe.json] [--no-render]
"""
import argparse, colorsys, glob, json, os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
EMU = 914400

ROLE_HUE = {'orange': 18, 'blue': 225, 'green': 140, 'purple': 265, 'teal': 182}
ROLE_ORDER = ('orange', 'blue', 'green', 'purple', 'teal')

def hue_word(h, l):
    if l < .2: return '深'
    for lo, hi, w in ((0, 10, '红'), (10, 45, '橙'), (45, 70, '黄'), (70, 165, '绿'), (165, 200, '青'),
                      (200, 250, '蓝'), (250, 290, '紫'), (290, 340, '粉'), (340, 361, '红')):
        if lo <= h < hi: return w
    return '灰'

def rel_lum(hexc):
    r, g, b = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)

def theme_colors(z):
    master = sorted(n for n in z.namelist() if re.match(r'ppt/slideMasters/slideMaster\d+\.xml$', n))[0]
    rels = z.read(master.replace('slideMasters/', 'slideMasters/_rels/') + '.rels').decode()
    theme = 'ppt/' + re.search(r'Target="\.\./(theme/theme\d+\.xml)"', rels).group(1)
    x = z.read(theme).decode()
    cs = re.search(r'<a:clrScheme.*?</a:clrScheme>', x, re.S).group(0)
    out = {}
    for k in ('dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6'):
        m = re.search(rf'<a:{k}>.*?(?:srgbClr val="([0-9A-Fa-f]{{6}})"|lastClr="([0-9A-Fa-f]{{6}})")', cs, re.S)
        out[k] = (m.group(1) or m.group(2)).upper() if m else '808080'
    return out, master

def map_colors(tc):
    acc = {}
    for k in ('accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6'):
        r, g, b = [int(tc[k][i:i + 2], 16) / 255 for i in (0, 2, 4)]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        acc[k] = dict(hex=tc[k], hue=h * 360, light=l, sat=s, lum=rel_lum(tc[k]))
    chromatic = [k for k, v in acc.items() if v['sat'] > .25 and .15 < v['light'] < .9]
    used, roles, notes = set(), {}, []
    for role in ROLE_ORDER:
        target = ROLE_HUE[role]
        dist = lambda k: min(abs(acc[k]['hue'] - target), 360 - abs(acc[k]['hue'] - target))
        hdist = lambda k1, k2: min(abs(acc[k1]['hue'] - acc[k2]['hue']), 360 - abs(acc[k1]['hue'] - acc[k2]['hue']))
        clash = lambda k: any(hdist(k, u) < 20 for u in used if u in acc)   # keep roles visually distinct
        cands = sorted(chromatic, key=lambda k: (k in used, clash(k), dist(k)))
        k = cands[0] if cands else 'dk2'
        used.add(k)
        if k == 'dk2':
            roles[role] = dict(scheme='dk2', base='', word='灰', hex=tc['dk2']); notes.append(f'{role}: no accent left -> dk2 (灰)'); continue
        a = acc[k]
        base = '<a:lumMod val="60000"/>' if a['lum'] > .55 else ('<a:lumMod val="75000"/>' if a['lum'] > .35 else '')
        word = hue_word(a['hue'], a['light'])
        roles[role] = dict(scheme=k, base=base, word=word, hex=a['hex'], hue_distance=round(dist(k)))
        if dist(k) > 25:
            notes.append(f'{role}: template has no close hue -> {k} #{a["hex"]} ({word}); legend words follow automatically')
    lt2_light = rel_lum(tc['lt2']) > .6
    neutrals = dict(
        ink=dict(scheme='dk1', base=''), muted=dict(scheme='dk2', base=''), soft=dict(scheme='dk2', base=''),
        white=dict(scheme='lt1', base=''), gray=dict(scheme='dk2', base='', word='灰'),
        line=dict(scheme='lt2', base='') if lt2_light else dict(scheme='dk2', base='<a:lumMod val="15000"/><a:lumOff val="85000"/>'),
        zone=dict(scheme='lt2', base='<a:lumMod val="50000"/><a:lumOff val="50000"/>') if lt2_light
        else dict(scheme='dk2', base='<a:lumMod val="5000"/><a:lumOff val="95000"/>'))
    roles.update(neutrals)
    return roles, notes

def layouts(z):
    out = []
    for n in sorted(z.namelist(), key=lambda s: int(re.findall(r'\d+', s)[-1]) if re.findall(r'\d+', s) else 0):
        if not re.match(r'ppt/slideLayouts/slideLayout\d+\.xml$', n): continue
        x = z.read(n).decode('utf-8', 'ignore')
        name = (re.search(r'matchingName="([^"]*)"', x) or re.search(r'<p:cSld name="([^"]*)"', x))
        typ = re.search(r'<p:sldLayout[^>]*\stype="(\w+)"', x)
        out.append(dict(part=n, name=name.group(1) if name else '', type=typ.group(1) if typ else '',
                        bg_dark=bool(re.search(r'<p:bg>.*?(dk1|000000|1[0-9A-F]{5})', x[:3000], re.S))))
    return out

def pick_layout(ls, want=None, family=''):
    if want:
        for l in ls:
            if l['name'] == want: return l
        sys.exit(f'layout "{want}" not found; available: ' + ', '.join(l['name'] for l in ls))
    def score(l):
        n = l['name'].lower(); s = 0
        if l['type'] == 'titleOnly' or 'title only' in n: s += 10
        elif l['type'] == 'blank' or 'blank' in n: s += 5
        else: return -1
        if 'light' in n: s += 3
        if 'dark' in n or l['bg_dark']: s -= 6
        if family and n.split()[:1] == [family]: s += 2
        return s
    best = max(ls, key=score)
    return best if score(best) > 0 else None

def slide1_family(z, ls):
    """First word of the layout used by the template's first slide (e.g. 'acme'), to prefer the main brand family."""
    try:
        pres = z.read('ppt/_rels/presentation.xml.rels').decode()
        s1 = 'ppt/' + re.search(r'Target="(slides/slide\d+\.xml)"', pres).group(1)
        rel = z.read(s1.replace('slides/', 'slides/_rels/') + '.rels').decode()
        part = 'ppt/' + re.search(r'Target="\.\./(slideLayouts/slideLayout\d+\.xml)"', rel).group(1)
        name = next(l['name'] for l in ls if l['part'] == part)
        return name.lower().split()[0] if name else ''
    except Exception:
        return ''

def title_info(z, layout_part, master_part, scale_px):
    x = z.read(layout_part).decode('utf-8', 'ignore'); m = z.read(master_part).decode('utf-8', 'ignore')
    def ph(xml):
        for sp in re.findall(r'<p:sp>.*?</p:sp>', xml, re.S):
            if re.search(r'<p:ph\b[^>]*type="(?:title|ctrTitle)"', sp): return sp
        return None
    lp, mp = ph(x), ph(m)
    src = lp if lp and '<a:off ' in lp else mp
    if not src: return None
    off = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"', src)
    box = [int(v) / EMU * scale_px for v in off.groups()]
    ins = {}
    for k, v in re.findall(r'\b([lrtb])Ins="(\d+)"', (lp or '') + (mp or '')):
        ins.setdefault(k, int(v) / EMU * scale_px)
    ins = {k: ins.get(k, .1 * scale_px if k in 'lr' else .05 * scale_px) for k in 'lrtb'}
    szs = re.findall(r'sz="(\d+)"', (lp or '') + (mp or '')) + re.findall(r'<p:titleStyle>.*?sz="(\d+)"', m, re.S)
    size = next((int(s) / 100 for s in szs if int(s) >= 1800), 32.0)
    anchor = re.search(r'anchor="(\w+)"', lp or mp or '')
    return dict(box_px=[round(v, 1) for v in box], ins_px={k: round(v, 1) for k, v in ins.items()},
                size_pt=size, anchor=anchor.group(1) if anchor else 't')

def safe_bottom(template, layout_name, workdir, h_px):
    """Render the empty layout and find where footer decoration starts (in spec px)."""
    page = os.path.join(workdir, 'probe_page.py')
    open(page, 'w').write("import sys\nsys.path.insert(0, %r)\nfrom slidekit import *\n"
                          "def build():\n    return [shape('probe', 0.01, 0.01, 0.01, 0.01)]\n" % os.path.join(HERE, 'vendor'))
    out = os.path.join(workdir, 'probe.pptx')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'vendor', 'build_slide.py'), '--template', template, '--page', page,
                        '--out', out, '--layout', layout_name, '--qa-dir', workdir], capture_output=True, text=True)
    jpgs = sorted(glob.glob(os.path.join(workdir, 'probe_stress*.jpg')))
    if not jpgs: return None, (r.stdout + r.stderr)[-800:]
    from PIL import Image
    im = Image.open(jpgs[0]).convert('L'); W, H = im.size; px = im.load()
    top_band = int(H * .55)
    first = None
    for y in range(top_band, H):
        dark = sum(1 for x in range(0, W, 4) if px[x, y] < 235)
        if dark > W / 4 * .004: first = y; break
    return (round(first / H * h_px, 1) if first else h_px), jpgs[0]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('template'); ap.add_argument('--layout'); ap.add_argument('--out')
    ap.add_argument('--no-render', action='store_true'); a = ap.parse_args()
    z = zipfile.ZipFile(a.template)
    pres = z.read('ppt/presentation.xml').decode()
    sz = re.search(r'<p:sldSz[^>]*>', pres).group(0)
    cx, cy = int(re.search(r'cx="(\d+)"', sz).group(1)), int(re.search(r'cy="(\d+)"', sz).group(1))
    w_in, h_in = cx / EMU, cy / EMU; scale_px = 1280 / w_in            # px per inch
    tc, master = theme_colors(z)
    roles, notes = map_colors(tc)
    ls = layouts(z); lay = pick_layout(ls, a.layout, slide1_family(z, ls))
    if not lay: sys.exit('no Title Only / Blank layout found; pass --layout. Available: ' + ', '.join(l['name'] for l in ls))
    probe = dict(template=os.path.abspath(a.template), canvas=dict(w_in=w_in, h_in=h_in, px_per_in=scale_px,
                 h_px=round(h_in * scale_px, 1), pt_per_px=round(w_in * 72 / 1280, 4)),
                 theme=tc, colors=roles, color_notes=notes, layout=lay['name'],
                 layouts=[l['name'] for l in ls], title=title_info(z, lay['part'], master, scale_px))
    if not a.no_render:
        wd = tempfile.mkdtemp(prefix='probe_')
        sb, info = safe_bottom(a.template, lay['name'], wd, probe['canvas']['h_px'])
        probe['safe_bottom_px'] = sb; probe['empty_layout_render'] = info
    out = a.out or os.path.splitext(a.template)[0] + '.probe.json'
    json.dump(probe, open(out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: probe[k] for k in ('canvas', 'layout', 'title', 'color_notes')}, ensure_ascii=False, indent=1))
    print('safe_bottom_px:', probe.get('safe_bottom_px'), '| roles:',
          {r: f"{v['scheme']}{'*' if v.get('base') else ''}" for r, v in roles.items() if r in ROLE_ORDER})
    print('[probe] ->', out)

if __name__ == '__main__':
    main()
