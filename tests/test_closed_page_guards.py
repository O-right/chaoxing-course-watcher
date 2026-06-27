import copy
import io
import unittest
from contextlib import redirect_stdout

from main import CONFIG, CourseAutoTester


class ClosedPage:
    def __init__(self, url="https://mooc1.chaoxing.com/mycourse/studentstudy"):
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


if __name__ == "__main__":
    unittest.main()