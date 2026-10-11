import hmac
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

#import the functions and classes from detector.py
from detector import (EmptyInputError, generate_key, is_flagged, normalize_text,
                score_text, tokenize, word_color)

KEY = bytes(range(32))  # fixed test key, ONLY for test!!

# find n words of a given color using the test key. returns a list of words.
def find_words(color, n, key=KEY):
    out, i = [], 0
    while len(out) < n:
        w = f"w{i}"
        if word_color(w, key) == color:
            out.append(w)
        i += 1
    return out


class TextRules(unittest.TestCase):
    # test that the normalization and tokenization rules are applied
    def test_case(self):
        self.assertEqual(tokenize("Book book BOOK"), ["book"] * 3)

    # test that punctuation and apostrophes are handled
    def test_punctuation_and_apostrophe(self):
        self.assertEqual(tokenize("Don't stop, well-known!"),
                         ["don't", "stop", "well", "known"])
        self.assertEqual(tokenize("don’t"), ["don't"])

    # test that zero-width and other invisible characters are removed
    def test_zero_width_removed(self):
        self.assertEqual(tokenize("he​llo wor‍ld﻿"),
                         ["hello", "world"])

    # test that unicode normalization is applied
    def test_unicode_nfkc(self):
        self.assertEqual(tokenize("Ｈｉ"), ["hi"])  # full-width Hi

    # test that homoglyphs are treated as different words
    def test_homoglyph_is_a_different_word(self):
        self.assertNotEqual(tokenize("cat"), tokenize("cаt"))  # Cyrillic a

    # test that normalization is applyed twice and gives the same result
    def test_normalize_idempotent(self):
        s = "Café​ ’x’"
        self.assertEqual(normalize_text(normalize_text(s)), normalize_text(s))


class Color(unittest.TestCase):
    # test that the word_color function matches the formula
    def test_matches_spec_formula(self):
        for w in ["apple", "banana", "the"]:
            expect = hmac.digest(KEY, w.encode(), "sha256")[-1] & 1
            self.assertEqual(word_color(w, KEY), expect)

    # test that the word_color function is deterministic and returns a binary value
    def test_deterministic_and_binary(self):
        self.assertEqual(word_color("x", KEY), word_color("x", KEY))
        self.assertIn(word_color("x", KEY), (0, 1))

    # test that the word_color function returns different colors for different words
    def test_key_changes_colors(self):
        other = generate_key()
        words = [f"w{i}" for i in range(200)]
        diff = sum(word_color(w, KEY) != word_color(w, other) for w in words)
        self.assertGreater(diff, 40)


class Scoring(unittest.TestCase):
    # test that the score_text function returns the correct counts and fraction
    def test_counts_and_repeats(self):
        g, r = find_words(1, 1)[0], find_words(0, 1)[0]
        s = score_text(f"{g} {g} {g} {r}", KEY)
        self.assertEqual((s.total, s.distinct, s.green), (4, 2, 3))
        self.assertAlmostEqual(s.fraction, 0.75)

    # test that repeated words score 0 or 1
    def test_repeated_word_scores_0_or_1(self):
        g, r = find_words(1, 1)[0], find_words(0, 1)[0]
        self.assertEqual(score_text((g + " ") * 1000, KEY).fraction, 1.0)
        self.assertEqual(score_text((r + " ") * 1000, KEY).fraction, 0.0)

    # test that an empty input raises EmptyInputError
    def test_empty_raises(self):
        for bad in ["", "   \n", "!!! ... ---", "​‍"]:
            with self.assertRaises(EmptyInputError):
                score_text(bad, KEY)

    # test that the exceeds method returns True if the fraction of green words exceeds the given threshold
    def test_threshold_strict(self):
        self.assertTrue(is_flagged(65, 100, 0.60))
        self.assertFalse(is_flagged(60, 100, 0.60))   # equal -> unflagged
        self.assertFalse(is_flagged(58, 100, 0.60))
        self.assertTrue(is_flagged(61, 100, 0.60))
        self.assertFalse(is_flagged(11, 20, 0.55))    # 0.55 exactly
        self.assertTrue(is_flagged(12, 20, 0.55))

    # test that the exceeds method returns True if the fraction of green words exceeds the given threshold
    def test_end_to_end_flag(self):
        greens = find_words(1, 65)
        reds = find_words(0, 35)
        text = " ".join(greens + reds)
        s = score_text(text, KEY)
        self.assertEqual((s.green, s.total), (65, 100))
        self.assertTrue(s.exceeds(0.60))


if __name__ == "__main__":
    unittest.main()
