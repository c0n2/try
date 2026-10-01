#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

service = (root / "app/src/main/java/com/osfans/trime/ime/core/TrimeInputMethodService.kt").read_text(encoding="utf-8")
daemon = (root / "app/src/main/java/com/osfans/trime/daemon/RimeDaemon.kt").read_text(encoding="utf-8")
rime = (root / "app/src/main/java/com/osfans/trime/core/Rime.kt").read_text(encoding="utf-8")
jni = (root / "app/src/main/jni/librime_jni/rime_jni.cc").read_text(encoding="utf-8")

failures = []

def require(cond: bool, name: str) -> None:
    if not cond:
        failures.append(name)

# v1.5.2 architecture: keep librime initialized and release only the active
# native session while levers imports the dictionary. Full Rime finalize/start
# is forbidden here because levers itself depends on initialized librime.
require("RimeDaemon.runSessionMaintenance" in service, "SERVICE_NOT_SESSION_MAINTENANCE_WRAPPED")
require("RimeDaemon.runMaintenance" not in service, "SERVICE_STILL_USES_FULL_MAINTENANCE")

require("suspend fun <T> runSessionMaintenance" in daemon, "DAEMON_SESSION_MAINTENANCE_API_MISSING")
require("realRime.runSessionMaintenance(block)" in daemon, "DAEMON_NOT_DELEGATING_TO_RIME_DISPATCHER")

require("suspend fun <T> runSessionMaintenance" in rime, "RIME_SESSION_MAINTENANCE_API_MISSING")
require("releaseRimeSession()" in rime, "RIME_RELEASE_SESSION_NATIVE_API_MISSING")
require("external fun releaseRimeSession()" in rime, "RIME_RELEASE_SESSION_EXTERNAL_MISSING")

require("void releaseSession()" in jni and "session_.reset();" in jni, "JNI_RELEASE_SESSION_IMPL_MISSING")
require("Java_com_osfans_trime_core_Rime_releaseRimeSession" in jni, "JNI_RELEASE_SESSION_ENTRYPOINT_MISSING")

# The old v1.5.1 daemon maintenance implementation is specifically forbidden.
if "fun <T> runMaintenance(block: () -> T): T" in daemon and "realRime.finalize()" in daemon:
    failures.append("FULL_RIME_FINALIZE_MAINTENANCE_PRESENT")

# Never work around LevelDB by touching LOCK files directly.
all_text = "\n".join((service, daemon, rime, jni))
require("delete" not in all_text.lower() or "LOCK" not in all_text, "LOCK_FILE_MUTATION_PRESENT")

if failures:
    print("V152_SESSION_MAINTENANCE_CONTRACT=FAIL")
    for failure in failures:
        print(f"FAIL={failure}")
    raise SystemExit(1)

print("V152_SESSION_MAINTENANCE_CONTRACT=PASS")
print("PASS=SERVICE_USES_SESSION_MAINTENANCE")
print("PASS=RIME_RELEASES_ONLY_NATIVE_SESSION")
print("PASS=LIBRIME_LIFECYCLE_REMAINS_READY")
print("PASS=NO_LOCK_FILE_MUTATION")
