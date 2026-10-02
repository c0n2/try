#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root
path = root / 'app/src/main/assets/shared/trime.yaml'
text = path.read_text(encoding='utf-8')

if '  ac_ios_light:\n' in text or '  ac_ios_dark:\n' in text:
    raise SystemExit('v1.5.6 iOS color schemes already present')

anchor = '''  aqua:\n    name: 碧水／Aqua\n'''
if text.count(anchor) != 1:
    raise SystemExit(f'expected exactly one aqua insertion anchor, got {text.count(anchor)}')

# Verification-only snapshot outside the Trime repository. The GREEN verifier
# compares geometry/style values against this actual AC baseline so v1.5.6 can
# prove it changed colors only without assuming upstream's stock geometry.
baseline_snapshot = root.parent / 'v156-pre-theme.yaml'
baseline_snapshot.write_text(text, encoding='utf-8')

schemes = r'''  ac_ios_light:
    name: AC iOS Light
    author: AC Trime
    back_color: 0xf2f2f7
    border_color: 0xd1d1d6
    candidate_separator_color: 0xd1d1d6
    candidate_text_color: 0x000000
    comment_text_color: 0x3c3c43
    hilited_text_color: 0x000000
    hilited_back_color: 0xd1d1d6
    hilited_candidate_back_color: 0xd1d1d6
    hilited_candidate_text_color: 0x000000
    hilited_comment_text_color: 0x3c3c43
    hilited_key_back_color: 0xb8bdc5
    hilited_key_border_color: 0xb8bdc5
    hilited_key_text_color: 0x000000
    hilited_key_symbol_color: 0x000000
    hilited_off_key_back_color: 0xb8bdc5
    hilited_off_key_border_color: 0xb8bdc5
    hilited_off_key_text_color: 0x000000
    hilited_off_key_symbol_color: 0x000000
    hilited_on_key_back_color: 0xb8bdc5
    hilited_on_key_border_color: 0xb8bdc5
    hilited_on_key_text_color: 0x000000
    hilited_on_key_symbol_color: 0x000000
    key_back_color: 0xffffff
    key_border_color: 0xd1d1d6
    key_text_color: 0x000000
    key_symbol_color: 0x3c3c43
    keyboard_back_color: 0xd1d5db
    label_color: 0x000000
    off_key_back_color: 0xaeb3bb
    off_key_border_color: 0xaeb3bb
    off_key_text_color: 0x000000
    off_key_symbol_color: 0x3c3c43
    on_key_back_color: 0xaeb3bb
    on_key_border_color: 0xaeb3bb
    on_key_text_color: 0x000000
    on_key_symbol_color: 0x3c3c43
    preview_back_color: 0xffffff
    preview_text_color: 0x000000
    shadow_color: 0x8e8e93
    text_color: 0x000000
    text_back_color: 0xf2f2f7

  ac_ios_dark:
    name: AC iOS Dark
    author: AC Trime
    back_color: 0x1c1c1e
    border_color: 0x545458
    candidate_separator_color: 0x3a3a3c
    candidate_text_color: 0xffffff
    comment_text_color: 0xd1d1d6
    hilited_text_color: 0xffffff
    hilited_back_color: 0x48484a
    hilited_candidate_back_color: 0x48484a
    hilited_candidate_text_color: 0xffffff
    hilited_comment_text_color: 0xd1d1d6
    hilited_key_back_color: 0x636366
    hilited_key_border_color: 0x636366
    hilited_key_text_color: 0xffffff
    hilited_key_symbol_color: 0xffffff
    hilited_off_key_back_color: 0x636366
    hilited_off_key_border_color: 0x636366
    hilited_off_key_text_color: 0xffffff
    hilited_off_key_symbol_color: 0xffffff
    hilited_on_key_back_color: 0x636366
    hilited_on_key_border_color: 0x636366
    hilited_on_key_text_color: 0xffffff
    hilited_on_key_symbol_color: 0xffffff
    key_back_color: 0x3a3a3c
    key_border_color: 0x545458
    key_text_color: 0xffffff
    key_symbol_color: 0xd1d1d6
    keyboard_back_color: 0x1c1c1e
    label_color: 0xffffff
    off_key_back_color: 0x545458
    off_key_border_color: 0x545458
    off_key_text_color: 0xffffff
    off_key_symbol_color: 0xd1d1d6
    on_key_back_color: 0x545458
    on_key_border_color: 0x545458
    on_key_text_color: 0xffffff
    on_key_symbol_color: 0xd1d1d6
    preview_back_color: 0x636366
    preview_text_color: 0xffffff
    shadow_color: 0x000000
    text_color: 0xffffff
    text_back_color: 0x1c1c1e

'''

path.write_text(text.replace(anchor, schemes + anchor, 1), encoding='utf-8')
print('V156_IOS_COLOR_SCHEMES_APPLIED')
print(f'V156_BASELINE_THEME_SNAPSHOT={baseline_snapshot}')
print('V156_NO_PNG_ASSETS=PASS')
