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
