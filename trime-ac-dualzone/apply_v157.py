#!/usr/bin/env python3
from pathlib import Path
import argparse
import re

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root

candidate = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateDelegate.kt'
ct = candidate.read_text(encoding='utf-8')

old_import = 'import com.google.android.flexbox.FlexboxLayoutManager\n'
new_import = 'import com.google.android.flexbox.FlexWrap\nimport com.google.android.flexbox.FlexboxLayoutManager\n'
if ct.count(old_import) != 1:
    raise SystemExit(f'expected one FlexboxLayoutManager import, got {ct.count(old_import)}')
ct = ct.replace(old_import, new_import, 1)

old_manager = '''    val layoutManager by lazy {\n        object : FlexboxLayoutManager(context) {\n            override fun canScrollHorizontally(): Boolean = false\n\n            override fun canScrollVertically(): Boolean = false\n'''
new_manager = '''    val layoutManager by lazy {\n        object : FlexboxLayoutManager(context) {\n            init {\n                flexWrap = FlexWrap.NOWRAP\n            }\n\n            override fun canScrollHorizontally(): Boolean = true\n\n            override fun canScrollVertically(): Boolean = false\n'''
if ct.count(old_manager) != 1:
    raise SystemExit(f'expected one compact layout manager block, got {ct.count(old_manager)}')
ct = ct.replace(old_manager, new_manager, 1)

old_update = '''        adapter.updateLayoutParams(layoutMinWidth, layoutFlexGrow)\n        adapter.updateCandidates(candidates, total, highlighted)\n\n        // not sure why empty candidates won't trigger `FlexboxLayoutManager#onLayoutCompleted()`\n'''
new_update = '''        adapter.updateLayoutParams(layoutMinWidth, layoutFlexGrow)\n        adapter.updateCandidates(candidates, total, highlighted)\n        if (candidates.isNotEmpty()) {\n            view.scrollToPosition(0)\n        }\n\n        // not sure why empty candidates won't trigger `FlexboxLayoutManager#onLayoutCompleted()`\n'''
if ct.count(old_update) != 1:
    raise SystemExit(f'expected one candidate update block, got {ct.count(old_update)}')
ct = ct.replace(old_update, new_update, 1)
candidate.write_text(ct, encoding='utf-8')

theme = root / 'app/src/main/assets/shared/trime.yaml'
tt = theme.read_text(encoding='utf-8')
m = re.search(r'(^  ac_ios_light:\n)(?P<body>.*?)(?=^  ac_ios_dark:\n)', tt, re.M | re.S)
if not m:
    raise SystemExit('AC iOS Light section not found; apply v1.5.6 first')
body = m.group('body')
for key in ['key_symbol_color', 'off_key_symbol_color', 'on_key_symbol_color']:
    pattern = rf'(^    {re.escape(key)}:\s*)0x3c3c43(\s*$)'
    body2, n = re.subn(pattern, rf'\g<1>0x000000\2', body, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f'expected one gray {key} in AC iOS Light, got {n}')
    body = body2

# Pressed symbol states were already black in v1.5.6; assert rather than silently alter them.
for key in ['hilited_key_symbol_color', 'hilited_off_key_symbol_color', 'hilited_on_key_symbol_color']:
    if not re.search(rf'^    {re.escape(key)}:\s*0x000000\s*$', body, re.M):
        raise SystemExit(f'expected {key} already pure black in AC iOS Light')

tt = tt[:m.start('body')] + body + tt[m.end('body'):]
theme.write_text(tt, encoding='utf-8')

print('V157_HORIZONTAL_CANDIDATE_SWIPE_APPLIED')
print('V157_CANDIDATE_NOWRAP_APPLIED')
print('V157_NEW_CANDIDATES_RESET_TO_HEAD_APPLIED')
print('V157_IOS_LIGHT_SYMBOLS_PURE_BLACK_APPLIED')
