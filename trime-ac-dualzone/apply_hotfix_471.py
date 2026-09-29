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
        raise SystemExit(f'{rel}: expected one replacement target, got {count}: {old[:120]!r}')
    write(rel, text.replace(old, new, 1))


if a.phase == 'tests':
    write('app/src/test/java/com/osfans/trime/daemon/RimeApiForwarderTest.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.daemon

import com.osfans.trime.core.RimeApi
import io.kotest.core.spec.style.StringSpec
import io.kotest.matchers.shouldBe
import kotlinx.coroutines.runBlocking
import java.lang.reflect.Proxy

class RimeApiForwarderTest : StringSpec({
    "new RimeApi methods are explicitly forwarded by daemon facade" {
        val calls = mutableListOf<Pair<String, String>>()
        val delegate = Proxy.newProxyInstance(
            RimeApi::class.java.classLoader,
            arrayOf(RimeApi::class.java),
        ) { _, method, args ->
            when (method.name) {
                "setRuntimeProperty" -> {
                    calls += (args[0] as String) to (args[1] as String)
                    Unit
                }
                "toString" -> "FakeRimeApi"
                "hashCode" -> 1
                "equals" -> false
                else -> throw UnsupportedOperationException(method.name)
            }
        } as RimeApi

        runBlocking {
            RimeApiForwarder(delegate).setRuntimeProperty("ac_touch_side", "RIGHT")
        }

        calls shouldBe listOf("ac_touch_side" to "RIGHT")
    }
})
''')
    print('HOTFIX_REGRESSION_TEST_APPLIED')
    raise SystemExit(0)

write('app/src/main/java/com/osfans/trime/daemon/RimeApiForwarder.kt', r'''// SPDX-FileCopyrightText: 2015 - 2026 Rime community
// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.daemon

import com.osfans.trime.core.RimeApi

/**
 * Explicit daemon-facing RimeApi facade.
 *
 * Keep newly-added RimeApi methods explicit here instead of relying only on
 * interface delegation, so the runtime facade cannot miss a method and throw
 * AbstractMethodError when the interface evolves.
 */
internal class RimeApiForwarder(
    private val delegate: RimeApi,
) : RimeApi by delegate {
    override suspend fun setRuntimeProperty(
        name: String,
        value: String,
    ) {
        delegate.setRuntimeProperty(name, value)
    }
}
''')

replace_once(
    'app/src/main/java/com/osfans/trime/daemon/RimeDaemon.kt',
    '    private val rimeImpl by lazy { object : RimeApi by realRime {} }\n',
    '    private val rimeImpl by lazy { RimeApiForwarder(realRime) }\n',
)

print('HOTFIX_IMPLEMENTATION_APPLIED')
