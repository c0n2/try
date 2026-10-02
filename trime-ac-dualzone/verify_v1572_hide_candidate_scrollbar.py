#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
delegate = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateDelegate.kt'
adapter = root / 'app/src/main/java/com/osfans/trime/ime/candidates/compact/CompactCandidateViewAdapter.kt'

results = []

def check(label, ok):
    results.append((label, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}={label}")

check('COMPACT_CANDIDATE_DELEGATE_EXISTS', delegate.is_file())
check('COMPACT_CANDIDATE_ADAPTER_EXISTS', adapter.is_file())

d = delegate.read_text(encoding='utf-8') if delegate.is_file() else ''
a = adapter.read_text(encoding='utf-8') if adapter.is_file() else ''

# v1.5.7 / v1.5.7.1 behavior must remain intact.
check('HORIZONTAL_CANDIDATE_SCROLL_RETAINED', 'override fun canScrollHorizontally(): Boolean = true' in d)
check('CANDIDATE_NOWRAP_RETAINED', 'flexWrap = FlexWrap.NOWRAP' in d)
check('CANDIDATE_FLEX_SHRINK_ZERO_RETAINED', 'flexShrink = 0f' in a)
check('UNROLL_BUTTON_PATH_RETAINED', 'UnrollButtonStateMachine' in d and 'refreshUnrolled' in d)
check('NEW_CANDIDATE_RESET_RETAINED', 'scrollToPosition(0)' in d)

# v1.5.7.2 behavior: hide only the visual horizontal scrollbar.
check('HORIZONTAL_SCROLLBAR_EXPLICITLY_DISABLED', 'isHorizontalScrollBarEnabled = false' in d)

failed = [name for name, ok in results if not ok]
if failed:
    print('V1572_HIDE_CANDIDATE_SCROLLBAR_CONTRACT=FAIL:' + ','.join(failed))
    sys.exit(1)
print('V1572_HIDE_CANDIDATE_SCROLLBAR_CONTRACT=PASS')
