#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root
rel = 'app/src/main/java/com/osfans/trime/ime/core/AcCtrlVimShortcut.kt'
path = root / rel
text = path.read_text(encoding='utf-8')
old = '''internal fun isAcPlainCtrlMetaState(metaState: Int): Boolean {
    val normalized = KeyEvent.normalizeMetaState(metaState)
    if (normalized and KeyEvent.META_CTRL_ON == 0) return false
    val disallowed =
        KeyEvent.META_SHIFT_ON or
            KeyEvent.META_ALT_ON or
            KeyEvent.META_META_ON or
            KeyEvent.META_SYM_ON
    return normalized and disallowed == 0
}
'''
new = '''internal fun isAcPlainCtrlMetaState(metaState: Int): Boolean {
    val ctrlMask =
        KeyEvent.META_CTRL_ON or
            KeyEvent.META_CTRL_LEFT_ON or
            KeyEvent.META_CTRL_RIGHT_ON
    if (metaState and ctrlMask == 0) return false

    val disallowed =
        KeyEvent.META_SHIFT_ON or
            KeyEvent.META_SHIFT_LEFT_ON or
            KeyEvent.META_SHIFT_RIGHT_ON or
            KeyEvent.META_ALT_ON or
            KeyEvent.META_ALT_LEFT_ON or
            KeyEvent.META_ALT_RIGHT_ON or
            KeyEvent.META_META_ON or
            KeyEvent.META_META_LEFT_ON or
            KeyEvent.META_META_RIGHT_ON or
            KeyEvent.META_SYM_ON
    return metaState and disallowed == 0
}
'''
if text.count(old) != 1:
    raise SystemExit('expected exactly one v1.4 meta-state helper')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print('V14_META_BITMASK_FIX_APPLIED')
