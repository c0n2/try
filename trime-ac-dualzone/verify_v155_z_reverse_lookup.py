#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib
import re
import sys

PINYIN_SIMP_COMMIT = "0c6861ef7420ee780270ca6d993d18d4101049d0"
CUSTOM_NAME = "ac_raincandy_wubi86.custom.yaml"

p = argparse.ArgumentParser()
p.add_argument("root", type=Path, help="source or packaged v1.5.5 data directory")
p.add_argument("--artifact", action="store_true", help="also require vendored upstream pinyin-simp files")
a = p.parse_args()
root = a.root

results = []

def check(label, ok, detail=""):
    results.append((label, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}={label}" + (f":{detail}" if detail else ""))

custom = root / CUSTOM_NAME
manifest = root / "UPSTREAM.txt"
readme = root / "README.txt"

check("AC_CUSTOM_PATCH_EXISTS", custom.is_file())
check("UPSTREAM_MANIFEST_EXISTS", manifest.is_file())
check("README_EXISTS", readme.is_file())

custom_text = custom.read_text(encoding="utf-8") if custom.is_file() else ""
manifest_text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""

# AC formal schema remains the owner; v1.5.5 must be a .custom overlay, not a replacement schema.
check("PATCH_DOES_NOT_REPLACE_FORMAL_SCHEMA", not (root / "ac_raincandy_wubi86.schema.yaml").exists())
check("PATCH_TARGETS_FORMAL_SCHEMA_BY_FILENAME", custom.name == CUSTOM_NAME)
check("NO_TONGWENFENG_MUTATION", "tongwenfeng" not in custom_text.lower())

# The official Rime Wubi Z-lookup chain.
check("PINYIN_SIMP_DEPENDENCY", bool(re.search(r"schema/dependencies|dependencies", custom_text)) and "pinyin_simp" in custom_text)
check("REVERSE_LOOKUP_TRANSLATOR", "reverse_lookup_translator" in custom_text)
check("NORMAL_TABLE_TRANSLATOR_PRESERVED", "table_translator" in custom_text)
check("PUNCT_TRANSLATOR_PRESERVED", "punct_translator" in custom_text)
check("Z_USER_DICT_GUARD", "^z.*$" in custom_text)
check("REVERSE_LOOKUP_DICTIONARY", bool(re.search(r"reverse_lookup:\s*\n(?:.*\n){0,8}\s*dictionary:\s*[\"']?pinyin_simp", custom_text)))
check("REVERSE_LOOKUP_PREFIX_Z", bool(re.search(r"\bprefix:\s*[\"']?z[\"']?", custom_text)))
check("REVERSE_LOOKUP_SUFFIX_APOSTROPHE", "suffix:" in custom_text and "'" in custom_text)
check("REVERSE_LOOKUP_TIPS_PINYIN", "拼音" in custom_text)
check("PINYIN_UMLAUT_PREEDIT", all(x in custom_text for x in ["([nl])v", "([nl])ue", "([jqxy])v"]))
check("Z_RECOGNIZER_PATTERN", "^z[a-z]*'?$" in custom_text)

# Reproducibility: pin the official pinyin-simp source, never float on master.
check("PINYIN_SIMP_SOURCE_REPO", "rime/rime-pinyin-simp" in manifest_text)
check("PINYIN_SIMP_SOURCE_PINNED", PINYIN_SIMP_COMMIT in manifest_text)
check("README_INSTALLS_TO_AC_TRIME", "AC-Trime" in readme_text)
check("README_REDEPLOY_REQUIRED", "部署" in readme_text or "redeploy" in readme_text.lower())

if a.artifact:
    required = ["pinyin_simp.dict.yaml", "pinyin_simp.schema.yaml", "PINYIN_SIMP_LICENSE"]
    for name in required:
        check(f"ARTIFACT_{name.upper().replace('.', '_')}", (root / name).is_file())
    dict_file = root / "pinyin_simp.dict.yaml"
    schema_file = root / "pinyin_simp.schema.yaml"
    if dict_file.is_file():
        txt = dict_file.read_text(encoding="utf-8")
        check("PINYIN_DICT_IDENTITY", "name: pinyin_simp" in txt and "sort: by_weight" in txt)
        check("PINYIN_DICT_HAS_NI", bool(re.search(r"^你\tni(?:\t|$)", txt, re.M)))
    if schema_file.is_file():
        txt = schema_file.read_text(encoding="utf-8")
        check("PINYIN_SCHEMA_IDENTITY", "schema_id: pinyin_simp" in txt and "dictionary: pinyin_simp" in txt)

failed = [name for name, ok, _ in results if not ok]
if failed:
    print("V155_Z_REVERSE_LOOKUP_CONTRACT=FAIL:" + ",".join(failed))
    sys.exit(1)
print("V155_Z_REVERSE_LOOKUP_CONTRACT=PASS")
