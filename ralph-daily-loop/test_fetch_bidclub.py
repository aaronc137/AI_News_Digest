import unittest
from datetime import datetime, timezone

from fetch_bidclub import compact_markdown, is_recent, make_record, parse_timestamp


class BidClubScannerTest(unittest.TestCase):
    def test_parse_timestamp_normalizes_zulu_time(self):
        parsed = parse_timestamp("2026-09-10T20:15:44+00:00")
        self.assertEqual(parsed, datetime(2026, 9, 10, 20, 15, 44, tzinfo=timezone.utc))

    def test_date_only_episode_is_recent_for_today(self):
        self.assertTrue(
            is_recent(
                {"date": "2026-09-11"},
                datetime(2026, 9, 10, tzinfo=timezone.utc),
                datetime(2026, 9, 11, tzinfo=timezone.utc).date(),
            )
        )

    def test_record_preserves_original_and_bidclub_links(self):
        record = make_record(
            {
                "slug": "sample-episode",
                "title": "Sample episode",
                "dek": "A compact description.",
                "date": "2026-09-11",
                "published_at": "2026-09-11T00:00:00Z",
                "source_url": "https://example.com/original",
                "shows": {"name": "Sample Show"},
            },
            {"tldr_md": "- **Core thesis**: evidence-backed summary."},
        )
        self.assertEqual(record["board"], "海外建设者")
        self.assertEqual(record["url"], "https://example.com/original")
        self.assertEqual(record["bidclub_url"], "https://bidclub.ai/e/sample-episode")
        self.assertIn("evidence-backed summary", record["podcast_evidence_excerpt"])

    def test_compact_markdown_removes_formatting_without_expanding_text(self):
        text = compact_markdown("### Title\n- **A** claim with [source](https://example.com)")
        self.assertEqual(text, "Title A claim with source")


if __name__ == "__main__":
    unittest.main()
