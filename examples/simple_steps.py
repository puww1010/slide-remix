"""Example: simple N-step flow (3–5 big stage cards + arrows + closing banner). Built from scratch by a first-time run of the skill.
Source: user-provided content (no screenshot). Added text: none.
Icons: person (identity subject only, per '图标极简')."""
from spec_lib import *   # make_html.py / make_pptx.py put scripts/ on sys.path

TITLE = '零信任访问三步走'
TITLE_BOX = (58, 38, 940, 32)
SUBTITLE_TOP = 84

STAGES = [('1. 识别身份', '用户与设备双重认证', 'purple', 'person'),
          ('2. 评估风险', '实时检查设备姿态与行为', 'orange', 'search'),
          ('3. 最小授权', '按应用粒度放行，持续验证', 'green', 'shield_ok')]
X0, X1 = 40, 1240

def build_spec():
    P = []
    zy, zh = 140, 330
    gap = 70
    w = (X1 - X0 - 2 * gap) / 3
    for i, (t, d, role, icon) in enumerate(STAGES):
        x = X0 + i * (w + gap)
        P += [R(x, zy, w, zh, fill=C(role, 'fill'), stroke=C(role, 'border'), sw=1.0, rx=10, name=f'Stage {i+1} zone'),
              R(x + 30, zy + 40, w - 60, zh - 80, fill=C('white'), stroke=C(role), sw=1.7, rx=8, name=f'Stage {i+1} card'),
              ICON(icon, x + w / 2, zy + 110, 48, C(role), name=f'Stage {i+1} icon'),
              T(x + 30, zy + 165, w - 60, [line1(t, 22, C('ink'), True, 30)], align='c', name=f'Stage {i+1} title'),
              T(x + 30, zy + 210, w - 60, [line1(d, 14, C('muted'), False, 20)], align='c', name=f'Stage {i+1} text')]
        if i < 2:
            ax = x + w + 10
            P.append(PL([(ax, zy + zh / 2), (ax + gap - 20, zy + zh / 2)], C('blue'), 2.5, tail=True, name=f'Arrow {i+1}'))
    # closing banner
    by = 520
    P += [R(X0, by, X1 - X0, 56, fill=C('orange', 'fill'), rx=6, name='Banner'),
          R(X0, by, 5, 56, fill=C('orange'), rx=0, name='Banner bar'),
          T(X0, by + 15, X1 - X0, [line1('每一次访问都要重新证明自己', 18, C('orange'), True, 26)], align='c', name='Banner text')]
    return P
