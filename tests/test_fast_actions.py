import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

from main import CONFIG, build_config_from_args


class FastActionsTests(unittest.TestCase):
    """CX_FAST_ACTIONS 与 --fast-actions 等价；默认关闭时不缩短任何等待。"""

    def build(self, fast_actions, argv=()):
        config = copy.deepcopy(CONFIG)
        config["fast_actions"] = fast_actions
        with mock.patch.object(sys, "argv", ["main.py", *argv]), redirect_stdout(io.StringIO()):
            return build_config_from_args(config)

    def test_env_flag_enables_fast_actions(self):
        config = self.build(True)
        self.assertEqual(config["delay_range_seconds"], (0.1, 0.3))
        self.assertEqual(config["slow_mo_ms"], 0)

    def test_cli_flag_still_enables_fast_actions(self):
        config = self.build(False, ["--fast-actions"])
        self.assertTrue(config["fast_actions"])
        self.assertEqual(config["delay_range_seconds"], (0.1, 0.3))

    def test_default_keeps_configured_delays(self):
        config = self.build(False)
        self.assertEqual(config["delay_range_seconds"], CONFIG["delay_range_seconds"])
        self.assertEqual(config["video_completion_settle_seconds"], CONFIG["video_completion_settle_seconds"])


if __name__ == "__main__":
    unittest.main()
