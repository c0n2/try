#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--phase', choices=['v14-meta', 'v15-post'], required=True)
a = p.parse_args()
root = a.root


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one target, got {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


if a.phase == 'v14-meta':
    path = root / 'app/src/main/java/com/osfans/trime/ime/core/AcCtrlVimShortcut.kt'
    text = path.read_text(encoding='utf-8')
    final = '''internal fun isAcPlainCtrlMetaState(metaState: Int): Boolean {
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
    if text.count(final) == 1:
        print('V14_META_BITMASK_ALREADY_FINAL')
        raise SystemExit(0)

    current = '''internal fun isAcPlainCtrlMetaState(metaState: Int): Boolean {
    if (metaState and KeyEvent.META_CTRL_ON == 0) return false
    val disallowed =
        KeyEvent.META_SHIFT_ON or
            KeyEvent.META_ALT_ON or
            KeyEvent.META_META_ON or
            KeyEvent.META_SYM_ON
    return metaState and disallowed == 0
}
'''
    legacy = '''internal fun isAcPlainCtrlMetaState(metaState: Int): Boolean {
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
    matches = [(name, old) for name, old in [('current', current), ('legacy', legacy)] if text.count(old) == 1]
    if len(matches) != 1:
        raise SystemExit(f'v1.4 meta helper state is ambiguous: {[name for name, _ in matches]}')
    name, old = matches[0]
    path.write_text(text.replace(old, final, 1), encoding='utf-8')
    print(f'V14_META_BITMASK_COMPAT_FIX_APPLIED_FROM={name}')
    raise SystemExit(0)

path = root / 'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt'
replace_exact(
    path,
    'inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS',
    'inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS',
)
print('V15_POST_IMPORT_COMPAT_FIX_APPLIED')
