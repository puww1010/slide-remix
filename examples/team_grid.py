"""Example: card grid (team / roles / capabilities). Title + key-message pill + N cards in a 4-column grid
(rows and card height are computed from N). Names below are FICTIONAL — real org pages stay internal."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from spec_lib import *

TITLE = 'Example Product PM Team Structure & Roles'
TITLE_BOX = (58, 38, 620, 32)        # right edge = where the pill starts (collision limit)
SUBTITLE_TOP = 96

PILL_LABEL, PILL_VALUE = 'Leadership Alignment:', 'Alex (Platform) → Jordan'
CARDS = [  # (icon, name, area, bullets)
    ('deploy', 'Sam Rivera', 'Hardware & Licensing', ['Appliance lifecycle & supply chain alignment', 'Virtual appliance platforms',
                                                      'Subscription licensing & competitive pricing']),
    ('globe', 'Priya Nair', 'Core Networking & SASE', ['Core routing & VPN connectivity', 'Branch LAG, IPv6, multicast & switching',
                                                       'Seamless onboarding', 'Competitive analysis']),
    ('test', 'Lukas Weber', 'Supportability & Operations', ['Field diagnostic tools & escalation rate reduction',
                                                             'Telemetry & serviceability requirements', 'Upgrades & operational health']),
    ('cloud', 'Slot [TBD]', 'Branch and Multicloud', ['Developer ecosystem & third party integrations', 'Multi-cloud networking',
                                                      'Branch LAN & Wi-Fi']),
    ('building', 'Mei Chen', 'Sovereign & Compliance', ['High/Moderate compliance certifications', 'Sovereign deployments',
                                                        'Controller region expansion', 'Migration tooling']),
    ('chip', 'Omar Haddad', 'Observability & AIOps', ['Copilot experiences', 'AI-powered operations', 'Telemetry & observability UX',
                                                      'Incident analytics & event correlation']),
    ('shield_ok', 'Ana Souza', 'Branch Security', ['Advanced threat services', 'Virtual patching', 'Microsegmentation by user / app / device',
                                                    'Quantum-safe security']),
]

def build_spec():
    P = []
    # key-message pill, right-aligned to the grid
    px, py, pw, ph = 702, 44, 536, 40
    P += [R(px, py, pw, ph, fill=C('zone'), stroke=C('line'), rx=20, name='Pill'),
          ICON('people', px + 30, py + ph / 2, 24, C('blue')),
          T(px + 54, py + 9, pw - 64, [([(PILL_LABEL, C('ink'), False), ('   ' + PILL_VALUE, C('blue'), False)], 16.5, 22)],
            name='Pill text')]
    cols, x0, x1, y0, y1, gx, gy = 4, 43, 1238, 109, 620, 19, 19
    rows = math.ceil(len(CARDS) / cols)
    cw, ch = (x1 - x0 - (cols - 1) * gx) / cols, (y1 - y0 - (rows - 1) * gy) / rows
    for k, (ic, name, area, bl) in enumerate(CARDS):
        x, y = x0 + (k % cols) * (cw + gx), y0 + (k // cols) * (ch + gy)
        P += [R(x, y, cw, ch, fill=C('blue', 'fill'), stroke=C('line'), rx=8, name=f'Card {k+1}'),
              ICON(ic, x + 29, y + 33, 26, C('blue')),
              T(x + 51, y + 20, cw - 64, [line1(name, 17.5, C('ink'), True, 26)], name=f'Card {k+1} name'),
              T(x + 18, y + 59, cw - 32, [line1(area, 15, C('ink'), True, 22)], name=f'Card {k+1} area'),
              BULLETS(x + 18, y + 90, cw - 30, bl, 13.3, C('muted'), lh=18.5, gap=8, name=f'Card {k+1} bullets')]
    return P
