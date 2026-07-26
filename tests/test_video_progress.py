"""视频完成判定 / 停滞判定 / 轮询间隔的确定性测试。

这三块是整个工具风险最高的逻辑（判错就等于"没看却报完成"或"看完了却卡住"），
原先全内联在 wait_until_video_finished 的 while 循环里，要测就得伪造 7 个协作者
并真的 sleep，所以一直没有覆盖。抽成纯函数后可以直接断言。
"""
import copy
import io
import unittest
from contextlib import redirect_stdout

from playwright.sync_api import Error as PlaywrightError

from main import (
    CONFIG,
    CourseAutoTester,
    classify_completion_scan,
    next_poll_seconds,
    stall_epsilon_for,
    video_is_complete,
)


def state(current, duration, ended=False, paused=False, rate=1.0):
    return {
        "currentTime": current,
        "duration": duration,
        "ended": ended,
        "paused": paused,
        "playbackRate": rate,
    }


class VideoIsCompleteTests(unittest.TestCase):
    def test_ended_flag_wins_even_without_duration(self):
        self.assertTrue(video_is_complete(state(0.0, 0.0, ended=True), 0.8))

    def test_playing_midway_is_not_complete(self):
        self.assertFalse(video_is_complete(state(300.0, 600.0), 0.8))

    def test_near_end_but_still_playing_is_not_complete(self):
        self.assertFalse(video_is_complete(state(599.5, 600.0, paused=False), 0.8))

    def test_near_end_and_paused_counts_as_complete(self):
        self.assertTrue(video_is_complete(state(599.5, 600.0, paused=True), 0.8))

    def test_paused_early_is_not_complete(self):
        self.assertFalse(video_is_complete(state(10.0, 600.0, paused=True), 0.8))

    def test_unknown_duration_never_completes_on_position(self):
        self.assertFalse(video_is_complete(state(9999.0, 0.0, paused=True), 0.8))


class StallEpsilonTests(unittest.TestCase):
    def test_default_poll_uses_configured_epsilon(self):
        # 10 秒轮询 1.0 倍速：期望前进 10 秒，配置阈值 0.5 秒是更严格的那个。
        self.assertAlmostEqual(stall_epsilon_for(10.0, 1.0, 0.5), 0.5)

    def test_dense_poll_scales_threshold_down(self):
        # 0.5 秒轮询 1.0 倍速：期望前进恰好 0.5 秒。
        # 旧实现用绝对 0.5 比较，健康视频每轮都被判成停滞。
        eps = stall_epsilon_for(0.5, 1.0, 0.5)
        self.assertLess(eps, 0.5)
        healthy_advance = 0.5
        self.assertGreater(healthy_advance, eps, "健康视频的前进量必须大于停滞阈值")

    def test_throttled_playback_rate_scales_threshold_down(self):
        # 平台把倍速压到 0.5x，1 秒轮询只前进 0.5 秒，同样不能按绝对阈值判。
        eps = stall_epsilon_for(1.0, 0.5, 0.5)
        self.assertGreater(1.0 * 0.5, eps)

    def test_threshold_is_always_positive(self):
        self.assertGreater(stall_epsilon_for(0.0, 0.0, 0.0), 0.0)

    def test_genuinely_stalled_video_still_trips(self):
        eps = stall_epsilon_for(10.0, 1.0, 0.5)
        advance = 0.0
        self.assertLessEqual(advance, eps, "完全没前进必须仍然算停滞")


class HealthyVideoNeverStallsTests(unittest.TestCase):
    """回归：以健康视频模拟整段播放，断言一次误判都不会发生。"""

    def simulate(self, duration, rate, poll, min_poll=0.5, margin=0.8, epsilon=0.5, stall_limit=3):
        current = 0.0
        last_current = None
        stall_polls = 0
        last_sleep = poll
        false_recoveries = 0
        for _ in range(100000):
            snapshot = state(current, duration, ended=current >= duration,
                             paused=current >= duration, rate=rate)
            if video_is_complete(snapshot, margin):
                return false_recoveries
            eps = stall_epsilon_for(last_sleep, rate, epsilon)
            if last_current is not None and current <= last_current + eps:
                stall_polls += 1
            else:
                stall_polls = 0
            last_current = current
            if stall_polls >= stall_limit:
                false_recoveries += 1
                stall_polls = 0
            sleep = next_poll_seconds(snapshot, poll, min_poll, margin)
            last_sleep = sleep
            current = min(duration, current + sleep * rate)
        self.fail("模拟未收敛")

    def test_no_false_recovery_across_poll_intervals(self):
        for poll in (10.0, 5.0, 3.0, 1.0, 0.5, 0.2, 0.1):
            with self.subTest(poll=poll):
                self.assertEqual(
                    self.simulate(600.0, 1.0, poll), 0,
                    f"--progress-poll-seconds {poll} 下健康视频被误判为停滞",
                )

    def test_no_false_recovery_when_platform_throttles_rate(self):
        for rate in (1.0, 0.5, 0.25):
            with self.subTest(rate=rate):
                self.assertEqual(
                    self.simulate(600.0, rate, 1.0), 0,
                    f"倍速 {rate} 下健康视频被误判为停滞",
                )


class NextPollSecondsTests(unittest.TestCase):
    def test_far_from_end_uses_full_poll(self):
        self.assertAlmostEqual(next_poll_seconds(state(10.0, 600.0), 10.0, 0.5, 0.8), 10.0)

    def test_near_end_shortens_but_respects_minimum(self):
        result = next_poll_seconds(state(599.9, 600.0), 10.0, 0.5, 0.8)
        self.assertAlmostEqual(result, 0.5)

    def test_unknown_duration_falls_back_to_full_poll(self):
        self.assertAlmostEqual(next_poll_seconds(state(5.0, 0.0), 10.0, 0.5, 0.8), 10.0)

    def test_zero_rate_falls_back_to_full_poll(self):
        self.assertAlmostEqual(next_poll_seconds(state(5.0, 600.0, rate=0.0), 10.0, 0.5, 0.8), 10.0)

    def test_double_rate_halves_the_estimate(self):
        slow = next_poll_seconds(state(590.0, 600.0, rate=1.0), 10.0, 0.1, 0.8)
        fast = next_poll_seconds(state(590.0, 600.0, rate=2.0), 10.0, 0.1, 0.8)
        self.assertLess(fast, slow)


class OpenPage:
    """未关闭的假页面，只满足 page_is_available 的检查。"""

    def __init__(self, url="https://mooc1.chaoxing.com/mycourse/studentstudy?courseid=x"):
        self.url = url

    def is_closed(self):
        return False


class FakeVideo:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<FakeVideo {self.name}>"


class CurrentVideoLocatorTests(unittest.TestCase):
    """回归：video_index 明确给出时，绝不能回退到页面上的第一个 <video>。

    回退会让第 2 个及以后的视频读到第 1 个（已 ended）的状态，
    从而被判成"已播放完成"而静默跳过——没看却报成功。
    """

    def make_tester(self):
        tester = CourseAutoTester(copy.deepcopy(CONFIG))
        tester.page = OpenPage()
        return tester

    def test_uses_the_indexed_video_when_enumeration_is_complete(self):
        tester = self.make_tester()
        first, second = FakeVideo("first"), FakeVideo("second")
        tester.video_locators = lambda: [first, second]

        with redirect_stdout(io.StringIO()):
            result = tester.current_video_locator(second, 1)

        self.assertIs(result, second)

    def test_short_enumeration_keeps_caller_locator_instead_of_first_video(self):
        tester = self.make_tester()
        first, second = FakeVideo("first"), FakeVideo("second")
        # 播放器 iframe 重载时枚举会短一个。
        tester.video_locators = lambda: [first]
        tester.video_locator = lambda: first

        output = io.StringIO()
        with redirect_stdout(output):
            result = tester.current_video_locator(second, 1)

        self.assertIsNot(result, first, "index=1 时绝不能回退到第一个 video")
        self.assertIs(result, second)
        self.assertIn("枚举数", output.getvalue())

    def test_no_index_may_still_fall_back_to_first_video(self):
        tester = self.make_tester()
        first = FakeVideo("first")
        tester.video_locators = lambda: []
        tester.video_locator = lambda: first

        with redirect_stdout(io.StringIO()):
            result = tester.current_video_locator(None, None)

        self.assertIs(result, first)


class CompletionScanTests(unittest.TestCase):
    def test_none_is_unreadable_not_complete(self):
        # 最关键的一条：读不到 != 已完成。
        self.assertEqual(classify_completion_scan(None), "unreadable")

    def test_signals_mean_incomplete(self):
        self.assertEqual(classify_completion_scan(["frame#0: 页面仍有未完成标记: 1"]), "incomplete")

    def test_empty_list_means_clear(self):
        self.assertEqual(classify_completion_scan([]), "clear")


class ScanningPage(OpenPage):
    """可控的假页面：evaluate 要么抛错，要么返回给定结果。"""

    def __init__(self, result=None, raises=False):
        super().__init__()
        self._result = result if result is not None else []
        self._raises = raises
        self.frames = []
        self.main_frame = self

    def evaluate(self, script, *args):
        if self._raises:
            raise PlaywrightError("Execution context was destroyed")
        return self._result


class IncompleteSignalsFailClosedTests(unittest.TestCase):
    """回归：完成状态扫描是唯一挡住"误判完课"的防线，读不到时必须 fail-closed。

    旧实现把"每个容器都读失败"和"读到了但没有未完成标记"都返回成空列表，
    于是选择器失配 / iframe 未 attach 会被当成"课程已完成"并以退出码 0 结束。
    """

    def make_tester(self, page):
        tester = CourseAutoTester(copy.deepcopy(CONFIG))
        tester.page = page
        return tester

    def test_returns_none_when_no_container_can_be_read(self):
        tester = self.make_tester(ScanningPage(raises=True))

        with redirect_stdout(io.StringIO()):
            result = tester.incomplete_learning_signals()

        self.assertIsNone(result, "一个容器都读不到时必须返回 None，不能返回空列表")
        self.assertEqual(classify_completion_scan(result), "unreadable")

    def test_returns_empty_list_when_page_is_readable_and_clean(self):
        tester = self.make_tester(ScanningPage(result=[]))

        with redirect_stdout(io.StringIO()):
            result = tester.incomplete_learning_signals()

        self.assertEqual(result, [])
        self.assertEqual(classify_completion_scan(result), "clear")

    def test_returns_signals_when_page_reports_incomplete(self):
        tester = self.make_tester(ScanningPage(result=["页面仍有未完成标记: 1"]))

        with redirect_stdout(io.StringIO()):
            result = tester.incomplete_learning_signals()

        self.assertEqual(classify_completion_scan(result), "incomplete")


if __name__ == "__main__":
    unittest.main()
