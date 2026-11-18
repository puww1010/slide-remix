"""Render a slide-remix spec to SVG (HTML page). Icons are converted from the same slidekit
shapes the PPTX uses, so both outputs show identical icons."""
import html, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'vendor')); sys.path.insert(0, HERE)
import slidekit as sk
from spec_lib import hex_of

FONT = ('-apple-system, "Helvetica Neue", Helvetica, Arial, "PingFang SC", "Hiragino Sans GB", '
        '"Noto Sans CJK SC", "Microsoft YaHei", sans-serif')
CLOUD = ('M.24,.92 C.08,.92 0,.78 .05,.64 C-.02,.5 .08,.34 .22,.36 C.24,.16 .44,.06 .58,.18 '
         'C.7,.04 .9,.1 .9,.3 C1.02,.36 1.04,.58 .92,.66 C.98,.82 .86,.94 .72,.9 Z')

def _box(sp):
    o = re.search(r'<a:off x="(\d+)" y="(\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', sp)
    return [int(v) / 914400 * 100 for v in o.groups()]  # icons are built at 1 "inch" = 100 px

def icon_svg(kind, cx, cy, s, color, stroke_px=2.0):
    if kind == 'person':
        r = s * .22
        return (f'<circle cx="{cx:.1f}" cy="{cy - s * .22:.1f}" r="{r:.1f}" fill="{color}"/>'
                f'<path d="M{cx - s * .42:.1f},{cy + s * .45:.1f} a{s * .42:.1f},{s * .4:.1f} 0 0 1 {s * .84:.1f},0 z" fill="{color}"/>')
    xml = sk.icon(kind, cx / 100, cy / 100, s / 100, 'dk1', stroke_px)
    out = []
    for sp in re.findall(r'<p:sp>.*?</p:sp>', xml, re.S):
        x, y, w, h = _box(sp)
        fill = color if '<a:solidFill><a:schemeClr val="dk1">' in sp.split('<a:ln')[0] else 'none'
        lnm = re.search(r'<a:ln w="(\d+)"', sp)
        st = f' stroke="{color}" stroke-width="{int(lnm.group(1)) / 12700:.2f}" stroke-linecap="round" stroke-linejoin="round"' \
            if lnm and '<a:ln><a:noFill/>' not in sp else ''
        prst = re.search(r'prst="(\w+)"', sp)
        if prst and prst.group(1) in ('rect', 'roundRect'):
            rx = min(w, h) * .18 if prst.group(1) == 'roundRect' else 0
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}"{st}/>')
        elif prst and prst.group(1) == 'ellipse':
            out.append(f'<ellipse cx="{x + w / 2:.1f}" cy="{y + h / 2:.1f}" rx="{w / 2:.1f}" ry="{h / 2:.1f}" fill="{fill}"{st}/>')
        elif prst and prst.group(1) == 'cloud':
            d = re.sub(r'(-?[\d.]+),(-?[\d.]+)', lambda m: f'{x + float(m.group(1)) * w:.1f},{y + float(m.group(2)) * h:.1f}', CLOUD)
            out.append(f'<path d="{d}" fill="{fill}"{st}/>')
        else:
            d = ''
            for cmd, body in re.findall(r'<a:(moveTo|lnTo|cubicBezTo)>(.*?)</a:\1>', sp):
                pts = [(x + int(a) / 1000 * w, y + int(b) / 1000 * h) for a, b in re.findall(r'x="(-?\d+)" y="(-?\d+)"', body)]
                d += {'moveTo': 'M', 'lnTo': 'L', 'cubicBezTo': 'C'}[cmd] + ' '.join(f'{px:.1f},{py:.1f}' for px, py in pts) + ' '
            if '<a:close/>' in sp: d += 'Z'
            if d: out.append(f'<path d="{d}" fill="{fill}"{st}/>')
        t = re.search(r'<a:rPr[^>]*sz="(\d+)"[^>]*>.*?<a:t[^>]*>([^<]+)</a:t>', sp)
        if t:
            fs = int(t.group(1)) / 100 * 100 / 72
            out.append(f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + fs * .35:.1f}" text-anchor="middle" '
                       f'style="font-size:{fs:.1f}px;font-weight:700;fill:{color}">{html.escape(t.group(2))}</text>')
    return ''.join(out)

def render(P):
    out, markers = [], set()
    for p in P:
        k = p['k']
        if k == 'rect':
            d = ' stroke-dasharray="5 4"' if p['dash'] == 'dash' else (' stroke-dasharray="2 3"' if p['dash'] == 'dot' else '')
            st = f' stroke="{hex_of(p["stroke"])}" stroke-width="{p["sw"]}"' if p['stroke'] else ''
            out.append(f'<rect x="{p["x"]:.1f}" y="{p["y"]:.1f}" width="{p["w"]:.1f}" height="{p["h"]:.1f}" rx="{p["rx"]}" '
                       f'fill="{hex_of(p["fill"])}"{st}{d}/>')
        elif k == 'poly':
            c = hex_of(p['color']); mid = 'm' + c[1:]; markers.add((mid, c))
            pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p['pts'])
            m = (f' marker-start="url(#{mid})"' if p['head'] else '') + (f' marker-end="url(#{mid})"' if p['tail'] else '')
            d = ' stroke-dasharray="5 3"' if p['dash'] == 'dash' else (' stroke-dasharray="2 3"' if p['dash'] == 'dot' else '')
            out.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="{p["sw"]}" stroke-linejoin="round"{d}{m}/>')
        elif k == 'tri':
            pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p['pts'])
            out.append(f'<polygon points="{pts}" fill="{hex_of(p["color"])}"/>')
        elif k == 'num':
            fs = p['size'] - (1 if len(p['n']) > 1 else 0)
            out.append(f'<circle cx="{p["cx"]:.1f}" cy="{p["cy"]:.1f}" r="{p["r"]}" fill="{hex_of(p["color"])}"/>'
                       f'<text x="{p["cx"]:.1f}" y="{p["cy"] + fs * .36:.1f}" text-anchor="middle" '
                       f'style="font-size:{fs}px;font-weight:700;fill:#fff">{p["n"]}</text>')
        elif k == 'check':
            cx, cy, r = p['cx'], p['cy'], p['r']; f = r / 10
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{hex_of(("green", "base"))}"/>'
                       f'<path d="M{cx - 4.5 * f:.1f},{cy + .5 * f:.1f} L{cx - 1.2 * f:.1f},{cy + 3.8 * f:.1f} L{cx + 4.8 * f:.1f},{cy - 3 * f:.1f}" '
                       f'fill="none" stroke="#fff" stroke-width="{2.2 * f:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
        elif k == 'icon':
            out.append(icon_svg(p['kind'], p['cx'], p['cy'], p['s'], hex_of(p['color']), max(1.4, p['s'] / 20)))
        elif k == 'text':
            top = p['y']
            for runs, size, lh in p['lines']:
                base = top + lh / 2 + size * .35
                x, anc = (p['x'] + p['w'] / 2, 'middle') if p['align'] == 'c' else (p['x'], 'start')
                spans = ''.join(f'<tspan style="fill:{hex_of(c)};font-weight:{700 if b else 400}">{html.escape(t)}</tspan>'
                                for t, c, b in runs)
                out.append(f'<text x="{x:.1f}" y="{base:.1f}" text-anchor="{anc}" style="font-size:{size}px">{spans}</text>')
                top += lh
        elif k == 'bullets':
            top, s, c = p['y'], p['size'], hex_of(p['color'])
            for i, item in enumerate(p['items']):
                if i: top += p['gap']
                for j, ln in enumerate(item):
                    base = top + p['lh'] / 2 + s * .35
                    if j == 0:
                        out.append(f'<text x="{p["x"]:.1f}" y="{base:.1f}" style="font-size:{s}px;fill:{c}">•</text>')
                    out.append(f'<text x="{p["x"] + s * 1.6:.1f}" y="{base:.1f}" style="font-size:{s}px;fill:{c}">{html.escape(ln)}</text>')
                    top += p['lh']
        else:
            raise ValueError(k)
    defs = ''.join(f'<marker id="{i}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="8" markerHeight="8" '
                   f'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z" fill="{c}"/></marker>'
                   for i, c in sorted(markers))
    return defs, '\n  '.join(out)

def page_html(P, title, dy=0):
    defs, body = render(P)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>
  html, body {{ margin: 0; height: 100%; background: #F3F4F7; }}
  body {{ display: flex; align-items: center; justify-content: center; }}
  svg {{ width: min(100vw, calc(100vh * 16 / 9)); height: auto; background: #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,.08), 0 0 0 1px #E5E7EB; }}
  text {{ font-family: {FONT}; }}
</style>
</head>
<body>
<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <defs>{defs}</defs>
  <g transform="translate(0,{dy})">
  {body}
  </g>
</svg>
</body>
</html>
'''
