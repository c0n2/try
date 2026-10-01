#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib
import re

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--phase', choices=['tests', 'impl'], required=True)
p.add_argument('--frost-chars', type=Path)
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
        raise SystemExit(f'{rel}: expected one replacement target, got {count}: {old[:180]!r}')
    write(rel, text.replace(old, new, 1))


if a.phase == 'tests':
    write('app/src/test/java/com/osfans/trime/ime/core/AcAddWordShortcutTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import android.view.KeyEvent
import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.maps.shouldContainExactly
import io.kotest.matchers.shouldBe

class AcAddWordShortcutTest : StringSpec({
    "Ctrl+P is handled only by the AC full keyboard schema" {
        resolveAcAddWordShortcut(
            KeyEvent.KEYCODE_P,
            KeyEvent.META_CTRL_ON,
            enabled = true,
            schemaId = AC_ADD_WORD_SCHEMA_ID,
        ) shouldBe true
        resolveAcAddWordShortcut(
            KeyEvent.KEYCODE_P,
            KeyEvent.META_CTRL_ON,
            enabled = true,
            schemaId = "luna_pinyin",
        ) shouldBe false
    }

    "left physical Ctrl is accepted while shifted Ctrl+P is not" {
        val leftCtrl = KeyEvent.META_CTRL_ON or KeyEvent.META_CTRL_LEFT_ON
        resolveAcAddWordShortcut(
            KeyEvent.KEYCODE_P,
            leftCtrl,
            enabled = true,
            schemaId = AC_ADD_WORD_SCHEMA_ID,
        ) shouldBe true
        resolveAcAddWordShortcut(
            KeyEvent.KEYCODE_P,
            KeyEvent.META_CTRL_ON or KeyEvent.META_SHIFT_ON,
            enabled = true,
            schemaId = AC_ADD_WORD_SCHEMA_ID,
        ) shouldBe false
    }

    "disabled Ctrl+P hook is not consumed" {
        resolveAcAddWordShortcut(
            KeyEvent.KEYCODE_P,
            KeyEvent.META_CTRL_ON,
            enabled = false,
            schemaId = AC_ADD_WORD_SCHEMA_ID,
        ) shouldBe false
    }

    "selected word accepts 2 to 32 Han characters and trims outer whitespace" {
        validateAcAddWordText("  搭档永在  ") shouldBe "搭档永在"
        validateAcAddWordText("搭") shouldBe null
        validateAcAddWordText("搭档!") shouldBe null
        validateAcAddWordText("汉".repeat(32)) shouldBe "汉".repeat(32)
        validateAcAddWordText("汉".repeat(33)) shouldBe null
    }

    "standard Wubi86 phrase rules generate expected codes" {
        val stems = mapOf(
            "搭" to "rawk",
            "档" to "sivg",
            "永" to "ynii",
            "在" to "dhfd",
            "自" to "thd",
            "己" to "nngn",
            "的" to "rqyy",
            "老" to "ftxb",
            "是" to "jghu",
        )
        encodeAcWubi86Word("搭档永在", stems::get) shouldBe "rsyd"
        encodeAcWubi86Word("自己的", stems::get) shouldBe "tnrq"
        encodeAcWubi86Word("老是", stems::get) shouldBe "ftjg"
    }

    "manual code is normalized and import line matches librime table format" {
        validateAcAddWordCode(" RASI ") shouldBe "rasi"
        validateAcAddWordCode("ra5i") shouldBe null
        buildAcUserDictImportLine("搭档", "rasi") shouldBe "搭档\trasi\t1\n"
    }

    "stem asset parser accepts one Unicode scalar plus one lowercase code" {
        parseAcWubi86StemLines(
            sequenceOf(
                "搭\trawk",
                "档\tsivg",
                "bad",
                "永\tYNII",
            ),
        ) shouldContainExactly mapOf("搭" to "rawk", "档" to "sivg")
    }
})
''')

    replace_once(
        'app/src/test/java/com/osfans/trime/data/prefs/AcKeyboardHookDefaultsTest.kt',
        '''        AcKeyboardHookDefaults.CTRL_Q shouldBe true\n        AcKeyboardHookDefaults.CTRL_LR shouldBe false\n''',
        '''        AcKeyboardHookDefaults.CTRL_Q shouldBe true\n        AcKeyboardHookDefaults.CTRL_P shouldBe true\n        AcKeyboardHookDefaults.CTRL_LR shouldBe false\n''',
    )
    print('V15_CTRL_P_ADD_WORD_TESTS_APPLIED')
    raise SystemExit(0)

if a.frost_chars is None or not a.frost_chars.is_file():
    raise SystemExit('--frost-chars is required for --phase impl')

raw = a.frost_chars.read_bytes()
raw_sha = hashlib.sha256(raw).hexdigest()
expected_raw_sha = 'c2adeceb8b670d6e33798517a432b479bf657df312eae6b2be88cc1a7eb0ad92'
if raw_sha != expected_raw_sha:
    raise SystemExit(f'Frost chars SHA mismatch: {raw_sha}')

# Build the compact runtime stem table from the pinned Frost Wubi chars table.
text = raw.decode('utf-8-sig')
header = False
body = False
stem_options = {}
for raw_line in text.splitlines():
    st = raw_line.strip()
    if not st or st.startswith('#'):
        continue
    if st == '---':
        header = True
        continue
    if st == '...' and header:
        body = True
        continue
    if header and not body:
        continue
    parts = raw_line.split('\t')
    if len(parts) < 4 or len(parts[0]) == 0:
        continue
    character = parts[0]
    stem = parts[3].strip()
    if re.fullmatch(r'[a-z]{1,4}', stem):
        stem_options.setdefault(character, set()).add(stem)

# Frost has exactly six characters with alternative historical stems.
# These choices were selected in Phase 1 by maximizing reproduction of
# Frost's own published word-code set (190067 / 190794 unique words).
preferred_multi = {
    '戈': 'agnt',
    '不': 'dhi',
    '上': 'hhgg',
    '民': 'nav',
    '为': 'ylyi',
    '我': 'trnt',
}
asset_lines = []
for ch in sorted(stem_options, key=lambda s: ord(s[0])):
    options = stem_options[ch]
    if len(options) == 1:
        stem = next(iter(options))
    else:
        stem = preferred_multi.get(ch)
        if stem is None or stem not in options:
            raise SystemExit(f'unresolved multi-stem character: {ch} {sorted(options)}')
    asset_lines.append(f'{ch}\t{stem}')
asset = '\n'.join(asset_lines) + '\n'
asset_bytes = asset.encode('utf-8')
if len(asset_lines) != 27529:
    raise SystemExit(f'unexpected stem count: {len(asset_lines)}')
asset_sha = hashlib.sha256(asset_bytes).hexdigest()
expected_asset_sha = '72c1fef8f31ffd5643391f3bc6c22c74f474218284fc5fcc2c688874aab2bf4b'
if asset_sha != expected_asset_sha:
    raise SystemExit(f'stem asset SHA mismatch: {asset_sha}')
write('app/src/main/assets/ac_wubi86_stems.tsv', asset)

write('app/src/main/java/com/osfans/trime/ime/core/AcAddWordShortcut.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.core

import android.content.res.AssetManager
import android.view.KeyEvent

internal const val AC_ADD_WORD_SCHEMA_ID = "ac_raincandy_wubi86"
internal const val AC_ADD_WORD_USER_DICT = "ac_raincandy_wubi86_user"

internal fun resolveAcAddWordShortcut(
    keyCode: Int,
    metaState: Int,
    enabled: Boolean,
    schemaId: String,
): Boolean =
    enabled &&
        schemaId == AC_ADD_WORD_SCHEMA_ID &&
        keyCode == KeyEvent.KEYCODE_P &&
        isAcPlainCtrlMetaState(metaState)

internal fun acUnicodeScalars(text: String): List<String> {
    val out = ArrayList<String>()
    var index = 0
    while (index < text.length) {
        val codePoint = Character.codePointAt(text, index)
        out += String(Character.toChars(codePoint))
        index += Character.charCount(codePoint)
    }
    return out
}

private fun isAcHanCodePoint(codePoint: Int): Boolean =
    codePoint == 0x3007 ||
        codePoint in 0x3400..0x4DBF ||
        codePoint in 0x4E00..0x9FFF ||
        codePoint in 0xF900..0xFAFF ||
        codePoint in 0x20000..0x2EBEF ||
        codePoint in 0x30000..0x323AF

internal fun validateAcAddWordText(text: String): String? {
    val normalized = text.trim()
    val scalars = acUnicodeScalars(normalized)
    if (scalars.size !in 2..32) return null
    if (scalars.any { scalar -> !isAcHanCodePoint(Character.codePointAt(scalar, 0)) }) return null
    return normalized
}

internal fun validateAcAddWordCode(code: String): String? {
    val normalized = code.trim().lowercase()
    return normalized.takeIf { it.matches(Regex("[a-z]{1,4}")) }
}

internal fun encodeAcWubi86Word(
    word: String,
    stemOf: (String) -> String?,
): String? {
    val chars = acUnicodeScalars(word)
    if (chars.size !in 2..32) return null
    val stems = chars.map { stemOf(it) ?: return null }
    return when (chars.size) {
        2 -> {
            if (stems[0].length < 2 || stems[1].length < 2) return null
            stems[0].take(2) + stems[1].take(2)
        }
        3 -> {
            if (stems[2].length < 2) return null
            stems[0].take(1) + stems[1].take(1) + stems[2].take(2)
        }
        else -> stems[0].take(1) + stems[1].take(1) + stems[2].take(1) + stems.last().take(1)
    }
}

internal fun buildAcUserDictImportLine(word: String, code: String): String =
    "$word\t$code\t1\n"

internal fun parseAcWubi86StemLines(lines: Sequence<String>): Map<String, String> {
    val map = HashMap<String, String>()
    lines.forEach { line ->
        val parts = line.split('\t')
        if (parts.size != 2) return@forEach
        val scalar = parts[0]
        val code = parts[1]
        if (acUnicodeScalars(scalar).size != 1) return@forEach
        if (!code.matches(Regex("[a-z]{1,4}"))) return@forEach
        map[scalar] = code
    }
    return map
}

internal class AcWubi86StemTable private constructor(
    private val stems: Map<String, String>,
) {
    fun stemOf(character: String): String? = stems[character]

    companion object {
        fun load(assets: AssetManager): AcWubi86StemTable {
            val stems =
                assets.open("ac_wubi86_stems.tsv").bufferedReader(Charsets.UTF_8).use { reader ->
                    parseAcWubi86StemLines(reader.lineSequence())
                }
            return AcWubi86StemTable(stems)
        }
    }
}
''')

replace_once(
    'app/src/main/java/com/osfans/trime/data/prefs/AcKeyboardHookDefaults.kt',
    '''    const val CTRL_Q = true\n}\n''',
    '''    const val CTRL_Q = true\n    const val CTRL_P = true\n}\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/data/prefs/AppPrefs.kt',
    '''            const val HOOK_CTRL_Q = "hook_ctrl_q"\n''',
    '''            const val HOOK_CTRL_Q = "hook_ctrl_q"\n            const val HOOK_CTRL_P = "hook_ctrl_p"\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/data/prefs/AppPrefs.kt',
    '''        val hookCtrlQ = switch(R.string.hook_ctrl_q, HOOK_CTRL_Q, AcKeyboardHookDefaults.CTRL_Q)\n''',
    '''        val hookCtrlQ = switch(R.string.hook_ctrl_q, HOOK_CTRL_Q, AcKeyboardHookDefaults.CTRL_Q)\n        val hookCtrlP = switch(R.string.hook_ctrl_p, HOOK_CTRL_P, AcKeyboardHookDefaults.CTRL_P)\n''',
)

for rel, old, new in [
    (
        'app/src/main/res/values/strings.xml',
        '''    <string name="hook_ctrl_q">Hook Ctrl+Q (Clipboard)</string>\n''',
        '''    <string name="hook_ctrl_q">Hook Ctrl+Q (Clipboard)</string>\n    <string name="hook_ctrl_p">Hook Ctrl+P (Add word)</string>\n    <string name="ac_add_word_title">Add Wubi word</string>\n    <string name="ac_add_word_text_hint">Word (2–32 Han characters)</string>\n    <string name="ac_add_word_code_hint">Wubi code (1–4 letters)</string>\n    <string name="ac_add_word_confirm">Add</string>\n    <string name="ac_add_word_success">Added: %1$s [%2$s]</string>\n    <string name="ac_add_word_invalid">Invalid word or Wubi code</string>\n    <string name="ac_add_word_failed">Failed to add word</string>\n''',
    ),
    (
        'app/src/main/res/values-zh-rCN/strings.xml',
        '''    <string name="hook_ctrl_q">拦截 Ctrl+Q（剪贴板）</string>\n''',
        '''    <string name="hook_ctrl_q">拦截 Ctrl+Q（剪贴板）</string>\n    <string name="hook_ctrl_p">拦截 Ctrl+P（加词）</string>\n    <string name="ac_add_word_title">添加五笔词</string>\n    <string name="ac_add_word_text_hint">词语（2–32 个汉字）</string>\n    <string name="ac_add_word_code_hint">五笔编码（1–4 个字母）</string>\n    <string name="ac_add_word_confirm">添加</string>\n    <string name="ac_add_word_success">已收录：%1$s [%2$s]</string>\n    <string name="ac_add_word_invalid">词语或五笔编码无效</string>\n    <string name="ac_add_word_failed">添加词语失败</string>\n''',
    ),
    (
        'app/src/main/res/values-zh-rTW/strings.xml',
        '''    <string name="hook_ctrl_q">攔截 Ctrl+Q（剪貼簿）</string>\n''',
        '''    <string name="hook_ctrl_q">攔截 Ctrl+Q（剪貼簿）</string>\n    <string name="hook_ctrl_p">攔截 Ctrl+P（加詞）</string>\n    <string name="ac_add_word_title">新增五筆詞</string>\n    <string name="ac_add_word_text_hint">詞語（2–32 個漢字）</string>\n    <string name="ac_add_word_code_hint">五筆編碼（1–4 個字母）</string>\n    <string name="ac_add_word_confirm">新增</string>\n    <string name="ac_add_word_success">已收錄：%1$s [%2$s]</string>\n    <string name="ac_add_word_invalid">詞語或五筆編碼無效</string>\n    <string name="ac_add_word_failed">新增詞語失敗</string>\n''',
    ),
]:
    replace_once(rel, old, new)

# Imports for the small add-word UI and user-dictionary importer.
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''import android.app.Dialog\n''',
    '''import android.app.AlertDialog\nimport android.app.Dialog\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''import android.widget.FrameLayout\n''',
    '''import android.widget.EditText\nimport android.widget.FrameLayout\nimport android.widget.LinearLayout\nimport android.widget.Toast\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''import com.osfans.trime.data.theme.ColorManager\n''',
    '''import com.osfans.trime.data.theme.ColorManager\nimport com.osfans.trime.data.userdict.UserDictManager\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''import kotlinx.coroutines.CoroutineScope\n''',
    '''import kotlinx.coroutines.CoroutineScope\nimport kotlinx.coroutines.Dispatchers\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''import kotlinx.coroutines.launch\n''',
    '''import kotlinx.coroutines.launch\nimport kotlinx.coroutines.withContext\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''    private val acHookedPhysicalKeyUps = mutableSetOf<Int>()\n''',
    '''    private val acHookedPhysicalKeyUps = mutableSetOf<Int>()\n    private val acWubi86StemTable by lazy { AcWubi86StemTable.load(assets) }\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''    /** 編輯操作 */\n    fun hookKeyboard(\n''',
    r'''    private fun importAcUserWord(word: String, code: String) {
        val payload = buildAcUserDictImportLine(word, code)
        lifecycleScope.launch(Dispatchers.IO) {
            val result =
                UserDictManager.importUserDict(
                    payload.byteInputStream(Charsets.UTF_8),
                    AC_ADD_WORD_USER_DICT,
                    "ac-add-word.txt",
                )
            withContext(Dispatchers.Main) {
                result.fold(
                    onSuccess = { count ->
                        if (count > 0) {
                            Toast.makeText(
                                this@TrimeInputMethodService,
                                getString(R.string.ac_add_word_success, word, code),
                                Toast.LENGTH_SHORT,
                            ).show()
                        } else {
                            Toast.makeText(
                                this@TrimeInputMethodService,
                                R.string.ac_add_word_failed,
                                Toast.LENGTH_SHORT,
                            ).show()
                        }
                    },
                    onFailure = {
                        Timber.e(it, "Ctrl+P add word failed")
                        Toast.makeText(
                            this@TrimeInputMethodService,
                            R.string.ac_add_word_failed,
                            Toast.LENGTH_SHORT,
                        ).show()
                    },
                )
            }
        }
    }

    private fun showAcAddWordDialog(initialWord: String = "") {
        val wordInput = EditText(this).apply {
            hint = getString(R.string.ac_add_word_text_hint)
            setSingleLine(true)
            setText(initialWord.trim())
        }
        val initialValidated = validateAcAddWordText(initialWord)
        val initialCode =
            initialValidated?.let { encodeAcWubi86Word(it, acWubi86StemTable::stemOf) }.orEmpty()
        val codeInput = EditText(this).apply {
            hint = getString(R.string.ac_add_word_code_hint)
            setSingleLine(true)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            setText(initialCode)
        }
        val pad = (20 * resources.displayMetrics.density).toInt()
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad / 2, pad, 0)
            addView(wordInput)
            addView(codeInput)
        }
        val dialog =
            AlertDialog.Builder(this)
                .setTitle(R.string.ac_add_word_title)
                .setView(content)
                .setPositiveButton(R.string.ac_add_word_confirm) { _, _ ->
                    val word = validateAcAddWordText(wordInput.text?.toString().orEmpty())
                    val code = validateAcAddWordCode(codeInput.text?.toString().orEmpty())
                    if (word == null || code == null) {
                        Toast.makeText(this, R.string.ac_add_word_invalid, Toast.LENGTH_SHORT).show()
                    } else {
                        importAcUserWord(word, code)
                    }
                }
                .setNegativeButton(android.R.string.cancel, null)
                .create()
        showDialog(dialog)
    }

    private fun handleAcAddWordShortcut(): Boolean {
        val selected = currentInputConnection?.getSelectedText(0)?.toString().orEmpty()
        val word = validateAcAddWordText(selected)
        if (word == null) {
            showAcAddWordDialog(selected)
            return true
        }
        val code = encodeAcWubi86Word(word, acWubi86StemTable::stemOf)
        if (code == null) {
            showAcAddWordDialog(word)
            return true
        }
        importAcUserWord(word, code)
        return true
    }

    /** 編輯操作 */
    fun hookKeyboard(
''',
)

# Ctrl+P enters before the legacy per-key Ctrl hook handling. v1.4's
# isAcPlainCtrlMetaState already supports physical left/right Ctrl bits.
replace_once(
    'app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt',
    '''        val ic = currentInputConnection ?: return false\n        // 没按下 Ctrl 键\n''',
    '''        val ic = currentInputConnection ?: return false\n\n        if (resolveAcAddWordShortcut(\n                code,\n                mask,\n                prefs.keyboard.hookCtrlP.getValue(),\n                rime.run { statusCached.schemaId },\n            )\n        ) {\n            return handleAcAddWordShortcut()\n        }\n\n        // 没按下 Ctrl 键\n''',
)

print('V15_CTRL_P_ADD_WORD_IMPLEMENTATION_APPLIED')
print(f'AC_WUBI86_STEM_ASSET_COUNT={len(asset_lines)}')
print(f'AC_WUBI86_STEM_ASSET_SHA256={asset_sha}')
