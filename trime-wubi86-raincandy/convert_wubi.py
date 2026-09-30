from __future__ import annotations

from pathlib import Path
from typing import Iterator

FOLD_MAP = str.maketrans({
    'q': 'q', 'w': 'q',
    'e': 'e', 'r': 'e',
    't': 't', 'y': 't',
    'u': 'u', 'i': 'u',
    'o': 'o', 'p': 'o',
    'a': 'a', 's': 'a',
    'd': 'd', 'f': 'd',
    'g': 'g', 'h': 'g',
    'j': 'j', 'k': 'j',
    'l': 'l', 'z': 'z',
    'x': 'x', 'c': 'x',
    'v': 'v', 'b': 'v',
    'n': 'n', 'm': 'n',
})


def fold_code(code: str) -> str:
    return code.translate(FOLD_MAP)


def _split_source(source: str) -> tuple[list[str], list[str]]:
    lines = source.splitlines()
    try:
        marker = lines.index('...')
    except ValueError as exc:
        raise ValueError("source dictionary has no YAML terminator '...'") from exc
    return lines[:marker + 1], lines[marker + 1:]


def parse_entries(source: str) -> Iterator[list[str]]:
    _, body = _split_source(source)
    for line in body:
        if not line or line.startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) >= 2:
            yield cols


def render_dictionary(source: str, *, name: str, fold: bool) -> str:
    _, body = _split_source(source)
    out = [
        '# Rime dictionary generated from RainCandyTech/WeaselSchemaSetup',
        '# Source: Schemas/RimeWubiTables86/wubi.dict.yaml',
        '# Encoding: UTF-8',
        '',
        '---',
        f'name: {name}',
        'version: "2026.09.29-ac"',
        'sort: by_weight',
        'columns:',
        '  - text',
        '  - code',
        '  - weight',
        '  - stem',
        '...',
    ]
    for line in body:
        if fold and line and not line.startswith('#'):
            cols = line.split('\t')
            if len(cols) >= 2:
                cols[1] = fold_code(cols[1])
                line = '\t'.join(cols)
        out.append(line)
    return '\n'.join(out).rstrip('\n') + '\n'


def convert_file(source_path: Path, normal_path: Path, double_path: Path) -> None:
    source = source_path.read_text(encoding='utf-8')
    normal_path.write_text(
        render_dictionary(source, name='ac_raincandy_wubi86', fold=False),
        encoding='utf-8', newline='\n')
    double_path.write_text(
        render_dictionary(source, name='ac_raincandy_wubi86_double', fold=True),
        encoding='utf-8', newline='\n')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('normal', type=Path)
    parser.add_argument('double', type=Path)
    args = parser.parse_args()
    convert_file(args.source, args.normal, args.double)
