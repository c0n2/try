#!/usr/bin/env python3
from pathlib import Path
import argparse
import re
import sys

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--baseline-theme', type=Path, default=None,
               help='pre-v1.5.6 trime.yaml; geometry/style values must remain identical')
a = p.parse_args()
root = a.root

theme = root / 'app/src/main/assets/shared/trime.yaml'
tongwen = root / 'app/src/main/assets/shared/tongwenfeng.trime.yaml'
text = theme.read_text(encoding='utf-8')
baseline_text = a.baseline_theme.read_text(encoding='utf-8') if a.baseline_theme else None

checks = []
def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(f"{'PASS' if ok else 'FAIL'}={label}")

lines = text.splitlines()

# v1.5.6 is colors-only. Compare geometry to the actual AC baseline, not to
# upstream Trime defaults (AC already has deliberate geometry customizations).
def style_value(source: str, key: str):
    m = re.search(rf'^  {re.escape(key)}:[ \t]*(.*?)[ \t]*$', source, re.M)
    return m.group(1) if m else None

geometry_keys = [
    'key_height',
    'key_width',
    'round_corner',
    'horizontal_gap',
    'vertical_gap',
    'keyboard_height',
    'keyboard_height_land',
]
if baseline_text is not None:
    for key in geometry_keys:
        check(
            f'GEOMETRY_{key.upper()}_UNCHANGED',
            style_value(text, key) == style_value(baseline_text, key),
        )
else:
    # RED-only invocations can omit a baseline; still require geometry keys to exist.
    for key in geometry_keys:
        check(f'GEOMETRY_{key.upper()}_PRESENT', style_value(text, key) is not None)

# v1.5.6 additions: two color schemes only.
check('IOS_LIGHT_EXISTS', '  ac_ios_light:' in lines)
check('IOS_DARK_EXISTS', '  ac_ios_dark:' in lines)

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
    target = f'  {name}:'
    try:
        start = lines.index(target)
    except ValueError:
        return ''
    body = []
    for line in lines[start + 1:]:
        # Scheme children are indented four spaces. A blank line is part of block.
        if line == '' or line.startswith('    '):
            body.append(line)
            continue
        break
    return '\n'.join(body) + ('\n' if body else '')

def require_block(prefix, body, required):
    for key, value in required.items():
        ok = bool(re.search(
            rf'^    {re.escape(key)}:[ \t]*{re.escape(value)}[ \t]*$',
            body,
            re.M,
        ))
        check(f'{prefix}_{key.upper()}', ok)

require_block('LIGHT', block('ac_ios_light'), light_required)
require_block('DARK', block('ac_ios_dark'), dark_required)

# No PNG/background-image theme dependency in this feature.
for scheme in ('ac_ios_light', 'ac_ios_dark'):
    b = block(scheme)
    check(f'{scheme.upper()}_NO_IMAGE_ASSET', '.png' not in b.lower() and 'background_folder' not in b)

# Forbidden upstream theme remains untouched by the v1.5.6 implementation.
check('TONGWENFENG_PRESENT', tongwen.is_file())

failed = [name for name, ok in checks if not ok]
if failed:
    print('V156_IOS_COLOR_CONTRACT=FAIL:' + ','.join(failed))
    sys.exit(1)
print('V156_IOS_COLOR_CONTRACT=PASS')
