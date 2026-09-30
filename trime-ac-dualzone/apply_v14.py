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
    write('app/src/test/java/com/osfans/trime/ime/core/AcCtrlVimShortcutTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import android.view.KeyEvent
import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcCtrlVimShortcutTest : StringSpec({
    val all = AcCtrlVimFlags(hjkl = true, bf = true, homeEnd = true, clipboard = true)

    "Ctrl+HJKL maps to Vim cursor movement" {
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_H, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.LEFT
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_J, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.DOWN
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_K, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.UP
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_L, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.RIGHT
    }

    "Ctrl+B/F maps to page movement" {
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_B, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.PAGE_UP
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_F, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.PAGE_DOWN
    }

    "Ctrl+0/E maps to home and end" {
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_0, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.HOME
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_E, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.END
    }

    "Ctrl+Q opens clipboard" {
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_Q, KeyEvent.META_CTRL_ON, all) shouldBe AcCtrlVimAction.CLIPBOARD
    }

    "physical left Ctrl metadata is accepted" {
        val meta = KeyEvent.META_CTRL_ON or KeyEvent.META_CTRL_LEFT_ON
        isAcPlainCtrlMetaState(meta) shouldBe true
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_H, meta, all) shouldBe AcCtrlVimAction.LEFT
    }

    "Ctrl with Shift is not treated as plain AC Ctrl" {
        val meta = KeyEvent.META_CTRL_ON or KeyEvent.META_SHIFT_ON
        isAcPlainCtrlMetaState(meta) shouldBe false
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_H, meta, all) shouldBe null
    }

    "individual groups can be disabled" {
        val none = AcCtrlVimFlags(hjkl = false, bf = false, homeEnd = false, clipboard = false)
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_H, KeyEvent.META_CTRL_ON, none) shouldBe null
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_B, KeyEvent.META_CTRL_ON, none) shouldBe null
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_0, KeyEvent.META_CTRL_ON, none) shouldBe null
        resolveAcCtrlVimAction(KeyEvent.KEYCODE_Q, KeyEvent.META_CTRL_ON, none) shouldBe null
    }
})
''')

    write('app/src/test/java/com/osfans/trime/data/prefs/AcKeyboardHookDefaultsTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.data.prefs

import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcKeyboardHookDefaultsTest : StringSpec({
    "AC editing hooks default on except Ctrl Left Right" {
        AcKeyboardHookDefaults.CTRL_A shouldBe true
        AcKeyboardHookDefaults.CTRL_CVX shouldBe true
        AcKeyboardHookDefaults.CTRL_ZY shouldBe true
        AcKeyboardHookDefaults.CTRL_HJKL shouldBe true
        AcKeyboardHookDefaults.CTRL_BF shouldBe true
        AcKeyboardHookDefaults.CTRL_0E shouldBe true
        AcKeyboardHookDefaults.CTRL_Q shouldBe true
        AcKeyboardHookDefaults.CTRL_LR shouldBe false
    }
})
''')
    print('V14_REGRESSION_TESTS_APPLIED')
    raise SystemExit(0)

write('app/src/main/java/com/osfans/trime/ime/core/AcCtrlVimShortcut.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import android.view.KeyEvent

internal data class AcCtrlVimFlags(
    val hjkl: Boolean,
    val bf: Boolean,
    val homeEnd: Boolean,
    val clipboard: Boolean,
)

internal enum class AcCtrlVimAction(val targetKeyCode: Int?) {
    LEFT(KeyEvent.KEYCODE_DPAD_LEFT),
    DOWN(KeyEvent.KEYCODE_DPAD_DOWN),
    UP(KeyEvent.KEYCODE_DPAD_UP),
    RIGHT(KeyEvent.KEYCODE_DPAD_RIGHT),
    PAGE_UP(KeyEvent.KEYCODE_PAGE_UP),
    PAGE_DOWN(KeyEvent.KEYCODE_PAGE_DOWN),
    HOME(KeyEvent.KEYCODE_MOVE_HOME),
    END(KeyEvent.KEYCODE_MOVE_END),
    CLIPBOARD(null),
}

internal fun isAcPlainCtrlMetaState(metaState: Int): Boolean {
    val normalized = KeyEvent.normalizeMetaState(metaState)
    if (normalized and KeyEvent.META_CTRL_ON == 0) return false
    val disallowed =
        KeyEvent.META_SHIFT_ON or
            KeyEvent.META_ALT_ON or
            KeyEvent.META_META_ON or
            KeyEvent.META_SYM_ON
    return normalized and disallowed == 0
}

internal fun resolveAcCtrlVimAction(
    keyCode: Int,
    metaState: Int,
    flags: AcCtrlVimFlags,
): AcCtrlVimAction? {
    if (!isAcPlainCtrlMetaState(metaState)) return null
    return when (keyCode) {
        KeyEvent.KEYCODE_H -> if (flags.hjkl) AcCtrlVimAction.LEFT else null
        KeyEvent.KEYCODE_J -> if (flags.hjkl) AcCtrlVimAction.DOWN else null
        KeyEvent.KEYCODE_K -> if (flags.hjkl) AcCtrlVimAction.UP else null
        KeyEvent.KEYCODE_L -> if (flags.hjkl) AcCtrlVimAction.RIGHT else null
        KeyEvent.KEYCODE_B -> if (flags.bf) AcCtrlVimAction.PAGE_UP else null
        KeyEvent.KEYCODE_F -> if (flags.bf) AcCtrlVimAction.PAGE_DOWN else null
        KeyEvent.KEYCODE_0 -> if (flags.homeEnd) AcCtrlVimAction.HOME else null
        KeyEvent.KEYCODE_E -> if (flags.homeEnd) AcCtrlVimAction.END else null
        KeyEvent.KEYCODE_Q -> if (flags.clipboard) AcCtrlVimAction.CLIPBOARD else null
        else -> null
    }
}
''')

write('app/src/main/java/com/osfans/trime/data/prefs/AcKeyboardHookDefaults.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.data.prefs

internal object AcKeyboardHookDefaults {
    const val CTRL_A = true
    const val CTRL_CVX = true
    const val CTRL_LR = false
    const val CTRL_ZY = true
    const val CTRL_HJKL = true
    const val CTRL_BF = true
    const val CTRL_0E = true
    const val CTRL_Q = true
}
''')

replace_once(
    'app/src/main/java/com/osfans/trime/data/prefs/AppPrefs.kt',
    '''            const val HOOK_CTRL_A = "hook_ctrl_a"\n            const val HOOK_CTRL_CV = "hook_ctrl_cv"\n            const val HOOK_CTRL_LR = "hook_ctrl_lr"\n            const val HOOK_CTRL_ZY = "hook_ctrl_zy"\n''',
    '''            const val HOOK_CTRL_A = "hook_ctrl_a"\n            const val HOOK_CTRL_CV = "hook_ctrl_cv"\n            const val HOOK_CTRL_LR = "hook_ctrl_lr"\n            const val HOOK_CTRL_ZY = "hook_ctrl_zy"\n            const val HOOK_CTRL_HJKL = "hook_ctrl_hjkl"\n            const val HOOK_CTRL_BF = "hook_ctrl_bf"\n            const val HOOK_CTRL_0E = "hook_ctrl_0e"\n            const val HOOK_CTRL_Q = "hook_ctrl_q"\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/data/prefs/AppPrefs.kt',
    '''        val hookCtrlA = switch(R.string.hook_ctrl_a, HOOK_CTRL_A, false)\n        val hookCtrlCV = switch(R.string.hook_ctrl_cv, HOOK_CTRL_CV, false)\n        val hookCtrlLR = switch(R.string.hook_ctrl_lr, HOOK_CTRL_LR, false)\n        val hookCtrlZY = switch(R.string.hook_ctrl_zy, HOOK_CTRL_ZY, false)\n''',
    '''        val hookCtrlA = switch(R.string.hook_ctrl_a, HOOK_CTRL_A, AcKeyboardHookDefaults.CTRL_A)\n        val hookCtrlCV = switch(R.string.hook_ctrl_cv, HOOK_CTRL_CV, AcKeyboardHookDefaults.CTRL_CVX)\n        val hookCtrlLR = switch(R.string.hook_ctrl_lr, HOOK_CTRL_LR, AcKeyboardHookDefaults.CTRL_LR)\n        val hookCtrlZY = switch(R.string.hook_ctrl_zy, HOOK_CTRL_ZY, AcKeyboardHookDefaults.CTRL_ZY)\n        val hookCtrlHJKL = switch(R.string.hook_ctrl_hjkl, HOOK_CTRL_HJKL, AcKeyboardHookDefaults.CTRL_HJKL)\n        val hookCtrlBF = switch(R.string.hook_ctrl_bf, HOOK_CTRL_BF, AcKeyboardHookDefaults.CTRL_BF)\n        val hookCtrl0E = switch(R.string.hook_ctrl_0e, HOOK_CTRL_0E, AcKeyboardHookDefaults.CTRL_0E)\n        val hookCtrlQ = switch(R.string.hook_ctrl_q, HOOK_CTRL_Q, AcKeyboardHookDefaults.CTRL_Q)\n''',
)

for rel, old, new in [
    (
        'app/src/main/res/values/strings.xml',
        '''    <string name="hook_ctrl_a">Hook Ctrl+A</string>\n    <string name="hook_ctrl_cv">Hook Ctrl+C/V/X</string>\n    <string name="hook_ctrl_lr">Hook Ctrl+Left/Right</string>\n    <string name="hook_ctrl_zy">Hook Ctrl+Z/Y</string>\n''',
        '''    <string name="hook_ctrl_a">Hook Ctrl+A</string>\n    <string name="hook_ctrl_cv">Hook Ctrl+C/V/X</string>\n    <string name="hook_ctrl_lr">Hook Ctrl+Left/Right</string>\n    <string name="hook_ctrl_zy">Hook Ctrl+Z/Y</string>\n    <string name="hook_ctrl_hjkl">Hook Ctrl+H/J/K/L (Vim cursor)</string>\n    <string name="hook_ctrl_bf">Hook Ctrl+B/F (Page Up/Down)</string>\n    <string name="hook_ctrl_0e">Hook Ctrl+0/E (Home/End)</string>\n    <string name="hook_ctrl_q">Hook Ctrl+Q (Clipboard)</string>\n''',
    ),
    (
        'app/src/main/res/values-zh-rCN/strings.xml',
        '''    <string name="hook_ctrl_a">拦截 Ctrl+A</string>\n    <string name="hook_ctrl_cv">拦截 Ctrl+C/V/X</string>\n    <string name="hook_ctrl_lr">拦截 Ctrl+Left/Right</string>\n    <string name="hook_ctrl_zy">拦截 Ctrl+Z/Y</string>\n''',
        '''    <string name="hook_ctrl_a">拦截 Ctrl+A</string>\n    <string name="hook_ctrl_cv">拦截 Ctrl+C/V/X</string>\n    <string name="hook_ctrl_lr">拦截 Ctrl+Left/Right</string>\n    <string name="hook_ctrl_zy">拦截 Ctrl+Z/Y</string>\n    <string name="hook_ctrl_hjkl">拦截 Ctrl+H/J/K/L（Vim 光标）</string>\n    <string name="hook_ctrl_bf">拦截 Ctrl+B/F（上/下翻页）</string>\n    <string name="hook_ctrl_0e">拦截 Ctrl+0/E（行首/行尾）</string>\n    <string name="hook_ctrl_q">拦截 Ctrl+Q（剪贴板）</string>\n''',
    ),
    (
        'app/src/main/res/values-zh-rTW/strings.xml',
        '''    <string name="hook_ctrl_a">攔截 Ctrl+A</string>\n    <string name="hook_ctrl_cv">攔截 Ctrl+C/V/X</string>\n    <string name="hook_ctrl_lr">攔截 Ctrl+Left/Right</string>\n    <string name="hook_ctrl_zy">攔截 Ctrl+Z/Y</string>\n''',
        '''    <string name="hook_ctrl_a">攔截 Ctrl+A</string>\n    <string name="hook_ctrl_cv">攔截 Ctrl+C/V/X</string>\n    <string name="hook_ctrl_lr">攔截 Ctrl+Left/Right</string>\n    <string name="hook_ctrl_zy">攔截 Ctrl+Z/Y</string>\n    <string name="hook_ctrl_hjkl">攔截 Ctrl+H/J/K/L（Vim 游標）</string>\n    <string name="hook_ctrl_bf">攔截 Ctrl+B/F（上/下翻頁）</string>\n    <string name="hook_ctrl_0e">攔截 Ctrl+0/E（行首/行尾）</string>\n    <string name="hook_ctrl_q">攔截 Ctrl+Q（剪貼簿）</string>\n''',
    ),
]:
    replace_once(rel, old, new)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/InputView.kt',
    '''import com.osfans.trime.ime.candidates.popup.PopupCandidatesMode\nimport com.osfans.trime.ime.composition.PreeditDelegate\n''',
    '''import com.osfans.trime.ime.candidates.popup.PopupCandidatesMode\nimport com.osfans.trime.ime.clipboard.ClipboardWindow\nimport com.osfans.trime.ime.composition.PreeditDelegate\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/InputView.kt',
    '''    fun refreshColors() {\n        keyboardBackground.imageDrawable = scope.drawable("keyboard_background")\n        popup.refreshColors()\n        keyboardWindow.refreshColors()\n        inputBar.refreshColors()\n        preedit.refreshColors()\n        windowManager.refreshColors()\n    }\n''',
    '''    fun refreshColors() {\n        keyboardBackground.imageDrawable = scope.drawable("keyboard_background")\n        popup.refreshColors()\n        keyboardWindow.refreshColors()\n        inputBar.refreshColors()\n        preedit.refreshColors()\n        windowManager.refreshColors()\n    }\n\n    fun showAcClipboardWindow() {\n        windowManager.attachWindow(ClipboardWindow(di))\n    }\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''    private var cursorUpdateIndex = 0\n''',
    '''    private var cursorUpdateIndex = 0\n    private val acHookedPhysicalKeyUps = mutableSetOf<Int>()\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''        // 没按下 Ctrl 键\n        if (mask != KeyEvent.META_CTRL_ON) {\n            return false\n        }\n''',
    '''        // Accept physical left/right Ctrl metadata too, but do not steal Ctrl+Shift/Alt/Meta chords.\n        if (!isAcPlainCtrlMetaState(mask)) {\n            return false\n        }\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {\n            if (prefs.keyboard.hookCtrlZY.getValue()) {\n                when (code) {\n                    KeyEvent.KEYCODE_Y -> return ic.performContextMenuAction(android.R.id.redo)\n                    KeyEvent.KEYCODE_Z -> return ic.performContextMenuAction(android.R.id.undo)\n                }\n            }\n        }\n\n        when (code) {\n''',
    '''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {\n            if (prefs.keyboard.hookCtrlZY.getValue()) {\n                when (code) {\n                    KeyEvent.KEYCODE_Y -> return ic.performContextMenuAction(android.R.id.redo)\n                    KeyEvent.KEYCODE_Z -> return ic.performContextMenuAction(android.R.id.undo)\n                }\n            }\n        }\n\n        resolveAcCtrlVimAction(\n            code,\n            mask,\n            AcCtrlVimFlags(\n                hjkl = prefs.keyboard.hookCtrlHJKL.getValue(),\n                bf = prefs.keyboard.hookCtrlBF.getValue(),\n                homeEnd = prefs.keyboard.hookCtrl0E.getValue(),\n                clipboard = prefs.keyboard.hookCtrlQ.getValue(),\n            ),\n        )?.let { action ->\n            if (action == AcCtrlVimAction.CLIPBOARD) {\n                if (inputView == null) return false\n                ContextCompat.getMainExecutor(this).execute {\n                    forceShowSelf()\n                    inputView?.showAcClipboardWindow()\n                }\n                return true\n            }\n            return sendDownUpKeyEvent(action.targetKeyCode!!)\n        }\n\n        when (code) {\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''        if (inputDeviceManager.evaluateOnKeyDown(event, this)) {\n            decorLocationUpdated = false\n            forceShowSelf()\n        }\n        return forwardKeyEvent(event) || super.onKeyDown(keyCode, event)\n    }\n\n    override fun onKeyUp(\n        keyCode: Int,\n        event: KeyEvent,\n    ): Boolean = forwardKeyEvent(event) || super.onKeyUp(keyCode, event)\n''',
    '''        if (inputDeviceManager.evaluateOnKeyDown(event, this)) {\n            decorLocationUpdated = false\n            forceShowSelf()\n        }\n        if (hookKeyboard(keyCode, event.metaState)) {\n            acHookedPhysicalKeyUps.add(keyCode)\n            return true\n        }\n        return forwardKeyEvent(event) || super.onKeyDown(keyCode, event)\n    }\n\n    override fun onKeyUp(\n        keyCode: Int,\n        event: KeyEvent,\n    ): Boolean {\n        if (acHookedPhysicalKeyUps.remove(keyCode)) return true\n        return forwardKeyEvent(event) || super.onKeyUp(keyCode, event)\n    }\n''',
)

print('V14_IMPLEMENTATION_APPLIED')
