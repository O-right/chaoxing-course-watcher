import copy
import io
import unittest
from contextlib import redirect_stdout

from main import CONFIG, CourseAutoTester, redact_url_for_log, redact_urls_in_text


class ClosedPage:
    def __init__(
        self,
        url="https://mooc1.chaoxing.com/mycourse/studentstudy?courseid=private-course&clazzid=private-class",
    ):
        self.url = url
        self.locator_called = False
        self.screenshot_called = False

    def is_closed(self):
        return True

    def locator(self, selector):
        self.locator_called = True
        raise AssertionError("closed pages must not be queried for locators")

    def screenshot(self, **kwargs):
        self.screenshot_called = True
        raise AssertionError("closed pages must not be screenshotted")


class StaleVideo:
    def __init__(self):
        self.evaluate_called = False

    def evaluate(self, script):
        self.evaluate_called = True
        raise AssertionError("stale video locators must not be evaluated after page close")


class ClosedPageGuardTests(unittest.TestCase):
    def make_tester(self):
        config = copy.deepcopy(CONFIG)
        config["lookup_timeout_ms"] = 1
        return CourseAutoTester(config)

    def test_save_debug_screenshot_skips_closed_page(self):
        tester = self.make_tester()
        page = ClosedPage()
        tester.page = page

        output = io.StringIO()
        with redirect_stdout(output):
            tester.save_debug_screenshot("video_wait_failed_inline_6")
            tester.save_debug_screenshot("learning_unit_failed_1")

        self.assertFalse(page.screenshot_called)
        self.assertEqual(output.getvalue().count("浏览器页面已关闭"), 1)
        self.assertNotIn("private-course", output.getvalue())
        self.assertNotIn("private-class", output.getvalue())
        self.assertIn("https://mooc1.chaoxing.com/<redacted>", output.getvalue())

    def test_find_locator_returns_none_without_querying_closed_page(self):
        tester = self.make_tester()
        page = ClosedPage()
        tester.page = page

        with redirect_stdout(io.StringIO()):
            result = tester.find_locator_in_page_or_frames("video", "video 元素")

        self.assertIsNone(result)
        self.assertFalse(page.locator_called)

    def test_read_video_state_does_not_evaluate_stale_video_after_page_close(self):
        tester = self.make_tester()
        tester.page = ClosedPage()
        stale_video = StaleVideo()

        with redirect_stdout(io.StringIO()):
            result = tester.read_video_state(stale_video, video_index=None)

        self.assertIsNone(result)
        self.assertFalse(stale_video.evaluate_called)


class LogRedactionTests(unittest.TestCase):
    def test_redact_url_for_log_removes_path_query_and_fragment(self):
        result = redact_url_for_log(
            "https://mooc1.chaoxing.com/mycourse/studentstudy?courseid=private#chapter"
        )

        self.assertEqual(result, "https://mooc1.chaoxing.com/<redacted>")

    def test_redact_url_for_log_removes_embedded_userinfo(self):
        result = redact_url_for_log(
            "https://private-user:private-password@mooc1.chaoxing.com:443/course"
        )

        self.assertEqual(result, "https://mooc1.chaoxing.com:443/<redacted>")

    def test_redact_urls_in_text_sanitizes_navigation_error(self):
        result = redact_urls_in_text(
            "Page.goto failed for https://mooc1.chaoxing.com/course?clazzid=private-class"
        )

        self.assertEqual(
            result,
            "Page.goto failed for https://mooc1.chaoxing.com/<redacted>",
        )

    def test_redact_urls_in_text_sanitizes_websocket_endpoint(self):
        result = redact_urls_in_text(
            "Browser endpoint wss://private-user:private-password@browser.example/ws?token=private"
        )

        self.assertEqual(result, "Browser endpoint wss://browser.example/<redacted>")


if __name__ == "__main__":
    unittest.main()
