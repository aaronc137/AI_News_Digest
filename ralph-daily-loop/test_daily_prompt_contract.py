import unittest

from style_contracts import build_prompt_trace, build_trend_translation


class DailyPromptContractTest(unittest.TestCase):
    def trace(self, trend):
        design = {"define": {"minimum_independent_score": 9}}
        translations = build_trend_translation({}, [trend], design)
        return build_prompt_trace({}, [trend], translations, design)[0]

    def test_legacy_input_requires_editorial_enrichment(self):
        trace = self.trace({"title": "Example", "desc": "A change"})
        contract = trace["daily_editorial_contract"]
        self.assertEqual(contract["input_status"], "needs_editorial_input")
        self.assertIsNone(contract["report_window"])
        self.assertEqual(contract["evidence"], [])
        self.assertFalse(contract["inherit_weekly_palette"])

    def test_preserves_supplied_facts_and_action(self):
        trend = {
            "title": "Example", "report_window": "2026-09-08/2026-09-09",
            "evidence": [{"news_id": "N1", "url": "https://example.org/news", "boundary": "trial only"}],
            "exact_text": {"title": "只改这里"}, "visual_action": "Replace one piece; retain its neighbors",
        }
        trace = self.trace(trend)
        contract = trace["daily_editorial_contract"]
        self.assertEqual(contract["evidence"], trend["evidence"])
        self.assertEqual(contract["exact_text"], trend["exact_text"])
        self.assertEqual(contract["input_status"], "ready_for_editorial_review")
        self.assertEqual(trace["components"]["subject_and_spatial_relation"], trend["visual_action"])
        self.assertIn("headline_hidden", contract["checks"])
        self.assertIn("story_substitution", contract["checks"])
        self.assertEqual(contract["text_budget"]["qualification_max_lines"], 1)

    def test_no_backend_keeps_previous_empty_behavior(self):
        self.assertEqual(build_prompt_trace({}, [], [], None), [])


if __name__ == "__main__":
    unittest.main()
