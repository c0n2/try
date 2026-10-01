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
    path = root / rel
    path.write_text(text, encoding="utf-8")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{rel}: expected exactly one replacement target, got {count}: {old[:180]!r}",
        )
    write(rel, text.replace(old, new, 1))


service = "app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt"
daemon = "app/src/main/java/com/osfans/trime/daemon/RimeDaemon.kt"

# Device crash 2026-10-01: Ctrl+P with no valid selection entered this
# function from Rime's DefaultDispatcher worker and constructed AlertDialog
# objects without a main Looper. Keep every UI object below on Main.
replace_once(
    service,
    '''    private fun showAcAddWordDialog(initialWord: String = "") {\n        val wordInput = EditText(this).apply {\n''',
    '''    private fun showAcAddWordDialog(initialWord: String = "") {\n        lifecycleScope.launch(Dispatchers.Main.immediate) {\n            showAcAddWordDialogOnMain(initialWord)\n        }\n    }\n\n    private fun showAcAddWordDialogOnMain(initialWord: String) {\n        val wordInput = EditText(this).apply {\n''',
)

# Device failure 2026-10-01: librime levers import attempted to open the
# active userdb while the running Rime instance already held LevelDB/LOCK.
# The daemon transaction below releases that lock for the duration of import.
replace_once(
    service,
    '''            val result =\n                UserDictManager.importUserDict(\n                    payload.byteInputStream(Charsets.UTF_8),\n                    AC_ADD_WORD_USER_DICT,\n                    "ac-add-word.txt",\n                )\n''',
    '''            val result =\n                RimeDaemon.runMaintenance {\n                    UserDictManager.importUserDict(\n                        payload.byteInputStream(Charsets.UTF_8),\n                        AC_ADD_WORD_USER_DICT,\n                        "ac-add-word.txt",\n                    )\n                }\n''',
)

# Use RimeDaemon's existing lock/startup/retry machinery. Sessions remain
# registered; only the underlying Rime instance is finalized temporarily.
replace_once(
    daemon,
    '''    /**\n     * Restart Rime instance to deploy while keep the session\n     */\n    fun restartRime(fullCheck: Boolean = false) = lock.withLock {\n''',
    '''    /**\n     * Run an exclusive operation while Rime is stopped. This is required for\n     * maintenance APIs such as user-dictionary import that need the LevelDB\n     * userdb lock held by the live Rime instance. Existing sessions are kept.\n     */\n    fun <T> runMaintenance(block: () -> T): T = lock.withLock {\n        startupRetryJob?.cancel()\n        startupRetryJob = null\n        try {\n            realRime.finalize()\n            block()\n        } finally {\n            if (sessions.isNotEmpty() && !tryStartRimeLocked()) {\n                scheduleStartupRetry()\n            }\n        }\n    }\n\n    /**\n     * Restart Rime instance to deploy while keep the session\n     */\n    fun restartRime(fullCheck: Boolean = false) = lock.withLock {\n''',
)

print("V151_CTRL_P_RUNTIME_FIX_APPLIED")
print("V151_UI_MAIN_DISPATCH_APPLIED")
print("V151_RIME_MAINTENANCE_IMPORT_APPLIED")
