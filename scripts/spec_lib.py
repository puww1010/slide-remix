"""slide-remix spec library.

A page spec is a Python module that defines:
    TITLE            str   page title (HTML draws it; PPTX puts it in the template title placeholder)
    TITLE_BOX        (x, y, w, h) px — where the title may live; its right edge is the collision limit
    SUBTITLE_TOP     px — top of the first element under the title (PPTX moves the title if it would hit this)
    build_spec()     -> list of primitives (dicts) on a 1280 x 720 px canvas

Colours are semantic, never hex:
    neutrals : 'ink' 'muted' 'soft' 'white' 'line' 'zone'
    roles    : 'orange' (enforcement / safety / request entry)  'blue' (call / data path)
               'purple' (identity / context / memory)  'green' (pass / status / checks)
               'teal' (secondary phase)  'gray' (control plane / neutral node)
    variant  : C('blue') base · C('blue','fill') ~7 % tint · C('blue','border') ~40 % tint
               C('blue','dark') 50 % shade · C('green','bg') ~10 % tint
Legend text must use cw(role) ("orange" -> 橙 / mapped template colour word) so it stays true after template mapping.
"""
import math, re

W, H = 1280, 720
ROLES = ('orange', 'blue', 'purple', 'green', 'teal', 'gray')
NEUTRALS = ('ink', 'muted', 'soft', 'white', 'line', 'zone')

# colour words, overwritten by the PPTX renderer after template mapping
COLOR_WORDS = {'orange': '橙', 'blue': '蓝', 'purple': '紫', 'green': '绿', 'teal': '青绿', 'gray': '灰'}
def cw(role):
    return COLOR_WORDS[role]

def C(role, variant='base'):
    assert role in ROLES + NEUTRALS, f'unknown colour role {role!r}'
    return (role, variant)

# ---------- primitives ----------
def R(x, y, w, h, fill=None, stroke=None, sw=1.0, rx=8, dash=None, name='Box'):
    return dict(k='rect', x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw, rx=rx, dash=dash, name=name)

def T(x, y, w, lines, align='l', name='Text'):
    """lines: list of (runs, size_px, line_height_px); runs: list of (text, colour, bold). y = top of first line."""
    return dict(k='text', x=x, y=y, w=w, lines=lines, align=align, name=name)

def line1(t, size, color=C('ink'), bold=False, lh=None):
    return ([(t, color, bold)], size, lh or round(size * 1.35, 1))

def PL(pts, color, sw=2.0, head=False, tail=False, dash=None, name='Flow'):
    """Polyline in px. head/tail = arrowhead at first/last point. dash: 'dash' or 'dot'."""
    return dict(k='poly', pts=pts, color=color, sw=sw, head=head, tail=tail, dash=dash, name=name)

def TRI(cx, cy, color, s=5, name='Arrow'):
    """Small right-pointing filled triangle (step-to-step arrow in tight gaps)."""
    return dict(k='tri', pts=[(cx - s * .6, cy - s), (cx + s * .8, cy), (cx - s * .6, cy + s)], color=color, name=name)

def NUM(n, cx, cy, color, r=9, size=10.5):
    return dict(k='num', n=str(n), cx=cx, cy=cy, r=r, color=color, size=size)

def CHK(cx, cy, r=10, name='Check'):
    return dict(k='check', cx=cx, cy=cy, r=r, name=name)

def ICON(kind, cx, cy, s, color, name=None):
    """kind in ICON_KINDS. s = icon box size in px."""
    assert kind in ICON_KINDS, f'unknown ICON kind {kind!r}'
    return dict(k='icon', kind=kind, cx=cx, cy=cy, s=s, color=color, name=name or f'Icon {kind}')

ICON_KINDS = ('person', 'people', 'globe', 'cloud', 'shield_ok', 'chip', 'building', 'test', 'deploy',
              'terminal', 'search', 'clock', 'chat', 'book', 'target')

def LABEL(t, x, y_base, size, color, anchor='m', name='Label'):
    """Connector label with a white box behind it (SVG-halo look). Position like SVG text: x + anchor, baseline y."""
    w = est_w(t, size) + 10; h = size * 1.55
    x0 = {'m': x - w / 2, 's': x - 5, 'e': x - w + 5}[anchor]
    y0 = y_base - size * 1.12
    return [R(x0, y0, w, h, fill=C('white'), rx=0, name=name + ' bg'),
            T(x0, y0 + (h - size * 1.35) / 2, w, [line1(t, size, color, True)], align='c', name=name)]

def BULLETS(x, y, w, items, size, color=C('muted'), lh=None, gap=None, name='Bullets'):
    """Bulleted list; wrapping is decided HERE (same breaks in HTML and PPTX)."""
    lh = lh or round(size * 1.4, 1); gap = size * .6 if gap is None else gap
    return dict(k='bullets', x=x, y=y, w=w, size=size, color=color, lh=lh, gap=gap, name=name,
                items=[wrap(t, w - size * 1.6, size) for t in items])

# ---------- text measuring ----------
def is_cjk(ch):
    return ord(ch) >= 0x2E80
def est_w(t, size):
    """Rough rendered width in px (CJK = 1 em, Latin average 0.56 em, capitals/digits 0.64 em)."""
    w = 0
    for ch in t:
        if is_cjk(ch): w += 1.0
        elif ch == ' ': w += .28
        elif ch.isupper() or ch.isdigit(): w += .64
        else: w += .54
    return w * size

def wrap(t, max_w, size):
    """Greedy wrap: Latin breaks at spaces, CJK anywhere (never before closing punctuation)."""
    tokens = re.findall(r'[A-Za-z0-9\-‑/().,:;&+_\'"%@#!?]+\s*|\s+|.', t)
    lines, cur = [], ''
    for tok in tokens:
        cand = cur + tok
        if cur and est_w(cand.rstrip(), size) > max_w and not re.match(r'[，。、；：）」』！？,.;:)]', tok):
            lines.append(cur.rstrip()); cur = tok.lstrip()
        else:
            cur = cand
    if cur.strip(): lines.append(cur.rstrip())
    return lines

def all_text(P):
    """Every text item of a primitive list, lines of one block joined (used for the text check)."""
    out = []
    for p in P:
        if p['k'] == 'text':
            out.append(''.join(''.join(r[0] for r in runs) for runs, _, _ in p['lines']))
        elif p['k'] == 'bullets':
            out += [''.join(item) for item in p['items']]
        elif p['k'] == 'num':
            pass
    return out

# ---------- HTML-side colour resolution (design system of the reference slide) ----------
BASE_HEX = {'orange': '#E8542F', 'blue': '#4263EB', 'purple': '#7C5CE0', 'green': '#2E9E4F', 'teal': '#0F8B8D',
            'gray': '#4B5563', 'ink': '#1F2937', 'muted': '#4B5563', 'soft': '#6B7280', 'white': '#FFFFFF',
            'line': '#E5E7EB', 'zone': '#F3F4F6'}
def _mix(hexc, other, t):
    a = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (y - x) * t):02X}' for x, y in zip(a, b))
def hex_of(c):
    if c is None: return 'none'
    role, v = c
    base = BASE_HEX[role]
    return {'base': base, 'fill': _mix(base, '#FFFFFF', .93), 'bg': _mix(base, '#FFFFFF', .90),
            'border': _mix(base, '#FFFFFF', .60), 'dark': _mix(base, '#000000', .45)}[v]
