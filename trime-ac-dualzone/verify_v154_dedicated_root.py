#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument("root", type=Path)
a = p.parse_args()
root = a.root


def read(rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")

app_prefs = read("app/src/main/java/com/osfans/trime/data/prefs/AppPrefs.kt")
sync = read("app/src/main/java/com/osfans/trime/data/sync/RimeDataSync.kt")
setup = read("app/src/main/java/com/osfans/trime/ui/setup/SetupActivity.kt")

failures = []


def require(ok: bool, code: str) -> None:
    if ok:
        print(f"PASS={code}")
    else:
        failures.append(code)
        print(f"FAIL={code}")

require(
    'val dataStorageMode = enum(R.string.data_storage_mode, DATA_STORAGE_MODE, DataStorageMode.EXTERNAL_SYNC)' in app_prefs,
    "EXTERNAL_SYNC_IS_AC_FRESH_INSTALL_DEFAULT",
)
require(
    'const val AC_EXTERNAL_DIR_NAME = "AC-Trime"' in sync,
    "AC_DEDICATED_ROOT_IS_DECLARED",
)
require(
    'fun acExternalInitialUri()' in sync and 'primary:$AC_EXTERNAL_DIR_NAME' in sync,
    "PICKER_TARGETS_AC_TRIME_ON_PRIMARY_STORAGE",
)
require(
    'fun isAcExternalTree(uri: Uri): Boolean' in sync and 'AC_EXTERNAL_DIR_NAME' in sync,
    "SELECTED_TREE_IS_VALIDATED_AS_AC_TRIME",
)
require(
    'dataPathPicker.launch(RimeDataSync.acExternalInitialUri())' in setup,
    "SETUP_PICKER_USES_DEDICATED_INITIAL_URI",
)
require(
    'RimeDataSync.isAcExternalTree(uri)' in setup,
    "SETUP_REJECTS_NON_DEDICATED_TREE",
)
require(
    'RimeDataSync.persistTreeUri(this@SetupActivity, uri)' in setup,
    "SAF_GRANT_IS_PERSISTED_BEFORE_IMPORT",
)
require(
    'RimeDataSync.clearExternalTree(this@SetupActivity)' not in setup,
    "IMPORT_FAILURE_DOES_NOT_ROLL_BACK_SAF_GRANT",
)
require(
    'AC_EXTERNAL_SYNC_V154_MIGRATED' in app_prefs and 'acExternalSyncV154Migrated' in app_prefs,
    "V153_APP_STORAGE_HAS_ONE_TIME_MIGRATION_MARKER",
)
require(
    'ensureAcExternalSyncV154Default()' in sync and 'acExternalSyncV154Migrated' in sync,
    "V153_APP_STORAGE_IS_MIGRATED_ONCE",
)
require(
    'RimeDataSync.ensureAcExternalSyncV154Default()' in setup,
    "SETUP_RUNS_V154_STORAGE_MIGRATION",
)

if failures:
    raise SystemExit("V154_DEDICATED_ROOT_CONTRACT=FAIL:" + ",".join(failures))

print("V154_DEDICATED_ROOT_CONTRACT=PASS")
