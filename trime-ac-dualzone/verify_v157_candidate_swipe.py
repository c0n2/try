#!/usr/bin/env python3
from pathlib import Path
import argparse
import re
import sys

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root

candidate = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateDelegate.kt'
theme = root / 'app/src/main/assets/shared/trime.yaml'

results = []
def check(label, ok):
    results.append((label, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}={label}")

ct = candidate.read_text(encoding='utf-8') if candidate.is_file() else ''
tt = theme.read_text(encoding='utf-8') if theme.is_file() else ''

# Candidate strip behavior: a single horizontal row that can actually scroll.
check('COMPACT_CANDIDATE_FILE_EXISTS', candidate.is_file())
check('HORIZONTAL_SCROLL_ENABLED', 'override fun canScrollHorizontally(): Boolean = true' in ct)
check('VERTICAL_SCROLL_STAYS_DISABLED', 'override fun canScrollVertically(): Boolean = false' in ct)
check('FLEX_WRAP_NOWRAP_IMPORTED', 'import com.google.android.flexbox.FlexWrap' in ct)
check('FLEX_WRAP_NOWRAP_SET', 'flexWrap = FlexWrap.NOWRAP' in ct)
check('UNROLL_BUTTON_PATH_PRESERVED', 'refreshUnrolled(cnt)' in ct)
check('CANDIDATE_CLICK_PRESERVED', 'selectCandidate(position, global = true)' in ct)
check('CANDIDATE_LONG_PRESS_PRESERVED', 'showCandidateActionMenu(position, items[position].text, view, global = true)' in ct)

# New candidate data should return to the head of the strip, avoiding a stale scrolled offset.
check('NEW_CANDIDATES_RESET_SCROLL', 'scrollToPosition(0)' in ct)

# Light theme: all secondary key symbols should be pure black for maximum readability.
light = ''
m = re.search(r'^  ac_ios_light:\n(?P<body>.*?)(?=^  [a-zA-Z0-9_]+:\n|\Z)', tt, re.M | re.S)
if m:
    light = m.group('body')
check('IOS_LIGHT_EXISTS', bool(light))
for key in [
    'key_symbol_color',
    'off_key_symbol_color',
    'on_key_symbol_color',
    'hilited_key_symbol_color',
    'hilited_off_key_symbol_color',
    'hilited_on_key_symbol_color',
]:
    check(f'IOS_LIGHT_{key.upper()}_PURE_BLACK', bool(re.search(rf'^    {re.escape(key)}:\s*0x000000\s*$', light, re.M)))

# Dark theme is intentionally unchanged by this readability tweak.
check('IOS_DARK_STILL_EXISTS', bool(re.search(r'^  ac_ios_dark:\n', tt, re.M)))

failed = [label for label, ok in results if not ok]
if failed:
    print('V157_CANDIDATE_SWIPE_CONTRACT=FAIL:' + ','.join(failed))
    sys.exit(1)
print('V157_CANDIDATE_SWIPE_CONTRACT=PASS')
