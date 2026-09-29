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
        raise SystemExit(f'{rel}: expected one replacement target, got {count}: {old[:100]!r}')
    write(rel, text.replace(old, new, 1))

if a.phase == 'tests':
    write('app/src/test/java/com/osfans/trime/ime/keyboard/AcDualZoneTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.keyboard

import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcDualZoneTest : StringSpec({
    "left half resolves LEFT" {
        resolveAcDualZoneSide(0f, 100) shouldBe AcDualZoneSide.LEFT
        resolveAcDualZoneSide(49.999f, 100) shouldBe AcDualZoneSide.LEFT
    }

    "midpoint and right half resolve RIGHT" {
        resolveAcDualZoneSide(50f, 100) shouldBe AcDualZoneSide.RIGHT
        resolveAcDualZoneSide(99.999f, 100) shouldBe AcDualZoneSide.RIGHT
    }

    "full touch cell including padding participates in the split" {
        resolveAcDualZoneSide(5f, 120) shouldBe AcDualZoneSide.LEFT
        resolveAcDualZoneSide(115f, 120) shouldBe AcDualZoneSide.RIGHT
    }
})
''')
    write('app/src/test/java/com/osfans/trime/data/theme/AcDualZoneTextKeyTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.data.theme

import com.osfans.trime.data.theme.model.TextKeyboard
import com.osfans.trime.util.yamlMapOf
import com.osfans.trime.util.yamlScalarOf
import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe

class AcDualZoneTextKeyTest : StringSpec({
    "dual-zone metadata decodes from snake-case YAML" {
        val key = ThemeTestSupport.yaml.decodeFromYamlNode<TextKeyboard.TextKey>(
            yamlMapOf(
                "click" to yamlScalarOf("q"),
                "ac_left_id" to yamlScalarOf("q"),
                "ac_right_id" to yamlScalarOf("w"),
            ),
        )
        key.acLeftId shouldBe "q"
        key.acRightId shouldBe "w"
    }

    "ordinary keys default to no dual-zone metadata" {
        val key = ThemeTestSupport.yaml.decodeFromYamlNode<TextKeyboard.TextKey>(yamlMapOf())
        key.acLeftId shouldBe ""
        key.acRightId shouldBe ""
    }
})
''')
    print('TEST_PATCH_APPLIED')
    raise SystemExit(0)

replace_once(
    'app/src/main/java/com/osfans/trime/data/theme/model/TextKeyboard.kt',
    '''        val hilitedKeyBorderColor: String = "",\n        val hilitedKeySymbolColor: String = "",\n        @Serializable(with = LenientStringListSerializer::class)\n''',
    '''        val hilitedKeyBorderColor: String = "",\n        val hilitedKeySymbolColor: String = "",\n        val acLeftId: String = "",\n        val acRightId: String = "",\n        @Serializable(with = LenientStringListSerializer::class)\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/Key.kt',
    '''    val hint: String = keyDef?.hint ?: ""\n    val popup = keyDef?.popup ?: emptyList()\n\n    val keyTextSize: Float = keyDef?.keyTextSize ?: 0f\n''',
    '''    val hint: String = keyDef?.hint ?: ""\n    val popup = keyDef?.popup ?: emptyList()\n    val acLeftId: String = keyDef?.acLeftId ?: ""\n    val acRightId: String = keyDef?.acRightId ?: ""\n    val hasAcDualZone: Boolean\n        get() = acLeftId.isNotEmpty() && acRightId.isNotEmpty()\n\n    val keyTextSize: Float = keyDef?.keyTextSize ?: 0f\n''',
)

write('app/src/main/java/com/osfans/trime/ime/keyboard/AcDualZone.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.ime.keyboard

enum class AcDualZoneSide {
    LEFT,
    RIGHT,
}

fun resolveAcDualZoneSide(x: Float, touchWidth: Int): AcDualZoneSide =
    if (x < touchWidth / 2f) AcDualZoneSide.LEFT else AcDualZoneSide.RIGHT
''')

replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/GestureFrame.kt',
    '''    var onPress: (() -> Unit)? = null\n    var onRelease: ((behavior: KeyBehavior, longPress: Boolean) -> Unit)? = null\n''',
    '''    var onPressAt: ((x: Float, y: Float) -> Unit)? = null\n    var onPress: (() -> Unit)? = null\n    var onRelease: ((behavior: KeyBehavior, longPress: Boolean) -> Unit)? = null\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/GestureFrame.kt',
    '''                if (vibrateOnKeyPress) InputFeedbackManager.keyPressVibrate(this)\n                onPress?.invoke()\n''',
    '''                if (vibrateOnKeyPress) InputFeedbackManager.keyPressVibrate(this)\n                onPressAt?.invoke(x, y)\n                onPress?.invoke()\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/KeyView.kt',
    '''    private var keyPressed = false\n    override fun isPressed(): Boolean = keyPressed\n''',
    '''    private var keyPressed = false\n    private var pressedAcSide: AcDualZoneSide? = null\n    override fun isPressed(): Boolean = keyPressed\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/KeyView.kt',
    '''        hasLazyDouble = key.hasAction(KeyBehavior.LAZY_DOUBLE_CLICK)\n        hasPopup = key.popup.isNotEmpty()\n\n        onPress = {\n''',
    '''        hasLazyDouble = key.hasAction(KeyBehavior.LAZY_DOUBLE_CLICK)\n        hasPopup = key.popup.isNotEmpty()\n\n        onPressAt = { x, _ ->\n            pressedAcSide = if (key.hasAcDualZone) resolveAcDualZoneSide(x, width) else null\n        }\n\n        onPress = {\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/KeyView.kt',
    '''                        val pressedIdx = keyboard.firstPressedKeyIndex\n                        val actionBehavior = if (pressedIdx != -1 && pressedIdx != id) KeyBehavior.COMBO else behavior\n                        key.getAction(actionBehavior)?.let { processKeyAction(it, actionBehavior) }\n''',
    '''                        val pressedIdx = keyboard.firstPressedKeyIndex\n                        val actionBehavior = if (pressedIdx != -1 && pressedIdx != id) KeyBehavior.COMBO else behavior\n                        if (actionBehavior == KeyBehavior.CLICK && key.hasAcDualZone) {\n                            pressedAcSide?.let { side ->\n                                service.postRimeJob { setRuntimeProperty("ac_touch_side", side.name) }\n                            }\n                        }\n                        key.getAction(actionBehavior)?.let { processKeyAction(it, actionBehavior) }\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/KeyView.kt',
    '''            if (keyboard.firstPressedKeyIndex == id) keyboard.firstPressedKeyIndex = -1\n        }\n''',
    '''            if (keyboard.firstPressedKeyIndex == id) keyboard.firstPressedKeyIndex = -1\n            pressedAcSide = null\n        }\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/ime/keyboard/KeyView.kt',
    '''        onCancel = {\n            deletedTextBuffer.clear()\n            setPressedState(false)\n            dismissPopupPreview()\n        }\n''',
    '''        onCancel = {\n            deletedTextBuffer.clear()\n            pressedAcSide = null\n            setPressedState(false)\n            dismissPopupPreview()\n        }\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/core/RimeApi.kt',
    '''    suspend fun getRuntimeOption(option: String): Boolean\n\n    suspend fun setNullInputType(value: Boolean)\n''',
    '''    suspend fun getRuntimeOption(option: String): Boolean\n\n    suspend fun setRuntimeProperty(\n        name: String,\n        value: String,\n    )\n\n    suspend fun setNullInputType(value: Boolean)\n''',
)

replace_once(
    'app/src/main/java/com/osfans/trime/core/Rime.kt',
    '''    override suspend fun getRuntimeOption(option: String): Boolean = withRimeContext {\n        getRimeOption(option)\n    }\n\n    override suspend fun setNullInputType(value: Boolean) = withRimeContext {\n''',
    '''    override suspend fun getRuntimeOption(option: String): Boolean = withRimeContext {\n        getRimeOption(option)\n    }\n\n    override suspend fun setRuntimeProperty(\n        name: String,\n        value: String,\n    ): Unit = withRimeContext {\n        setRimeProperty(name, value)\n    }\n\n    override suspend fun setNullInputType(value: Boolean) = withRimeContext {\n''',
)
replace_once(
    'app/src/main/java/com/osfans/trime/core/Rime.kt',
    '''        external fun getRimeOption(option: String): Boolean\n\n        @JvmStatic\n        external fun getRimeSchemaList(): Array<SchemaItem>\n''',
    '''        external fun getRimeOption(option: String): Boolean\n\n        @JvmStatic\n        external fun setRimeProperty(\n            name: String,\n            value: String,\n        )\n\n        @JvmStatic\n        external fun getRimeSchemaList(): Array<SchemaItem>\n''',
)

replace_once(
    'app/src/main/jni/librime_jni/rime_jni.cc',
    '''  bool getOption(std::string_view key) {\n    return rime->get_option(session(), key.data());\n  }\n\n  std::string currentSchemaId() {\n''',
    '''  bool getOption(std::string_view key) {\n    return rime->get_option(session(), key.data());\n  }\n\n  void setProperty(std::string_view key, std::string_view value) {\n    rime->set_property(session(), key.data(), value.data());\n  }\n\n  std::string currentSchemaId() {\n''',
)
replace_once(
    'app/src/main/jni/librime_jni/rime_jni.cc',
    '''extern "C" JNIEXPORT void JNICALL Java_com_osfans_trime_core_Rime_setRimeOption(\n    JNIEnv* env, jclass /* thiz */, jstring option, jboolean value) {\n  Rime::Instance().setOption(*CString(env, option), value);\n}\n''',
    '''extern "C" JNIEXPORT void JNICALL Java_com_osfans_trime_core_Rime_setRimeOption(\n    JNIEnv* env, jclass /* thiz */, jstring option, jboolean value) {\n  Rime::Instance().setOption(*CString(env, option), value);\n}\n\nextern "C" JNIEXPORT void JNICALL Java_com_osfans_trime_core_Rime_setRimeProperty(\n    JNIEnv* env, jclass /* thiz */, jstring name, jstring value) {\n  Rime::Instance().setProperty(*CString(env, name), *CString(env, value));\n}\n''',
)

print('IMPLEMENTATION_PATCH_APPLIED')
