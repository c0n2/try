#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root

delegate = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateDelegate.kt'
text = delegate.read_text(encoding='utf-8')

old = '''        context.recyclerView(R.id.candidate_view) {\n            itemAnimator = null\n            isFocusable = false\n'''
new = '''        context.recyclerView(R.id.candidate_view) {\n            itemAnimator = null\n            isHorizontalScrollBarEnabled = false\n            isFocusable = false\n'''

count = text.count(old)
if count != 1:
    raise SystemExit(f'expected exactly one compact candidate RecyclerView init block, got {count}')
if 'isHorizontalScrollBarEnabled = false' in text:
    raise SystemExit('candidate horizontal scrollbar is already explicitly disabled')

delegate.write_text(text.replace(old, new, 1), encoding='utf-8')
print('V1572_HORIZONTAL_SCROLLBAR_DISABLED')
print('V1572_HORIZONTAL_SWIPE_PRESERVED')
