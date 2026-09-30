#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--phase', choices=['tests','impl'], required=True)
a = p.parse_args()
root = a.root


def read(rel):
    return (root / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_once(rel, old, new):
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{rel}: expected one replacement target, got {count}: {old[:160]!r}')
    write(rel, text.replace(old, new, 1))


if a.phase == 'tests':
    write('app/src/test/java/com/osfans/trime/ime/keyboard/AcCtrlSpacePolicyTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.keyboard

import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcCtrlSpacePolicyTest : StringSpec({
    "normal RainCandy toggles ascii without changing keyboard" {
        resolveAcCtrlSpaceAction("ac_raincandy_wubi86", false) shouldBe AcCtrlSpaceAction.TOGGLE_ASCII
        resolveAcCtrlSpaceAction("ac_raincandy_wubi86", true) shouldBe AcCtrlSpaceAction.TOGGLE_ASCII
    }

    "double-key RainCandy switches to ASCII QWERTY from Chinese" {
        resolveAcCtrlSpaceAction("ac_raincandy_wubi86_double", false) shouldBe
            AcCtrlSpaceAction.SWITCH_TO_ASCII_KEYBOARD
    }

    "double-key RainCandy returns to compact keyboard from ASCII" {
        resolveAcCtrlSpaceAction("ac_raincandy_wubi86_double", true) shouldBe
            AcCtrlSpaceAction.SWITCH_TO_DOUBLE_KEYBOARD
    }

    "other schemas are untouched" {
        resolveAcCtrlSpaceAction("luna_pinyin", false) shouldBe AcCtrlSpaceAction.NONE
    }
})
''')

    write('app/src/test/java/com/osfans/trime/ime/core/AcSelectAllFallbackTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcSelectAllFallbackTest : StringSpec({
    "fallback selects the entire extracted text using absolute offsets" {
        computeAcSelectAllFallbackRange(startOffset = 7, textLength = 5) shouldBe
            AcSelectionRange(7, 12)
    }

    "empty extracted text has no fallback range" {
        computeAcSelectAllFallbackRange(startOffset = 0, textLength = 0) shouldBe null
    }

    "invalid negative start offset has no fallback range" {
        computeAcSelectAllFallbackRange(startOffset = -1, textLength = 5) shouldBe null
    }
})
''')
    print('V13_REGRESSION_TESTS_APPLIED')
    raise SystemExit(0)

write('app/src/main/java/com/osfans/trime/ime/keyboard/AcCtrlSpacePolicy.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.keyboard

internal enum class AcCtrlSpaceAction {
    NONE,
    TOGGLE_ASCII,
    SWITCH_TO_ASCII_KEYBOARD,
    SWITCH_TO_DOUBLE_KEYBOARD,
}

internal fun resolveAcCtrlSpaceAction(
    schemaId: String,
    isAsciiMode: Boolean,
): AcCtrlSpaceAction =
    when (schemaId) {
        "ac_raincandy_wubi86" -> AcCtrlSpaceAction.TOGGLE_ASCII
        "ac_raincandy_wubi86_double" ->
            if (isAsciiMode) {
                AcCtrlSpaceAction.SWITCH_TO_DOUBLE_KEYBOARD
            } else {
                AcCtrlSpaceAction.SWITCH_TO_ASCII_KEYBOARD
            }
        else -> AcCtrlSpaceAction.NONE
    }
''')

write('app/src/main/java/com/osfans/trime/ime/core/AcSelectAllFallback.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

internal data class AcSelectionRange(
    val start: Int,
    val end: Int,
)

internal fun computeAcSelectAllFallbackRange(
    startOffset: Int,
    textLength: Int,
): AcSelectionRange? {
    if (startOffset < 0 || textLength <= 0) return null
    val end = startOffset.toLong() + textLength.toLong()
    if (end > Int.MAX_VALUE) return null
    return AcSelectionRange(startOffset, end.toInt())
}
''')

replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/CommonKeyboardActionListener.kt',
    '''            private fun handleDefaultKeyAction(action: KeyAction) {\n                val shouldHookShiftKey = when {\n''',
    '''            private fun handleAcCtrlSpace(): Boolean {\n                val status = rime.run { statusCached }\n                return when (resolveAcCtrlSpaceAction(status.schemaId, status.isAsciiMode)) {\n                    AcCtrlSpaceAction.NONE -> false\n\n                    AcCtrlSpaceAction.TOGGLE_ASCII -> {\n                        service.postRimeJob {\n                            if (statusCached.isComposing) commitComposition()\n                            setRuntimeOption("ascii_mode", !statusCached.isAsciiMode)\n                        }\n                        true\n                    }\n\n                    AcCtrlSpaceAction.SWITCH_TO_ASCII_KEYBOARD -> {\n                        keyboardWindow.switchKeyboard("ac_ascii_qwerty")\n                        true\n                    }\n\n                    AcCtrlSpaceAction.SWITCH_TO_DOUBLE_KEYBOARD -> {\n                        keyboardWindow.switchKeyboard("ac_raincandy_wubi86_double")\n                        true\n                    }\n                }\n            }\n\n            private fun handleDefaultKeyAction(action: KeyAction) {\n                val effectiveModifier =\n                    if (action.modifier == 0) KeyboardWindow.currentKeyboard.modifier else action.modifier\n\n                if (action.code == KeyEvent.KEYCODE_SPACE &&\n                    effectiveModifier and KeyEvent.META_CTRL_ON != 0 &&\n                    handleAcCtrlSpace()\n                ) {\n                    return\n                }\n\n                val shouldHookShiftKey = when {\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''            KeyEvent.KEYCODE_A -> {\n                // 全选\n                return if (prefs.keyboard.hookCtrlA.getValue()) {\n                    ic.performContextMenuAction(android.R.id.selectAll)\n                } else {\n                    false\n                }\n            }\n''',
    '''            KeyEvent.KEYCODE_A -> {\n                // 全选。先走标准 Android 菜单动作；若编辑器未形成选区，再退回显式 setSelection。\n                if (!prefs.keyboard.hookCtrlA.getValue()) return false\n\n                val standardResult = ic.performContextMenuAction(android.R.id.selectAll)\n                val etr = ExtractedTextRequest().apply { token = 0 }\n                val et = ic.getExtractedText(etr, 0)\n\n                if (et != null && et.selectionStart != et.selectionEnd) return true\n\n                val range = et?.let {\n                    computeAcSelectAllFallbackRange(it.startOffset, it.text?.length ?: 0)\n                }\n                if (range != null && ic.setSelection(range.start, range.end)) return true\n\n                Timber.w("hookKeyboard selectAll fallback fail")\n                return standardResult\n            }\n''',
)

print('V13_IMPLEMENTATION_APPLIED')
