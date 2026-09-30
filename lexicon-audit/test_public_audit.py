import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import public_audit as pa


class ParserTests(unittest.TestCase):
    def test_rime_header_and_first_column(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.dict.yaml"
            p.write_text(
                "# comment\n---\nname: a\ncolumns:\n  - text\n  - code\n...\n工\ta\t10\n工具\taahw\t2\n# x\n\n",
                encoding="utf-8",
            )
            self.assertEqual(list(pa.iter_rime_entries(p)), ["工", "工具"])

    def test_no_header_plain_rows(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "plain.txt"
            p.write_text("词条\tabcd\n纯文本\n", encoding="utf-8")
            self.assertEqual(list(pa.iter_rime_entries(p)), ["词条", "纯文本"])

    def test_word_kind_and_buckets(self):
        self.assertEqual(pa.kind("中国"), "han_only")
        self.assertEqual(pa.kind("3D打印"), "mixed_han")
        self.assertEqual(pa.kind("DNA"), "ascii_only")
        self.assertEqual(pa.len_bucket(1), "1")
        self.assertEqual(pa.len_bucket(5), "5-6")
        self.assertEqual(pa.len_bucket(8), "7+")


if __name__ == "__main__":
    unittest.main()
