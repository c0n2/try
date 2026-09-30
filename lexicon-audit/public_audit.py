#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import sys
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(os.environ.get("AUDIT_OUT", "lexicon-audit-out"))
RAW = ROOT / "raw"
WORDS = ROOT / "words"
RAW.mkdir(parents=True, exist_ok=True)
WORDS.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "raincandy": {
        "repo": "RainCandyTech/WeaselSchemaSetup",
        "commit": "f327d602b5af3d06bc8cbf0856714b0607fb02a5",
        "files": ["Schemas/RimeWubiTables86/wubi.dict.yaml"],
        "note": "Exact Wubi86 source used by the AC Trime RainCandy conversion.",
    },
    "frost_wubi": {
        "repo": "gaboolic/rime-frost",
        "commit": "2a027a0affdadd43194e6b3dc12cfffdd1426379",
        "files": ["cn_dicts_wb/chars.dict.yaml", "cn_dicts_wb/words.dict.yaml"],
        "note": "Runtime imports of rime_frost_wubi86.dict.yaml.",
    },
    "wanxiang_core": {
        "repo": "amzxyz/rime-wanxiang",
        "commit": "94f1e8d7b6d1267a9c8752a2e62145705dd1fb92",
        "files": ["dicts/zi.dict.yaml", "dicts/jichu.dict.yaml"],
        "note": "Core characters + 2-4 character base vocabulary.",
    },
    "wanxiang_full": {
        "repo": "amzxyz/rime-wanxiang",
        "commit": "94f1e8d7b6d1267a9c8752a2e62145705dd1fb92",
        "files": [
            "dicts/zi.dict.yaml", "dicts/jichu.dict.yaml", "dicts/lianxiang.dict.yaml",
            "dicts/cuoyin.dict.yaml", "dicts/duoyin.dict.yaml", "dicts/shici.dict.yaml",
            "dicts/diming.dict.yaml", "dicts/yixue.dict.yaml", "dicts/huaxue.dict.yaml",
            "dicts/yaopin.dict.yaml", "dicts/mingren.dict.yaml", "dicts/yiren.dict.yaml",
            "dicts/wuzhong.dict.yaml", "dicts/renming.dict.yaml", "dicts/taifeng.dict.yaml",
            "dicts/fangyan.dict.yaml",
        ],
        "note": "All tables imported by wanxiang.dict.yaml at the pinned commit.",
    },
    "ice_standard": {
        "repo": "iDvel/rime-ice",
        "commit": "3aea6d3694fb3d94ec663641f021f788822897ad",
        "files": [
            "cn_dicts/8105.dict.yaml", "cn_dicts/base.dict.yaml", "cn_dicts/ext.dict.yaml",
            "cn_dicts/tencent.dict.yaml", "cn_dicts/others.dict.yaml",
        ],
        "note": "Default imports of rime_ice.dict.yaml; optional 41448 table excluded.",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def raw_url(repo: str, commit: str, rel: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{commit}/{rel}"


def download(repo: str, commit: str, rel: str) -> Path:
    dest = RAW / repo.replace("/", "__") / commit / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        url = raw_url(repo, commit, rel)
        print(f"DOWNLOAD {url}", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "AC-Trime-Lexicon-Audit/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r, dest.open("wb") as w:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                w.write(chunk)
    return dest


def iter_rime_entries(path: Path) -> Iterable[str]:
    """Yield normalized first-column text from a Rime dictionary body.

    Supports ordinary YAML headers terminated by `...`, comments/blank lines,
    and body rows with one or more tab-separated columns. If a file has no YAML
    header, non-comment tabbed/plain rows are still accepted.
    """
    header_seen = False
    in_body = False
    with path.open("r", encoding="utf-8-sig", errors="strict") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped == "---" and not in_body:
                header_seen = True
                continue
            if stripped == "..." and header_seen and not in_body:
                in_body = True
                continue
            if header_seen and not in_body:
                continue
            # Some dictionaries omit a YAML header. Avoid obvious YAML metadata.
            if not header_seen and "\t" not in line and ":" in line:
                continue
            text = line.split("\t", 1)[0].strip()
            if not text:
                continue
            yield unicodedata.normalize("NFC", text)


def is_han_char(ch: str) -> bool:
    cp = ord(ch)
    return (
        cp == 0x3007
        or 0x3400 <= cp <= 0x4DBF
        or 0x4E00 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x20000 <= cp <= 0x2EBEF
        or 0x30000 <= cp <= 0x323AF
    )


def kind(word: str) -> str:
    if word and all(is_han_char(c) for c in word):
        return "han_only"
    has_han = any(is_han_char(c) for c in word)
    if has_han:
        return "mixed_han"
    if word and all(ord(c) < 128 for c in word):
        return "ascii_only"
    return "other"


def len_bucket(n: int) -> str:
    if n <= 4:
        return str(n)
    if n <= 6:
        return "5-6"
    return "7+"


def analyze_profile(name: str, spec: dict, file_cache: dict[tuple[str, str, str], Path]):
    words_all: list[str] = []
    file_meta = []
    for rel in spec["files"]:
        key = (spec["repo"], spec["commit"], rel)
        path = file_cache.get(key)
        if path is None:
            path = download(*key)
            file_cache[key] = path
        entry_count = 0
        for text in iter_rime_entries(path):
            words_all.append(text)
            entry_count += 1
        file_meta.append({
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "entry_count": entry_count,
        })

    counts = Counter(words_all)
    unique = set(counts)
    lens = Counter(len_bucket(len(w)) for w in unique)
    kinds = Counter(kind(w) for w in unique)
    duplicate_texts = sum(1 for n in counts.values() if n > 1)
    duplicate_extra_rows = sum(n - 1 for n in counts.values() if n > 1)

    out_words = WORDS / f"{name}.txt.gz"
    with gzip.open(out_words, "wt", encoding="utf-8", newline="\n", compresslevel=9) as f:
        for w in sorted(unique):
            f.write(w + "\n")

    # A deliberately conservative candidate view for AC supplementation.
    clean = sorted(w for w in unique if 2 <= len(w) <= 6 and kind(w) == "han_only")
    out_clean = WORDS / f"{name}.han2to6.txt.gz"
    with gzip.open(out_clean, "wt", encoding="utf-8", newline="\n", compresslevel=9) as f:
        for w in clean:
            f.write(w + "\n")

    return unique, {
        "profile": name,
        "repo": spec["repo"],
        "commit": spec["commit"],
        "note": spec["note"],
        "files": file_meta,
        "raw_entry_count": len(words_all),
        "unique_word_count": len(unique),
        "duplicate_text_count": duplicate_texts,
        "duplicate_extra_rows": duplicate_extra_rows,
        "length_distribution": {k: lens.get(k, 0) for k in ["1", "2", "3", "4", "5-6", "7+"]},
        "kind_distribution": {k: kinds.get(k, 0) for k in ["han_only", "mixed_han", "ascii_only", "other"]},
        "han_2_to_6_count": len(clean),
        "word_list_gzip": str(out_words.relative_to(ROOT)),
        "clean_word_list_gzip": str(out_clean.relative_to(ROOT)),
    }


def pairwise_rows(sets: dict[str, set[str]]):
    names = list(sets)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sa, sb = sets[a], sets[b]
            inter = len(sa & sb)
            union = len(sa | sb)
            rows.append({
                "a": a,
                "b": b,
                "a_unique_words": len(sa),
                "b_unique_words": len(sb),
                "intersection": inter,
                "jaccard": inter / union if union else 0.0,
                "a_covered_by_b": inter / len(sa) if sa else 0.0,
                "b_covered_by_a": inter / len(sb) if sb else 0.0,
                "a_only": len(sa - sb),
                "b_only": len(sb - sa),
            })
    return rows


def main() -> int:
    file_cache: dict[tuple[str, str, str], Path] = {}
    sets: dict[str, set[str]] = {}
    summaries = {}
    for name, spec in SOURCES.items():
        print(f"ANALYZE {name}", flush=True)
        s, summary = analyze_profile(name, spec, file_cache)
        sets[name] = s
        summaries[name] = summary
        print(f"  unique={len(s):,} raw={summary['raw_entry_count']:,}", flush=True)

    rows = pairwise_rows(sets)
    with (ROOT / "pairwise_public.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Useful public-only deltas to inspect before bringing in the private AC core.
    rc, fr, wx_core, wx_full, ice = (
        sets["raincandy"], sets["frost_wubi"], sets["wanxiang_core"], sets["wanxiang_full"], sets["ice_standard"]
    )
    deltas = {
        "frost_not_raincandy": fr - rc,
        "raincandy_not_frost": rc - fr,
        "wanxiang_core_not_frost_or_raincandy": wx_core - fr - rc,
        "wanxiang_full_not_frost_or_raincandy": wx_full - fr - rc,
        "ice_not_frost": ice - fr,
        "ice_not_frost_or_wanxiang_full": ice - fr - wx_full,
    }
    delta_counts = {}
    for name, values in deltas.items():
        delta_counts[name] = len(values)
        path = WORDS / f"delta-{name}.txt.gz"
        with gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=9) as f:
            for w in sorted(values):
                f.write(w + "\n")

    manifest = {
        "format": "AC_TRIME_LEXICON_PUBLIC_AUDIT_V1",
        "sources": SOURCES,
        "profiles": summaries,
        "public_delta_counts": delta_counts,
    }
    (ROOT / "public_summary.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Compact human-readable report.
    lines = [
        "# AC Trime Public Lexicon Audit — Phase 0",
        "",
        "This report intentionally excludes the user's private AC lexicon; it is merged locally after artifact download.",
        "",
        "## Profile summary",
        "",
        "| profile | raw entries | unique words | Han 2–6 | duplicates (texts) |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in SOURCES:
        s = summaries[name]
        lines.append(
            f"| {name} | {s['raw_entry_count']:,} | {s['unique_word_count']:,} | {s['han_2_to_6_count']:,} | {s['duplicate_text_count']:,} |"
        )
    lines += ["", "## Public deltas", ""]
    for k, v in delta_counts.items():
        lines.append(f"- {k}: {v:,}")
    lines.append("")
    (ROOT / "PUBLIC-REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print("PUBLIC_LEXICON_AUDIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
