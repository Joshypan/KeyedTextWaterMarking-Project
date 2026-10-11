"""
Turns text into a clean list of words.
Gives each word a color from the secret key. word_color mixes the word with the 32-byte key using HMAC, and keeps one bit of the result
Scores a passage and decides whether to flag it.
"""
import hmac
import re
import secrets
import unicodedata
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

# word rules

_APOSTROPHES = {"\u2019": "'", "\u2018": "'", "\u02bc": "'"}  # right/left single quote, modifier apostrophe
_WORD_RE = re.compile(r"[^\W_]+(?:'[^\W_]+)*")


# text normalization
def normalize_text(text: str) -> str:
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    text = unicodedata.normalize("NFKC", text)
    for src, dst in _APOSTROPHES.items():
        text = text.replace(src, dst)
    return text

# tokenization: split into words, normalize, lowercase
def tokenize(text: str) -> list[str]:
    """Return the list of normalized words (with repeats) in `text`."""
    return [w.casefold() for w in _WORD_RE.findall(normalize_text(text))]

# detector
class EmptyInputError(ValueError):
    """Raised when the input contains no words after tokenization."""

# data class to hold the score of a passage
@dataclass(frozen=True)
class Score:
    total: int      # word occurrences
    distinct: int   # distinct normalized words
    green: int      # green word occurrences

    @property
    def fraction(self) -> float:
        return self.green / self.total
    # exceeds returns True if the fraction of green words exceeds the given threshold
    def exceeds(self, threshold) -> bool:
        return is_flagged(self.green, self.total, threshold)

