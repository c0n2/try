#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root

adapter = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateViewAdapter.kt'
text = adapter.read_text(encoding='utf-8')

old = '''        holder.ui.root.updateLayoutParams<FlexboxLayoutManager.LayoutParams> {\n            minWidth = this@CompactCandidateViewAdapter.layoutMinWidth\n            flexGrow = this@CompactCandidateViewAdapter.layoutFlexGrow\n        }\n'''
new = '''        holder.ui.root.updateLayoutParams<FlexboxLayoutManager.LayoutParams> {\n            minWidth = this@CompactCandidateViewAdapter.layoutMinWidth\n            flexGrow = this@CompactCandidateViewAdapter.layoutFlexGrow\n            flexShrink = 0f\n        }\n'''

count = text.count(old)
if count != 1:
    raise SystemExit(f'expected exactly one compact candidate layout bind block, got {count}')

adapter.write_text(text.replace(old, new, 1), encoding='utf-8')
print('V1571_CANDIDATE_FLEX_SHRINK_DISABLED')
print('V1571_HORIZONTAL_OVERFLOW_PRESERVED')
