from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from convert_wubi import fold_code, parse_entries, render_dictionary


def test_fold_code_uses_ac_pairs_and_keeps_z():
    assert fold_code('qwertyuiopasdfghjklzxcvbnm') == 'qqeettuuooaaddggjjlzxxvvnn'


def test_parse_entries_preserves_text_weight_and_extra_columns():
    sample = '''# source\n---\nname: wubi\nversion: "2.0"\nsort: by_weight\n...\n我\tq\t90788800\ttrny\n上\th\t90000000\thhgg\n词组\tabcd\t1234\n'''
    entries = list(parse_entries(sample))
    assert entries == [
        ['我', 'q', '90788800', 'trny'],
        ['上', 'h', '90000000', 'hhgg'],
        ['词组', 'abcd', '1234'],
    ]


def test_render_normal_changes_header_only_not_entry_columns():
    sample = '''---\nname: wubi\nversion: "2.0"\nsort: by_weight\n...\n我\tq\t90788800\ttrny\n'''
    out = render_dictionary(sample, name='ac_raincandy_wubi86', fold=False)
    assert 'name: ac_raincandy_wubi86' in out
    assert '\n我\tq\t90788800\ttrny\n' in out


def test_render_double_folds_only_code_column():
    sample = '''---\nname: wubi\nversion: "2.0"\nsort: by_weight\n...\n示例\twhtr\t42\twhtr\n'''
    out = render_dictionary(sample, name='ac_raincandy_wubi86_double', fold=True)
    assert '\n示例\tqgte\t42\twhtr\n' in out


def test_render_preserves_comments_and_blank_lines_in_body():
    sample = '''---\nname: wubi\nversion: "2.0"\nsort: by_weight\n...\n# comment\n\n我\tq\t1\n'''
    out = render_dictionary(sample, name='x', fold=True)
    assert '# comment\n\n我\tq\t1\n' in out
