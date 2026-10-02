#!/usr/bin/env python3
from pathlib import Path
import argparse
import re
import sys

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root

adapter = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateViewAdapter.kt'
delegate = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateDelegate.kt'

results = []
def check(label, ok):
    results.append((label, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}={label}")

at = adapter.read_text(encoding='utf-8') if adapter.is_file() else ''
dt = delegate.read_text(encoding='utf-8') if delegate.is_file() else ''

check('CANDIDATE_ADAPTER_EXISTS', adapter.is_file())
check('V157_NOWRAP_RETAINED', 'flexWrap = FlexWrap.NOWRAP' in dt)
check('V157_HORIZONTAL_SCROLL_RETAINED', 'override fun canScrollHorizontally(): Boolean = true' in dt)
check('CANDIDATE_MIN_WIDTH_PRESERVED', 'minWidth = this@CompactCandidateViewAdapter.layoutMinWidth' in at)
check('CANDIDATE_FLEX_GROW_PRESERVED', 'flexGrow = this@CompactCandidateViewAdapter.layoutFlexGrow' in at)

# With NOWRAP, FlexboxLayoutManager defaults each FlexItem to flexShrink=1f.
# That compresses overflowing candidate items back into one screen, clipping text and
# leaving no horizontal overflow for RecyclerView to scroll. The compact candidates
# must explicitly opt out of shrink so their measured widths can overflow horizontally.
bind = re.search(
    r'holder\.ui\.root\.updateLayoutParams<FlexboxLayoutManager\.LayoutParams>\s*\{(?P<body>.*?)\n\s*\}',
    at,
    re.S,
)
bind_body = bind.group('body') if bind else ''
check('CANDIDATE_BIND_LAYOUT_PARAMS_FOUND', bool(bind))
check('CANDIDATE_FLEX_SHRINK_DISABLED', bool(re.search(r'\bflexShrink\s*=\s*0f\b', bind_body)))

failed = [label for label, ok in results if not ok]
if failed:
    print('V1571_CANDIDATE_OVERFLOW_CONTRACT=FAIL:' + ','.join(failed))
    sys.exit(1)
print('V1571_CANDIDATE_OVERFLOW_CONTRACT=PASS')
