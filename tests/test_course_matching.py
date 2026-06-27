import copy
import unittest

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


if __name__ == "__main__":
    unittest.main()
