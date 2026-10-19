import copy
import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from main import CONFIG, CourseAutoTester


class RedirectingPage:
    """模拟 sync API 下的登录跳转：page.url 是本地缓存，只有经过一次 Playwright 调用
    （这里是 wait_for_timeout）处理了导航事件之后才会更新；单纯反复读取或 time.sleep 都不会。"""

    def __init__(self, pumps_before_redirect):
        self.pumps_before_redirect = pumps_before_redirect
        self.pumps = 0

    @property
    def url(self):
        if self.pumps < self.pumps_before_redirect:
            return "https://passport2.chaoxing.com/login?fid=&newversion=true"
        return "https://i.chaoxing.com/base?t=0"

    def wait_for_timeout(self, timeout_ms):
        self.pumps += 1

    def is_closed(self):
        return False


class LoginCheckTests(unittest.TestCase):
    def make_tester(self, page, timeout_ms=8_000):
        config = copy.deepcopy(CONFIG)
        config["login_check_timeout_ms"] = timeout_ms
        config["selectors"]["login_success_marker"] = ""
        tester = CourseAutoTester(config)
        tester.page = page
        return tester

    def test_login_succeeds_when_redirect_lands_after_first_check(self):
        # 回归：实测中登录成功，但点击后第一次读 URL 仍在 passport，被误判成登录失败；
        # 第一版修复用 time.sleep 轮询缓存的 page.url，URL 永远不更新，同样误判。
        tester = self.make_tester(RedirectingPage(pumps_before_redirect=2))

        with (
            mock.patch("main.time.sleep"),
            mock.patch.object(tester, "save_debug_screenshot"),
            redirect_stdout(io.StringIO()),
        ):
            self.assertTrue(tester.login_succeeded())

    def test_login_fails_when_page_never_leaves_passport(self):
        tester = self.make_tester(RedirectingPage(pumps_before_redirect=10**9), timeout_ms=0)

        output = io.StringIO()
        with mock.patch.object(tester, "save_debug_screenshot") as screenshot, redirect_stdout(output):
            self.assertFalse(tester.login_succeeded())

        screenshot.assert_called_once_with("login_rejected")
        self.assertIn("判定登录失败", output.getvalue())


if __name__ == "__main__":
    unittest.main()
