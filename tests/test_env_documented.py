"""防止 main.py 新增的 CX_* 配置项忘记写进 .env.example。

只扫真正的读取调用点（env_flag / env_int / env_float / os.getenv 的字面量参数），
不要用裸正则扫全文——那会把只出现在日志或 --help 文案里的名字也算成配置项。
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN_PATH = REPO_ROOT / "main.py"
EXAMPLE_PATH = REPO_ROOT / ".env.example"

READ_CALL = re.compile(r'(?:env_flag|env_int|env_float|os\.getenv)\(\s*"(CX_[A-Z0-9_]+)"')
DOCUMENTED = re.compile(r"^\s*#?\s*(CX_[A-Z0-9_]+)\s*=", re.MULTILINE)

# 这些选择器最容易随超星改版失效，必须在 .env.example 里留出可发现的逃生口。
REQUIRED_SELECTOR_OVERRIDES = {
    "CX_SELECTOR_CHAPTERS_TAB",
    "CX_SELECTOR_CHAPTER_ITEM",
    "CX_SELECTOR_CHAPTER_CATALOG_ITEM",
    "CX_SELECTOR_NEXT_CHAPTER",
    "CX_SELECTOR_NEXT_CONTROL",
    "CX_SELECTOR_VIDEO_PLAY_CONTROL",
    "CX_SELECTOR_LEARNING_CARD_TABS",
}


class EnvExampleDriftTests(unittest.TestCase):
    def setUp(self):
        self.main_source = MAIN_PATH.read_text(encoding="utf-8")
        self.example_source = EXAMPLE_PATH.read_text(encoding="utf-8")
        self.documented = set(DOCUMENTED.findall(self.example_source))

    def test_every_scalar_env_var_is_documented(self):
        read_names = set(READ_CALL.findall(self.main_source))
        self.assertTrue(read_names, "未能从 main.py 解析出任何 CX_* 读取点，正则可能失效了")
        missing = sorted(read_names - self.documented)
        self.assertEqual(
            missing,
            [],
            f".env.example 缺少这些 main.py 会读取的配置项: {missing}",
        )

    def test_fragile_selector_overrides_are_discoverable(self):
        missing = sorted(REQUIRED_SELECTOR_OVERRIDES - self.documented)
        self.assertEqual(
            missing,
            [],
            f".env.example 需要为易失效选择器保留可发现的覆盖入口: {missing}",
        )

    def test_example_does_not_document_unknown_vars(self):
        read_names = set(READ_CALL.findall(self.main_source))
        from main import CONFIG

        selector_names = {f"CX_SELECTOR_{key.upper()}" for key in CONFIG["selectors"]}
        unknown = sorted(self.documented - read_names - selector_names)
        self.assertEqual(
            unknown,
            [],
            f".env.example 记录了 main.py 并不读取的配置项（可能已改名或删除）: {unknown}",
        )


if __name__ == "__main__":
    unittest.main()
