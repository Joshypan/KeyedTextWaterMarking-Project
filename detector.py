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

# key management
def generate_key() -> bytes:
    return secrets.token_bytes(32)

# save/load key to/from file for use in word coloring
def save_key(path, key: bytes) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(key.hex() + "\n")

# load key from file for use in word coloring
def load_key(path) -> bytes:
    return bytes.fromhex(Path(path).read_text().strip())

# word coloring to determine if a word is green or red. returns 1 for green, 0 for red. `word` must already be normalized.
def word_color(word: str, key: bytes) -> int:
    """1 = green, 0 = red. `word` must already be normalized."""
    return hmac.digest(key, word.encode("utf-8"), "sha256")[-1] & 1

# score a passage
def score_text(text: str, key: bytes) -> Score:
    words = tokenize(text)
    if not words:
        raise EmptyInputError("input contains no words")
    counts = Counter(words)
    green = sum(c for w, c in counts.items() if word_color(w, key) == 1)
    return Score(total=len(words), distinct=len(counts), green=green)

# flagging for a given threshold.
def is_flagged(green: int, total: int, threshold) -> bool:
    """Flag only when green/total is strictly greater than threshold."""
    if total <= 0:
        raise EmptyInputError("total word count must be positive")
    return Fraction(green, total) > Fraction(str(threshold))