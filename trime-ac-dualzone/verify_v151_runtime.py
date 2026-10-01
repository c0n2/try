#!/usr/bin/env python3
from pathlib import Path
import argparse
import re
import sys

p = argparse.ArgumentParser()
p.add_argument("root", type=Path)
a = p.parse_args()
root = a.root

service_path = root / "app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt"
daemon_path = root / "app/src/main/java/com/osfans/trime/daemon/RimeDaemon.kt"

service = service_path.read_text(encoding="utf-8")
daemon = daemon_path.read_text(encoding="utf-8")

failures = []

# Device crash 2026-10-01: AlertDialog was created on DefaultDispatcher-worker-3.
if "Dispatchers.Main.immediate" not in service:
    failures.append("UI_MAIN_DISPATCH_MISSING")
if not re.search(
    r"private fun showAcAddWordDialog\([^)]*\)\s*\{\s*"
    r"lifecycleScope\.launch\(Dispatchers\.Main\.immediate\)",
    service,
    re.S,
):
    failures.append("ADD_WORD_DIALOG_NOT_MAIN_WRAPPED")

# Device failure 2026-10-01: levers import tried to open the live userdb and hit LOCK.
if "fun <T> runMaintenance(block: () -> T): T" not in daemon:
    failures.append("RIME_MAINTENANCE_API_MISSING")
else:
    marker = "fun <T> runMaintenance(block: () -> T): T"
    body = daemon[daemon.index(marker):]
    for token, label in [
        ("lock.withLock", "RIME_MAINTENANCE_LOCK_MISSING"),
        ("realRime.finalize()", "RIME_MAINTENANCE_FINALIZE_MISSING"),
        ("try", "RIME_MAINTENANCE_TRY_MISSING"),
        ("finally", "RIME_MAINTENANCE_FINALLY_MISSING"),
        ("tryStartRimeLocked()", "RIME_MAINTENANCE_RESTART_MISSING"),
        ("scheduleStartupRetry()", "RIME_MAINTENANCE_RETRY_MISSING"),
    ]:
        if token not in body:
            failures.append(label)

if not re.search(
    r"RimeDaemon\.runMaintenance\s*\{[\s\S]*?UserDictManager\.importUserDict\(",
    service,
):
    failures.append("ADD_WORD_IMPORT_NOT_MAINTENANCE_WRAPPED")

# Safety: never "fix" the LevelDB collision by deleting its lock file.
if re.search(r"userdb[/\\\\]LOCK|\.userdb.*LOCK|delete\([^\n]*LOCK", service + "\n" + daemon, re.I):
    failures.append("FORBIDDEN_USERDB_LOCK_MUTATION")

if failures:
    print("V151_RUNTIME_CONTRACT=FAIL")
    for failure in failures:
        print(f"FAIL={failure}")
    sys.exit(1)

print("V151_RUNTIME_CONTRACT=PASS")
print("UI_MAIN_DISPATCH=PASS")
print("RIME_STOP_IMPORT_RESTART=PASS")
print("USERDB_LOCK_MUTATION=ABSENT_PASS")
