import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from clausewitz import parse
from validate import validate
class RepositoryTests(unittest.TestCase):
    def test_static_validation(self):self.assertIn('PASS',validate())
    def test_parser_rejects_truncated_and_unbalanced_input(self):
        for source in ('x = { y = 1','x =','x = { y = }','}'):
            with self.subTest(source=source), self.assertRaises(ValueError):parse(source)
    def test_parser_preserves_repeated_options_and_bare_flags(self):
        tree=parse('x = { option = { name = a } option = { name = b } flags = { requires_interest } }')
        self.assertEqual([e.key for e in tree[0].value],['option','option','flags'])
if __name__=='__main__':unittest.main()
