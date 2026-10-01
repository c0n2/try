#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument("root", type=Path)
a = p.parse_args()
root = a.root

path = root / "app/src/main/java/com/osfans/trime/data/prefs/AppPrefs.kt"
text = path.read_text(encoding="utf-8")
old = "val dataStorageMode = enum(R.string.data_storage_mode, DATA_STORAGE_MODE, DataStorageMode.EXTERNAL_SYNC)"
new = "val dataStorageMode = enum(R.string.data_storage_mode, DATA_STORAGE_MODE, DataStorageMode.APP_STORAGE)"
count = text.count(old)
if count != 1:
    raise SystemExit(f"AppPrefs.kt: expected one storage-default target, got {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

print("V153_APP_STORAGE_DEFAULT_APPLIED")
print("V153_EXTERNAL_SYNC_OPTION_PRESERVED")
