import json
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package import package
class PackageTests(unittest.TestCase):
    def test_both_launcher_archives(self):
        for version in ('1.13','1.14'):
            with self.subTest(version=version),zipfile.ZipFile(package(version)) as archive:
                self.assertIsNone(archive.testzip())
                names=archive.namelist()
                self.assertFalse(any('/.git/' in name or '__pycache__' in name for name in names))
                self.assertIn('faith_and_intervention/events/fia_events.txt',names)
                self.assertIn('faith_and_intervention_docs/DESIGN.md',names)
                descriptor=archive.read('faith_and_intervention.mod').decode()
                self.assertIn('path="mod/faith_and_intervention"',descriptor)
                self.assertIn(f'supported_version="{version}.*"',descriptor)
                meta=json.loads(archive.read('faith_and_intervention/.metadata/metadata.json'))
                self.assertEqual(meta['supported_game_version'],f'{version}.*')
if __name__=='__main__':unittest.main()
