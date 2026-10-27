import unittest
from conversation_processor import (
    clean_text, split_statements, remove_exact_duplicates, chunk_statements,
    detect_corrections, compress_conversation,
)

SAMPLE = """The meeting is scheduled for Thursday.
I checked the official calendar.
The meeting is scheduled for Friday, not Thursday.
We need to finish the presentation slides by Monday.
The meeting is scheduled for Thursday."""

class ProcessorTests(unittest.TestCase):
    def test_cleaning(self):
        self.assertEqual(clean_text("  Hello   world\r\n\r\n"), "Hello world")
    def test_split(self):
        self.assertEqual(split_statements("One thing. Two things!"), ["One thing.", "Two things!"])
    def test_exact_duplicates(self):
        kept, count = remove_exact_duplicates(["Hello.", "hello", "World."])
        self.assertEqual(count, 1)
        self.assertEqual(len(kept), 2)
    def test_correction_detected(self):
        events = detect_corrections(split_statements(SAMPLE))
        self.assertTrue(any("Friday" in e["newer_statement"] for e in events))
    def test_summary_keeps_correction_once(self):
        result = compress_conversation(SAMPLE)
        self.assertEqual(result["duplicates_removed"], 1)
        self.assertIn("Earlier statement:", result["compressed_text"])
        self.assertEqual(result["compressed_text"].count("Friday, not Thursday"), 1)
    def test_chunking(self):
        chunks = chunk_statements(["one two", "three four", "five six"], 3)
        self.assertEqual(len(chunks), 3)
    def test_empty_input(self):
        result = compress_conversation("")
        self.assertEqual(result["original_words"], 0)
        self.assertEqual(result["compressed_text"], "")

if __name__ == "__main__":
    unittest.main()
