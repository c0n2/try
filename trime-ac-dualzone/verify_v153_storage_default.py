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
setup = read("app/src/main/java/com/osfans/trime/ui/setup/SetupFragment.kt")

failures = []

def require(ok: bool, code: str) -> None:
    if ok:
        print(f"PASS={code}")
    else:
        failures.append(code)
        print(f"FAIL={code}")

require(
    'val dataStorageMode = enum(R.string.data_storage_mode, DATA_STORAGE_MODE, DataStorageMode.APP_STORAGE)' in app_prefs,
    "APP_STORAGE_IS_FRESH_INSTALL_DEFAULT",
)
require(
    'DataStorageMode.APP_STORAGE -> true' in sync,
    "APP_STORAGE_REQUIRES_NO_TREE_URI",
)
require(
    'DataStorageMode.EXTERNAL_SYNC -> treeUri.isNotEmpty()' in sync,
    "EXTERNAL_SYNC_STILL_REQUIRES_TREE_URI",
)
require(
    'R.id.sync_from_external_option -> DataStorageMode.EXTERNAL_SYNC' in setup and
    'R.id.app_specific_storage_option -> DataStorageMode.APP_STORAGE' in setup,
    "BOTH_STORAGE_CHOICES_REMAIN_AVAILABLE",
)

if failures:
    raise SystemExit("V153_STORAGE_DEFAULT_CONTRACT=FAIL:" + ",".join(failures))

print("V153_STORAGE_DEFAULT_CONTRACT=PASS")
