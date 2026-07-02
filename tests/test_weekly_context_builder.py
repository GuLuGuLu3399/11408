import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "weekly-context-builder.py"


def load_module():
    spec = importlib.util.spec_from_file_location("weekly_context_builder", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WeeklyContextBuilderTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "408").mkdir(parents=True)
        (self.root / "docs" / "408" / "系统调用.md").write_text("# 系统调用\n", encoding="utf-8")
        (self.root / "docs" / "408" / "内存管理.md").write_text("# 内存管理\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_report_focuses_on_current_docs_notes_not_migration_noise(self):
        activity = {
            "commits": [("abc1234", "2026-06-30T08:00:00+08:00", "notes: update syscall")],
            "files": {
                "408/内存管理.md": {"added": 120, "deleted": 40, "ops": {"A", "M"}, "commits": 1},
                "docs/408/内存管理.md": {"added": 0, "deleted": 0, "ops": {"R"}, "commits": 1},
                "docs/408/系统调用.md": {"added": 20, "deleted": 2, "ops": {"M"}, "commits": 1},
                "rag-hook-test.md": {"added": 1, "deleted": 1, "ops": {"D"}, "commits": 1},
            },
        }

        markdown = self.module.build_markdown(self.root, "main", 7, activity)

        self.assertIn("docs/408/系统调用.md", markdown)
        self.assertNotIn("408/内存管理.md` · +120", markdown)
        self.assertNotIn("docs/408/内存管理.md` · +0", markdown)
        self.assertIn("结构迁移/非当前笔记改动", markdown)
        self.assertIn("被降噪", markdown)


if __name__ == "__main__":
    unittest.main()
