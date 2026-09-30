#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--phase', choices=['tests', 'impl'], required=True)
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
    write('app/src/test/java/com/osfans/trime/ime/core/AcWeChatDiagnosticTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcWeChatDiagnosticTest : StringSpec({
    "diagnostic snapshot never contains editor text" {
        AcWeChatDiagSnapshot(
            event = "CTRL_A_BEFORE",
            icId = 123,
            extractedNull = false,
            startOffset = 7,
            selectionStart = 2,
            selectionEnd = 2,
            textLength = 42,
        ).render() shouldBe
            "event=CTRL_A_BEFORE ic=123 etNull=false startOffset=7 sel=2..2 textLen=42"
    }
})
''')
    print('V132_DIAG_TEST_APPLIED')
    raise SystemExit(0)

write('app/src/main/java/com/osfans/trime/ime/core/AcWeChatDiagnostic.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

internal data class AcWeChatDiagSnapshot(
    val event: String,
    val icId: Int,
    val extractedNull: Boolean,
    val startOffset: Int,
    val selectionStart: Int,
    val selectionEnd: Int,
    val textLength: Int,
) {
    fun render(): String =
        "event=$event ic=$icId etNull=$extractedNull startOffset=$startOffset " +
            "sel=$selectionStart..$selectionEnd textLen=$textLength"
}
''')

# Add a compact privacy-preserving logger: package-gated to WeChat, no actual text content.
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''    fun hookKeyboard(\n        code: Int,\n        mask: Int,\n    ): Boolean {\n        val ic = currentInputConnection ?: return false\n''',
    '''    private fun acWeChatDiag(\n        event: String,\n        ic: android.view.inputmethod.InputConnection? = currentInputConnection,\n    ) {\n        if (currentInputEditorInfo.packageName != "com.tencent.mm") return\n        val connection = ic ?: run {\n            android.util.Log.w("ACIME_DIAG", "event=$event ic=null")\n            return\n        }\n        val et = runCatching {\n            connection.getExtractedText(ExtractedTextRequest().apply { token = 0 }, 0)\n        }.getOrNull()\n        val snap =\n            AcWeChatDiagSnapshot(\n                event = event,\n                icId = System.identityHashCode(connection),\n                extractedNull = et == null,\n                startOffset = et?.startOffset ?: -1,\n                selectionStart = et?.selectionStart ?: -1,\n                selectionEnd = et?.selectionEnd ?: -1,\n                textLength = et?.text?.length ?: -1,\n            )\n        android.util.Log.w("ACIME_DIAG", snap.render())\n    }\n\n    fun hookKeyboard(\n        code: Int,\n        mask: Int,\n    ): Boolean {\n        val ic = currentInputConnection ?: return false\n''',
)

# Instrument Ctrl+A around all three existing paths.
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''            KeyEvent.KEYCODE_A -> {\n                // 全选。先走标准 Android 菜单动作；若编辑器未形成选区，再退回显式 setSelection。\n                if (!prefs.keyboard.hookCtrlA.getValue()) return false\n\n                // First emulate a real hardware Ctrl+A chord. Some editors (notably WeChat)\n''',
    '''            KeyEvent.KEYCODE_A -> {\n                // 全选。先走标准 Android 菜单动作；若编辑器未形成选区，再退回显式 setSelection。\n                if (!prefs.keyboard.hookCtrlA.getValue()) return false\n\n                acWeChatDiag("CTRL_A_BEFORE", ic)\n\n                // First emulate a real hardware Ctrl+A chord. Some editors (notably WeChat)\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''                val keyEventResult = sendDownUpKeyEvent(chord.keyCode, chord.metaState)\n\n                val standardResult = ic.performContextMenuAction(android.R.id.selectAll)\n''',
    '''                val keyEventResult = sendDownUpKeyEvent(chord.keyCode, chord.metaState)\n                if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n                    android.util.Log.w("ACIME_DIAG", "event=CTRL_A_KEYEVENT result=$keyEventResult")\n                }\n                acWeChatDiag("CTRL_A_AFTER_KEYEVENT", ic)\n\n                val standardResult = ic.performContextMenuAction(android.R.id.selectAll)\n                if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n                    android.util.Log.w("ACIME_DIAG", "event=CTRL_A_MENU result=$standardResult")\n                }\n                acWeChatDiag("CTRL_A_AFTER_MENU", ic)\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''                if (range != null && ic.setSelection(range.start, range.end)) return true\n\n                Timber.w(\n''',
    '''                if (range != null) {\n                    val setSelectionResult = ic.setSelection(range.start, range.end)\n                    if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n                        android.util.Log.w(\n                            "ACIME_DIAG",\n                            "event=CTRL_A_SET_SELECTION result=$setSelectionResult " +\n                                "range=${range.start}..${range.end}",\n                        )\n                    }\n                    acWeChatDiag("CTRL_A_AFTER_SET_SELECTION", ic)\n                    if (setSelectionResult) return true\n                }\n\n                Timber.w(\n''',
)

# Instrument Ctrl+V branch without logging clipboard content.
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''            KeyEvent.KEYCODE_V -> {\n                // 粘贴\n                if (prefs.keyboard.hookCtrlCV.getValue()) {\n                    val etr = ExtractedTextRequest()\n''',
    '''            KeyEvent.KEYCODE_V -> {\n                // 粘贴\n                if (prefs.keyboard.hookCtrlCV.getValue()) {\n                    acWeChatDiag("CTRL_V_BEFORE", ic)\n                    val etr = ExtractedTextRequest()\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''                    if (et == null) {\n                        Timber.d("hookKeyboard paste, et == null, try commitText")\n                        val clipboardText = clipboardManager.primaryClip?.getItemAt(0)?.coerceToText(this)\n                        if (ic.commitText(clipboardText, 1)) {\n                            return true\n                        }\n                    } else if (ic.performContextMenuAction(android.R.id.paste)) {\n                        return true\n                    }\n''',
    '''                    if (et == null) {\n                        Timber.d("hookKeyboard paste, et == null, try commitText")\n                        if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n                            android.util.Log.w("ACIME_DIAG", "event=CTRL_V_PATH path=commitText etNull=true")\n                        }\n                        val clipboardText = clipboardManager.primaryClip?.getItemAt(0)?.coerceToText(this)\n                        val commitResult = ic.commitText(clipboardText, 1)\n                        if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n                            android.util.Log.w("ACIME_DIAG", "event=CTRL_V_COMMIT result=$commitResult")\n                        }\n                        acWeChatDiag("CTRL_V_AFTER_COMMIT", ic)\n                        if (commitResult) {\n                            return true\n                        }\n                    } else {\n                        if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n                            android.util.Log.w("ACIME_DIAG", "event=CTRL_V_PATH path=contextMenuPaste etNull=false")\n                        }\n                        val pasteResult = ic.performContextMenuAction(android.R.id.paste)\n                        if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n                            android.util.Log.w("ACIME_DIAG", "event=CTRL_V_MENU result=$pasteResult")\n                        }\n                        acWeChatDiag("CTRL_V_AFTER_MENU", ic)\n                        if (pasteResult) return true\n                    }\n''',
)

# Instrument selection transitions, still no text.
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''        super.onUpdateSelection(\n            oldSelStart,\n            oldSelEnd,\n            newSelStart,\n            newSelEnd,\n            candidatesStart,\n            candidatesEnd,\n        )\n        cursorUpdateIndex += 1\n''',
    '''        super.onUpdateSelection(\n            oldSelStart,\n            oldSelEnd,\n            newSelStart,\n            newSelEnd,\n            candidatesStart,\n            candidatesEnd,\n        )\n        if (currentInputEditorInfo.packageName == "com.tencent.mm") {\n            android.util.Log.w(\n                "ACIME_DIAG",\n                "event=SELECTION_CALLBACK old=$oldSelStart..$oldSelEnd " +\n                    "new=$newSelStart..$newSelEnd comp=$candidatesStart..$candidatesEnd " +\n                    "ic=${System.identityHashCode(currentInputConnection)}",\n            )\n        }\n        cursorUpdateIndex += 1\n''',
)

print('V132_DIAG_IMPLEMENTATION_APPLIED')
