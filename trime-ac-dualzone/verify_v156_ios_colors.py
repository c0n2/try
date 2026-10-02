#!/usr/bin/env python3
from pathlib import Path
import argparse
import re
import sys

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root

theme = root / 'app/src/main/assets/shared/trime.yaml'
tongwen = root / 'app/src/main/assets/shared/tongwenfeng.trime.yaml'
text = theme.read_text(encoding='utf-8')

checks = []
def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(f"{'PASS' if ok else 'FAIL'}={label}")

# Original geometry must stay at the pinned-Trime values.
check('GEOMETRY_KEY_HEIGHT_UNCHANGED', bool(re.search(r'^  key_height:\s*44\s*$', text, re.M)))
check('GEOMETRY_KEY_WIDTH_UNCHANGED', bool(re.search(r'^  key_width:\s*10\.0\s*$', text, re.M)))
check('GEOMETRY_ROUND_CORNER_UNCHANGED', bool(re.search(r'^  round_corner:\s*8\s*$', text, re.M)))
check('GEOMETRY_HORIZONTAL_GAP_UNCHANGED', bool(re.search(r'^  horizontal_gap:\s*1\s*$', text, re.M)))
check('GEOMETRY_VERTICAL_GAP_UNCHANGED', bool(re.search(r'^  vertical_gap:\s*1\s*$', text, re.M)))

# v1.5.6 additions: two color schemes only.
check('IOS_LIGHT_EXISTS', bool(re.search(r'^  ac_ios_light:\s*$', text, re.M)))
check('IOS_DARK_EXISTS', bool(re.search(r'^  ac_ios_dark:\s*$', text, re.M)))

light_required = {
    'name': 'AC iOS Light',
    'keyboard_back_color': '0xd1d5db',
    'key_back_color': '0xffffff',
    'off_key_back_color': '0xaeb3bb',
    'key_text_color': '0x000000',
    'key_symbol_color': '0x3c3c43',
    'hilited_key_back_color': '0xb8bdc5',
    'back_color': '0xf2f2f7',
    'candidate_text_color': '0x000000',
    'hilited_candidate_back_color': '0xd1d1d6',
    'hilited_candidate_text_color': '0x000000',
}
dark_required = {
    'name': 'AC iOS Dark',
    'keyboard_back_color': '0x1c1c1e',
    'key_back_color': '0x3a3a3c',
    'off_key_back_color': '0x545458',
    'key_text_color': '0xffffff',
    'key_symbol_color': '0xd1d1d6',
    'hilited_key_back_color': '0x636366',
    'back_color': '0x1c1c1e',
    'candidate_text_color': '0xffffff',
    'hilited_candidate_back_color': '0x48484a',
    'hilited_candidate_text_color': '0xffffff',
}

def block(name):
    m = re.search(rf'^  {re.escape(name)}:\s*\n(?P<body>(?:    .*\n|\s*\n)*)', text, re.M)
    return m.group('body') if m else ''

def require_block(prefix, body, required):
    for key, value in required.items():
        if key == 'name':
            ok = bool(re.search(rf'^    name:\s*{re.escape(value)}\s*$', body, re.M))
        else:
            ok = bool(re.search(rf'^    {re.escape(key)}:\s*{re.escape(value)}\s*$', body, re.M))
        check(f'{prefix}_{key.upper()}', ok)

require_block('LIGHT', block('ac_ios_light'), light_required)
require_block('DARK', block('ac_ios_dark'), dark_required)

# No PNG/background-image theme dependency in this feature.
for scheme in ('ac_ios_light', 'ac_ios_dark'):
    b = block(scheme)
    check(f'{scheme.upper()}_NO_IMAGE_ASSET', '.png' not in b.lower() and 'background_folder' not in b)

# The forbidden upstream theme remains byte-addressable and outside this verifier's target.
check('TONGWENFENG_PRESENT', tongwen.is_file())

failed = [name for name, ok in checks if not ok]
if failed:
    print('V156_IOS_COLOR_CONTRACT=FAIL:' + ','.join(failed))
    sys.exit(1)
print('V156_IOS_COLOR_CONTRACT=PASS')
