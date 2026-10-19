import copy
import io
import unittest
from contextlib import redirect_stdout

from main import CONFIG, CourseAutoTester


class CourseMatchingTests(unittest.TestCase):
    def make_tester(self):
        config = copy.deepcopy(CONFIG)
        config["course_match_min_score"] = 0.72
        config["course_match_ambiguous_delta"] = 0.06
        return CourseAutoTester(config)

    def test_keyword_terms_expand_quotes_and_suffixes(self):
        tester = self.make_tester()

        terms = tester.course_keyword_terms("“四史”专题课")

        self.assertIn("“四史”专题课", terms)
        self.assertIn("四史专题课", terms)
        self.assertIn("四史", terms)
        self.assertIn("四史专题", terms)

    def test_exact_title_beats_shorter_contains_match(self):
        tester = self.make_tester()
        terms = tester.course_keyword_terms("2025-2026(2) 物理学")
        candidates = [
            {"text": "物理学", "source": "course link"},
            {"text": "2025-2026(2) 物理学", "source": "course link"},
        ]

        best, ranked, status = tester.select_best_course_candidate(terms, candidates)

        self.assertEqual(status, "matched")
        self.assertEqual(best["text"], "2025-2026(2) 物理学")
        self.assertEqual(best["match_reason"], "exact")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_suffix_variant_matches_course_without_original_suffix(self):
        tester = self.make_tester()
        terms = tester.course_keyword_terms("“四史”专题课")
        candidates = [
            {"text": "大学生安全教育", "source": "course link"},
            {"text": "四史专题课", "source": "course link"},
        ]

        best, _, status = tester.select_best_course_candidate(terms, candidates)

        self.assertEqual(status, "matched")
        self.assertEqual(best["text"], "四史专题课")
        self.assertEqual(best["match_reason"], "exact")

    def test_short_keyword_with_close_candidates_is_ambiguous(self):
        tester = self.make_tester()
        terms = tester.course_keyword_terms("物理学")
        candidates = [
            {"text": "2025-2026(2) 物理学", "source": "course link"},
            {"text": "大学物理学实验", "source": "course link"},
        ]

        best, ranked, status = tester.select_best_course_candidate(terms, candidates)

        self.assertIsNone(best)
        self.assertEqual(status, "ambiguous")
        self.assertEqual(len(ranked), 2)

    def test_low_similarity_candidate_is_rejected(self):
        tester = self.make_tester()
        terms = tester.course_keyword_terms("高等数学")
        candidates = [
            {"text": "大学英语", "source": "course link"},
            {"text": "体育健康", "source": "course link"},
        ]

        best, ranked, status = tester.select_best_course_candidate(terms, candidates)

        self.assertIsNone(best)
        self.assertEqual(ranked, [])
        self.assertEqual(status, "no_match")

    def test_missing_middle_character_still_matches_history_course(self):
        tester = self.make_tester()
        terms = tester.course_keyword_terms("中国现代史纲要")
        candidates = [
            {"text": "马克思主义基本原理", "source": "course link"},
            {"text": "中国近现代史纲要", "source": "course link"},
        ]

        best, _, status = tester.select_best_course_candidate(terms, candidates)

        self.assertEqual(status, "matched")
        self.assertEqual(best["text"], "中国近现代史纲要")
        self.assertEqual(best["match_reason"], "similarity")
        self.assertGreaterEqual(best["score"], 0.8)

    def test_same_card_elements_sharing_href_are_not_ambiguous(self):
        # 同一张课程卡的 <a> 和包着它的 <h3> 分数相同，按 href 归组后不能算歧义。
        tester = self.make_tester()
        terms = tester.course_keyword_terms("药物发现的故事和启示")
        candidates = [
            {"text": "药物发现的故事和启示", "href": "https://mooc1.example.test/course/1", "tag": "A"},
            {"text": "药物发现的故事和启示", "href": "https://mooc1.example.test/course/1", "tag": "H3"},
        ]

        best, ranked, status = tester.select_best_course_candidate(terms, candidates)

        self.assertEqual(status, "matched")
        self.assertEqual(best["href"], "https://mooc1.example.test/course/1")
        self.assertEqual(len(ranked), 1)

    def test_same_named_courses_with_different_links_stay_ambiguous(self):
        # 课程列表里真实存在两张同名卡片（不同班级），绝不能随便点一张。
        tester = self.make_tester()
        terms = tester.course_keyword_terms("马克思主义基本原理")
        candidates = [
            {"text": "马克思主义基本原理", "href": "https://mooc1.example.test/course/2"},
            {"text": "马克思主义基本原理", "href": "https://mooc1.example.test/course/3"},
        ]

        best, ranked, status = tester.select_best_course_candidate(terms, candidates)

        self.assertIsNone(best)
        self.assertEqual(status, "ambiguous")
        self.assertEqual(len(ranked), 2)

    def test_href_less_duplicate_is_still_ambiguous_without_card_href(self):
        # Python 侧不按文本合并：拿不到卡片链接的同名元素宁可报歧义，也不猜它属于哪张卡。
        tester = self.make_tester()
        terms = tester.course_keyword_terms("药物发现的故事和启示")
        candidates = [
            {"text": "药物发现的故事和启示", "href": "https://mooc1.example.test/course/1"},
            {"text": "药物发现的故事和启示", "href": ""},
        ]

        best, _, status = tester.select_best_course_candidate(terms, candidates)

        self.assertIsNone(best)
        self.assertEqual(status, "ambiguous")

    def test_missing_course_keyword_and_url_fails_fast(self):
        tester = self.make_tester()
        tester.config["course_keyword"] = ""
        tester.config["course_url"] = ""
        tester.page = object()

        output = io.StringIO()
        with redirect_stdout(output):
            result = tester.open_course()

        self.assertFalse(result)
        self.assertIn("CX_COURSE_KEYWORD", output.getvalue())
        self.assertIn("CX_COURSE_URL", output.getvalue())


if __name__ == "__main__":
    unittest.main()
