"""用真实浏览器引擎跑课程卡片候选收集的 JS。

既没有 Playwright 自带 Chromium 也没有系统 Chrome 时整组跳过。
GitHub 的 windows-latest runner 预装 Chrome，所以 CI 上这组会真实运行。
夹具结构取自实测的课程列表：div.course > div.course-info > h3.inlineBlock > a.color1。
"""

import copy
import io
import unittest
from contextlib import redirect_stdout

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from main import CONFIG, CourseAutoTester


COURSE_LIST_HTML = """
<html><body>
<div class="courselistArea"><div class="course-list"><div>
  <div class="course clearfix learnCourse">
    <a class="course-cover" href="https://mooc1.example.test/course/1"
       style="display:block;width:240px;height:120px">cover</a>
    <div class="course-info">
      <h3 class="inlineBlock"><a class="color1" href="https://mooc1.example.test/course/1">药物发现的故事和启示</a></h3>
    </div>
    <div class="course-menu"><a href="javascript:;">移动到</a><a href="javascript:;">退课</a></div>
  </div>
  <div class="course clearfix learnCourse">
    <div class="course-info">
      <h3 class="inlineBlock"><a class="color1" href="https://mooc1.example.test/course/2">马克思主义基本原理</a></h3>
    </div>
  </div>
  <div class="course clearfix learnCourse">
    <div class="course-info">
      <h3 class="inlineBlock"><a class="color1" href="https://mooc1.example.test/course/3">马克思主义基本原理</a></h3>
    </div>
  </div>
  <div class="course clearfix learnCourse">
    <div class="course-info">
      <span class="course-title">人体机能学</span>
      <a href="https://mooc1.example.test/course/4">进入</a>
      <a href="https://mooc1.example.test/teacher/9">教师主页</a>
    </div>
  </div>
</div></div></div>
</body></html>
"""


class CourseCardDomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = None
        for options in ({}, {"channel": "chrome"}):
            try:
                cls.browser = cls.playwright.chromium.launch(**options)
                break
            except PlaywrightError:
                continue
        if cls.browser is None:
            cls.playwright.stop()
            raise unittest.SkipTest("本机没有可用的 Chromium / Chrome，跳过 DOM 夹具测试。")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.page.set_content(COURSE_LIST_HTML)
        config = copy.deepcopy(CONFIG)
        self.tester = CourseAutoTester(config)
        self.tester.page = self.page

    def tearDown(self):
        self.page.close()

    def select(self, keyword):
        terms = self.tester.course_keyword_terms(keyword)
        with redirect_stdout(io.StringIO()):
            candidates = self.tester.collect_course_candidates(terms)
        return self.tester.select_best_course_candidate(terms, candidates)

    def test_title_wrapper_and_link_of_one_card_resolve_to_single_match(self):
        # 回归：实测中 <h3> 拿不到 href，和同卡的 <a> 同分，同一门课被判成歧义。
        best, _, status = self.select("药物发现的故事和启示")

        self.assertEqual(status, "matched")
        self.assertEqual(best["href"], "https://mooc1.example.test/course/1")

    def test_two_cards_with_same_name_remain_ambiguous(self):
        best, ranked, status = self.select("马克思主义基本原理")

        self.assertIsNone(best)
        self.assertEqual(status, "ambiguous")
        self.assertEqual(
            {item["href"] for item in ranked[:2]},
            {"https://mooc1.example.test/course/2", "https://mooc1.example.test/course/3"},
        )

    def test_unlinked_title_in_multi_link_card_gets_no_guessed_href(self):
        title = self.page.locator(".course-title")

        details = self.tester.course_candidate_details(title)

        self.assertEqual(details["href"], "")


if __name__ == "__main__":
    unittest.main()
