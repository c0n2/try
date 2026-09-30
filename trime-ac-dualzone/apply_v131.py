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
    write('app/src/test/java/com/osfans/trime/ime/core/AcSelectAllKeyEventTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import android.view.KeyEvent
import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcSelectAllKeyEventTest : StringSpec({
    "cold Ctrl+A dispatch uses a real Ctrl+A key chord" {
        acSelectAllKeyChord() shouldBe
            AcKeyChord(
                keyCode = KeyEvent.KEYCODE_A,
                metaState = KeyEvent.META_CTRL_ON,
            )
    }
})
''')
    print('V131_REGRESSION_TEST_APPLIED')
    raise SystemExit(0)

write('app/src/main/java/com/osfans/trime/ime/core/AcSelectAllKeyEvent.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import android.view.KeyEvent

internal data class AcKeyChord(
    val keyCode: Int,
    val metaState: Int,
)

internal fun acSelectAllKeyChord(): AcKeyChord =
    AcKeyChord(
        keyCode = KeyEvent.KEYCODE_A,
        metaState = KeyEvent.META_CTRL_ON,
    )
''')

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''                val standardResult = ic.performContextMenuAction(android.R.id.selectAll)\n                val etr = ExtractedTextRequest().apply { token = 0 }\n                val et = ic.getExtractedText(etr, 0)\n\n                if (et != null && et.selectionStart != et.selectionEnd) return true\n\n                val range = et?.let {\n                    computeAcSelectAllFallbackRange(it.startOffset, it.text?.length ?: 0)\n                }\n                if (range != null && ic.setSelection(range.start, range.end)) return true\n\n                Timber.w("hookKeyboard selectAll fallback fail")\n                return standardResult\n''',
    '''                // First emulate a real hardware Ctrl+A chord. Some editors (notably WeChat)\n                // ignore selectAll/setSelection until they have entered an active edit transaction,\n                // but may still handle a genuine key chord through InputConnection.sendKeyEvent().\n                val chord = acSelectAllKeyChord()\n                val keyEventResult = sendDownUpKeyEvent(chord.keyCode, chord.metaState)\n\n                val standardResult = ic.performContextMenuAction(android.R.id.selectAll)\n                val etr = ExtractedTextRequest().apply { token = 0 }\n                val et = ic.getExtractedText(etr, 0)\n\n                if (et != null && et.selectionStart != et.selectionEnd) return true\n\n                val range = et?.let {\n                    computeAcSelectAllFallbackRange(it.startOffset, it.text?.length ?: 0)\n                }\n                if (range != null && ic.setSelection(range.start, range.end)) return true\n\n                Timber.w(\n                    "hookKeyboard selectAll fallback fail; " +\n                        "keyEventResult=$keyEventResult standardResult=$standardResult",\n                )\n                return keyEventResult || standardResult\n''',
)

print('V131_IMPLEMENTATION_APPLIED')
