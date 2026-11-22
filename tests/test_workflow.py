from datetime import date
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


lint = module('check_knowledge')
review = module('new_review')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'knowledge', self.root / 'knowledge')
        shutil.copytree(ROOT / 'reviews', self.root / 'reviews')

    def tearDown(self):
        self.temp.cleanup()

    def test_example_is_consistent(self):
        self.assertEqual(lint.check(self.root, date(2026, 1, 12)), ([], []))

    def test_broken_reference_fails(self):
        path = self.root / 'knowledge/05_open_issues.md'
        path.write_text(path.read_text() + '\n[broken](missing.md)\n', encoding='utf-8')
        self.assertTrue(any('リンク先がありません' in x for x in lint.check(self.root, date(2026, 1, 12))[0]))

    def test_duplicate_decision_fails(self):
        path = self.root / 'knowledge/08_ledger.md'
        path.write_text(path.read_text() + '\n| D-001 | 重複 | 根拠 | 条件 |\n', encoding='utf-8')
        self.assertTrue(any('ID重複' in x for x in lint.check(self.root, date(2026, 1, 12))[0]))

    def test_invalid_date_fails(self):
        path = self.root / 'knowledge/10_actuals.md'
        path.write_text(path.read_text().replace('2026-01-12', '2026-02-30'), encoding='utf-8')
        self.assertTrue(any('日が不正' in x for x in lint.check(self.root, date(2026, 3, 1))[0]))

    def test_reference_cannot_escape(self):
        path = self.root / 'knowledge/05_open_issues.md'
        path.write_text(path.read_text() + '\n[outside](../../outside.md)\n', encoding='utf-8')
        self.assertTrue(any('外を指して' in x for x in lint.check(self.root, date(2026, 1, 12))[0]))

    def test_iso_week_and_no_overwrite(self):
        target, created = review.create(self.root, date(2027, 1, 1))
        self.assertTrue(created)
        self.assertEqual(target.name, '2026-W53.md')
        target.write_text('keep existing notes', encoding='utf-8')
        self.assertFalse(review.create(self.root, date(2027, 1, 1))[1])
        self.assertEqual(target.read_text(), 'keep existing notes')


if __name__ == '__main__':
    unittest.main()
