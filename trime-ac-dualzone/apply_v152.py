#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument("root", type=Path)
a = p.parse_args()
root = a.root


def read(rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (root / rel).write_text(text, encoding="utf-8")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected one target, got {count}: {old[:180]!r}")
    write(rel, text.replace(old, new, 1))

service = "app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt"
daemon = "app/src/main/java/com/osfans/trime/daemon/RimeDaemon.kt"
rime = "app/src/main/java/com/osfans/trime/core/Rime.kt"
jni = "app/src/main/jni/librime_jni/rime_jni.cc"

# v1.5.1 stopped the entire librime runtime before calling levers import.
# v1.5.2 keeps librime initialized and releases only the active input session.
replace_once(
    service,
    "RimeDaemon.runMaintenance {\n",
    "RimeDaemon.runSessionMaintenance {\n",
)

replace_once(
    daemon,
    '''    /**\n     * Run an exclusive operation while Rime is stopped. This is required for\n     * maintenance APIs such as user-dictionary import that need the LevelDB\n     * userdb lock held by the live Rime instance. Existing sessions are kept.\n     */\n    fun <T> runMaintenance(block: () -> T): T = lock.withLock {\n        startupRetryJob?.cancel()\n        startupRetryJob = null\n        try {\n            realRime.finalize()\n            block()\n        } finally {\n            if (sessions.isNotEmpty() && !tryStartRimeLocked()) {\n                scheduleStartupRetry()\n            }\n        }\n    }\n\n''',
    '''    /**\n     * Run user-dictionary maintenance on Rime's serialized native dispatcher\n     * after releasing only the active input session. Librime stays initialized,\n     * so levers APIs remain valid and the next Rime operation lazily creates a\n     * fresh input session.\n     */\n    suspend fun <T> runSessionMaintenance(block: () -> T): T =\n        realRime.runSessionMaintenance(block)\n\n''',
)

replace_once(
    rime,
    '''    private suspend inline fun <T> withRimeContext(crossinline block: suspend () -> T): T = withContext(dispatcher) {\n        block()\n    }\n\n''',
    '''    private suspend inline fun <T> withRimeContext(crossinline block: suspend () -> T): T = withContext(dispatcher) {\n        block()\n    }\n\n    /**\n     * Release only the active native input session, then run maintenance on the\n     * same single-threaded Rime dispatcher. This frees userdb locks without\n     * finalizing librime or cancelling Rime lifecycle children.\n     */\n    suspend fun <T> runSessionMaintenance(block: () -> T): T = withRimeContext {\n        releaseRimeSession()\n        block()\n    }\n\n''',
)

replace_once(
    rime,
    '''        @JvmStatic\n        external fun startupRime(\n''',
    '''        @JvmStatic\n        external fun releaseRimeSession()\n\n        @JvmStatic\n        external fun startupRime(\n''',
)

replace_once(
    jni,
    '''  void exit() {\n    session_.reset();\n    rime->finalize();\n  }\n''',
    '''  void releaseSession() { session_.reset(); }\n\n  void exit() {\n    session_.reset();\n    rime->finalize();\n  }\n''',
)

replace_once(
    jni,
    '''extern "C" JNIEXPORT void JNICALL\nJava_com_osfans_trime_core_Rime_exitRime(JNIEnv* env, jclass /* thiz */) {\n  Rime::Instance().exit();\n}\n''',
    '''extern "C" JNIEXPORT void JNICALL\nJava_com_osfans_trime_core_Rime_releaseRimeSession(JNIEnv* env,\n                                                   jclass /* thiz */) {\n  Rime::Instance().releaseSession();\n}\n\nextern "C" JNIEXPORT void JNICALL\nJava_com_osfans_trime_core_Rime_exitRime(JNIEnv* env, jclass /* thiz */) {\n  Rime::Instance().exit();\n}\n''',
)

print("V152_SESSION_ONLY_MAINTENANCE_APPLIED")
print("V152_FULL_RIME_FINALIZE_REMOVED_FROM_CTRL_P_IMPORT")
print("V152_NATIVE_SESSION_RELEASE_API_APPLIED")
