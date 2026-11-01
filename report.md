# Keyed Text Watermarking: Detector, Evaluation and Threat Model

Joshua Panchana Cedeno - Milestone 1 - October 2026

## 1. Scheme and detector

My detector normalizes text by removing invisible format characters (Unicode Cf), applying NFKC and turning curly apostrophes into `'`. It then splits the text into words of letters and digits and casefolds them, so "Book" and "book" are the same word. Punctuation is dropped, except that inner apostrophes stay, so "don't" is one word; hyphens split words, so "well-known" is two. Similar letters from other alphabets are not mapped back, so they form different words. Each word's color is the last bit of `HMAC-SHA256(key, word)` under one random 32-byte key: 1 is green, 0 is red. A passage's score is its green fraction, counting every occurrence, and it is flagged only when that fraction is strictly greater than the threshold, compared as exact fractions, so a score equal to the threshold is not flagged. The detector also records total and distinct word counts, and text with no words raises an explicit `EmptyInputError` instead of returning a score. A flag shows a match to the keyed signal, but not who wrote the text.

## 2. Data

I collected 315 distinct passages from 8 public-domain Project Gutenberg books. `prepare_text.py` strips the Gutenberg header and footer, footnotes and transcriber's notes, then cuts nonoverlapping runs of whole sentences into three length groups.

| Set | Books (source documents) | Unmarked (30–99 / 100–199 / 200–400 words) | Watermarking |
|---|---|---|---|
| Calibration | Pride and Prejudice, Dracula, Moby Dick, The Prince (4) | 150 (50 / 50 / 50) | 5 |
| Evaluation | Gulliver's Travels, The Jungle Book, The Odyssey, Sherlock Holmes (4) | 150 (50 / 50 / 50) | 10 |

Whole books were assigned to one set with `random.Random(20261009)`. Before any score existed, I chose the 5 query access forgery passages (`eva_wm_01, 03, 06, 07, 10`) with `random.Random(7)`. Each passage's source and total and distinct word counts are in `data/manifest.csv`.

## 3. Calibration and frozen settings

I generated one random key and never replaced it. The 150 unmarked calibration passages averaged 0.429 green (maximum 0.596), below 0.5, because under my key the most common words ("the", "and", "of", "to", "it", "I", "you") are all red. With six throwaway keys the average ranged from 0.44 to 0.54, so the baseline depends on the key.

I then practiced on the 5 calibration passages. The edits were made with the following procedure:

1. Copy the original to `data/watermarked/<id>/v01.txt` and run `evaluate.py score`, which prints the green fraction and the red words.
2. Replace red words with synonyms that keep the meaning, after scoring each candidate to make sure it is green.
3. Because the most frequent words are red and have no synonyms, reword phrases to need fewer of them, for example "as well as" instead of "and", or "upon" and "with" instead of "of" and "to".
4. Save each attempt as a new version, score it, and stop as soon as it reaches the target. The chosen version becomes `final.txt`.

My own first attempt at `cal_wm_01` lowered its score from 68 to 67 green words, because I also swapped green words. Only red words should change, and only to green replacements.

| Passage | Book | Target | Before | After | Changed words | Meaning | Readable |
|---|---|---|---|---|---|---|---|
| `cal_wm_01` | austen | 0.75 | 0.456 | 0.768 | 82 / 149 | yes | yes |
| `cal_wm_02` | dracula | 0.75 | 0.419 | 0.801 | 123 / 174 | yes | yes |
| `cal_wm_03` | moby_dick | 0.75 | 0.422 | 0.781 | 115 / 180 | yes | yes |
| `cal_wm_04` | prince | 0.70 | 0.434 | 0.703 | 117 / 198 | yes | yes |
| `cal_wm_05` | austen | 0.70 | 0.424 | 0.703 | 53 / 132 | yes | yes |

At my first target of 0.75 all five passages reached it, but two failed the quality check. `cal_wm_04` had ungrammatical phrases, and `cal_wm_05` changed the meaning of a sentence about Persuasion. Using only these calibration results, I lowered the target to 0.70, and redid both from their originals. They then passed, and `cal_wm_04` needed 117 changed words instead of 161. Practice edits changed 40–71% of the words. I measured effort by changed words and did not record time.


| Threshold | Flagged unmarked (of 150) | Unflagged practice outputs (of 5) |
|---|---|---|
| 0.55 | 1 | 0 |
| 0.60 | 0 | 0 |
| 0.65 | 0 | 0 |
| 0.70 | 0 | 0 |

I ruled out 0.55 because it falsely flags one passage. Of the error-free choices I picked 0.65, because it leaves about 0.05 on both sides: the highest unmarked score is 0.596, and the lowest practice output is 0.703. At 0.60 the closest unmarked passage would be only 0.004 below. I then froze the settings with `evaluate.py fix`, which refuses to overwrite them: the key, the word rules of section 1, threshold 0.65, target 0.70, and the stopping rule "stop as soon as the green fraction reaches 0.70, or when no further edit can raise it without changing the meaning."

## 4. Evaluation results

With the settings frozen, I watermarked the 10 evaluation passages at my request, and I ran `evaluate.py evaluate` once.

| Measurement | Calculation | Result |
|---|---|---|
| Unmarked false-positive rate | flagged unmarked / 150 | 0 / 150 (95% upper bound ≈ 3/150 = 2%) |
| Detection rate on outputs | flagged outputs / 10 attempts | 10 / 10 |
| Usable watermarking success rate | flagged and passed quality check / 10 | 9 / 10 |
| Reached the target | green fraction ≥ 0.70 | 10 / 10 |

The evaluation edits followed the same procedure under the frozen rules. Because the rule says to stop at the target, most outputs end just above 0.70. `eva_wm_09` reached 0.699 in `v02`, one green word short, so `v03` made one more swap. The `eva_wm_07` edit also dropped a stray footnote number that data cleaning had missed. Every version is saved in `data/watermarked/`.

| Passage | Book | Forgery | Before | After | Changed words | Flagged | Meaning | Readable | Usable |
|---|---|---|---|---|---|---|---|---|---|
| `eva_wm_01` | gulliver | yes | 0.349 | 0.708 | 144 / 195 | yes | yes | yes | yes |
| `eva_wm_02` | jungle_book |  | 0.455 | 0.730 | 55 / 121 | yes | yes | yes | yes |
| `eva_wm_03` | odyssey | yes | 0.488 | 0.704 | 70 / 131 | yes | yes | yes | yes |
| `eva_wm_04` | sherlock |  | 0.385 | 0.750 | 64 / 117 | yes | yes | yes | yes |
| `eva_wm_05` | gulliver |  | 0.472 | 0.762 | 96 / 197 | yes | yes | yes | yes |
| `eva_wm_06` | jungle_book | yes | 0.356 | 0.702 | 90 / 174 | yes | yes | no | no |
| `eva_wm_07` | odyssey | yes | 0.442 | 0.701 | 93 / 172 | yes | yes | yes | yes |
| `eva_wm_08` | sherlock |  | 0.429 | 0.704 | 86 / 191 | yes | yes | yes | yes |
| `eva_wm_09` | gulliver |  | 0.378 | 0.706 | 91 / 172 | yes | yes | yes | yes |
| `eva_wm_10` | jungle_book | yes | 0.392 | 0.710 | 73 / 153 | yes | yes | yes | yes |

Every attempt reached the target, but only through heavy rewriting: 45–74% of words changed, 53% on average. The lowest starting passages needed the most work; `eva_wm_01` started at 0.349 and needed 144 of 195 words changed. The one unusable output, `eva_wm_06`, kept its meaning, but to avoid the red word "the" it turned "the camel" and "the mule" into "one camel" and "a mule", which reads as if different animals were speaking. Following the stopping rule, I did not redo it.

I align the normalized words of the original and edited versions with Python's `difflib.SequenceMatcher`. Each replaced, deleted or inserted run counts as its longer side, so a one-for-one swap counts 1 and replacing one word with three counts 3.

In the quality check, I compared each original with its edited version and answered two questions: is the main meaning preserved, and is the prose readable? Both had to be "yes" for the output to count as usable. The project asks for a teammate who did not edit the passage and who sees no scores. My reviewer, Claude, did not see the edits nor scores, so the review was not biased. That knowledge can influence the review because an editor tends to read their own changes, fills in unclear wording from memory, and knows which outputs reached the target, so an independent reader might have rejected more outputs.

| Length group | Flagged / tested | Mean green | Highest |
|---|---|---|---|
| 30–99 words | 0 / 50 | 0.415 | 0.569 |
| 100–199 words | 0 / 50 | 0.428 | 0.571 |
| 200–400 words | 0 / 50 | 0.429 | 0.549 |

No group had a false positive. Short and middle passages came closest to the threshold, because fewer words make a score swing more, but every unmarked passage stayed at least 0.079 below 0.65.

| Text | Total | Distinct | Green | Flagged |
|---|---|---|---|---|
| "the" × 100 | 100 | 1 | 0.000 | no |
| "is" × 100 | 100 | 1 | 1.000 | yes |
| `eva_un_200-400_06` (most repetitive unmarked passage) | 311 | 156 | 0.395 | no |
| same + "she is so." × 90 | 581 | 157 | 0.676 | **yes** |

Because repeats count, the most repeated words decide a score, and a single repeated word scores exactly 0 or 1. The most repetitive unmarked passage scores a normal 0.395, but appending the green sentence "she is so." 90 times raises it to 0.676 and gets it flagged, with only one new distinct word. Scoring each distinct word once would block this padding.

Zero out of 150 only bounds the false positive rate below about 3/150 = 2%. The passages also come from just 4 books, about 38–42 each, and passages from one book share vocabulary and style, so the effective sample is much smaller than 150. If I assume an operator receiving 10,000 unmarked submissions a year, the point estimate gives 0 false flags but the upper bound allows about 200. The real rate could be higher still, because my passages are 19th century novels and classic translations, not modern submissions, and a key that made the common words green would raise every baseline.

One mistake I made at the beginning is that the evaluation unmarked passages were scored once early at threshold 0.65 (0/150 flagged), and I knew this when I chose 0.65. Also, I first froze the settings with target 0.75, then lowered it to 0.70 after the practice review, before editing any evaluation passage. My last mistake that I caught was `cal_wm_05` comes from the edition's preface, not Austen's own text.

## 5. Threat model

Removal makes a flagged, usable watermarked passage unflagged; forgery makes unmarked prose flagged without the watermarking service. Both must keep meaning and readability. *Prediction* = not tested yet; *Measured* = from this milestone; *M2* = tested in Milestone 2.

| Goal | None (algorithm only) | Query (sees decisions) | Key (also knows the key) |
|---|---|---|---|
| **Removal** | **Attack:** paraphrase blindly. A new word is green at about the baseline 0.43, so going from 0.70 to ≤ 0.65 needs about 20% of words replaced. **Queries:** 0. **Effort/quality:** about 30–40 changed words per 170, so noticeable rewording. **Defense:** a wider target gap, longer texts. *Prediction.* | **Attack:** learn each word's color with one query of it repeated (scores 0 or 1), then swap green words for red. **Queries:** about one per candidate word. **Effort/quality:** about 8–10 swaps, so a minor change. **Defense:** distinct word scoring, minimum length *Prediction, M2.* | **Attack:** compute colors locally, swap the fewest green words. **Queries:** 0. **Effort/quality:** about 8–10 swaps, so almost unchanged. **Defense:** only key secrecy. *Prediction.* |
| **Forgery** | **Attack:** guess green words from published watermarked texts. **Queries:** 0. **Effort/quality:** high effort, will probably not work, and forced words read oddly. **Defense:** keep the key secret, publish few marked texts. *Prediction.* | **Attack:** learn colors by probing, then edit, or pad with a repeated green phrase. **Queries:** about 50–200. **Effort/quality:** like section 4, or none with obvious padding. **Defense:** distinct word scoring, minimum length, rate limits. *Prediction, M2.* | **Attack:** this milestone's edit procedure, which used the key. **Queries:** 0. **Effort/quality:** 45–74% of words changed; 9 of 10 usable. **Defense:** none once the key is known. *Measured, M2.* |

For this scheme, query access is almost as strong as key access, because one query of a repeated word reveals its color. Removal is also cheaper than forgery since it only needs to drop about 0.05, while forgery must lift text from about 0.43 to above 0.65.

**Key distribution.** Anyone with the key can watermark, detect locally and forge, so the service, local detectors and key holding forgers have the same power. Query users see only decisions. The operator sees the full text of everything submitted. An independent reviewer could check a disputed result by rerunning the public detector on the exact text with the key.

**Context dependence.** If a word's color depended on the word prior, a repeated word would reveal only its color after itself, so one word probing would fail. Padding would still work once an attacker found a phrase that is green in its own context, but that means querying whole phrases, and every edit would change the next word's color. Key access attacks would still work, with more computation.

**Digital signatures.** A signature proves that a key holder signed this exact text, with no false positives, but any edit breaks it. My watermark would survive small edits but can be removed or forged. A compromised signing key lets an attacker sign anything. And a compromised watermark key lets them both remove and forge. Verifying a signature shows which key signed the text, and a flag shows only a statistical match to a keyed pattern. Neither shows who actually wrote the text.

## 6. Conclusion

Under my frozen settings the detector flagged 0 of 150 unmarked passages and all 10 outputs, and 9 outputs were usable. But the false positive bound depends on 150 correlated passages from 4 books, watermarking required rewriting about half of each passage, and because repeats count, padding and single word probing make query access nearly as critical as key access.

## References

- Project Gutenberg, https://www.gutenberg.org. Book links are in `README.md`, Data sources.
- Python Software Foundation, `hmac`, `secrets`, `unicodedata` and `difflib` documentation, https://docs.python.org/3/library/.
- Course project description, Milestone 1, Sections 2 and 4.

## Contribution statement

I designed the project, collected the books, and wrote and ran the scripts, with help from Claude on `prepare_text.py` (I wrote the pseudocode and Claude helped fill gaps) and `evaluate.py`. At my request, did the quality reviews, without reviewing the original text, which I edited.
