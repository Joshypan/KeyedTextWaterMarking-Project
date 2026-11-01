# KeyedTextWaterMarking-Project
Text watermarking embeds a detectable signal in text. In a keyed scheme, the signal depends on a secret key. A detector reports a match to that signal. Authorship and policy violations require separate evidence. The full method and results are in `report.md`.

## Data sources

All 315 passages were extracted from 8 source documents from [Project Gutenberg](https://www.gutenberg.org), a library of free ebooks. Project Gutenberg follows US copyright law, and these titles are public domain in the US. Plain-text (UTF-8) files were used. `prepare_text.py` strips the Gutenberg header and footer, footnotes and footnote numbers, transcriber's notes, headings and all-caps lines. The book files themselves are not committed (`data/books/` is git-ignored); download them from the links below.

| Book ID (file name) | Title | Author (translator) | Gutenberg link | Set | Passages |
|---|---|---|---|---|---|
| `austen` | Pride and Prejudice | Jane Austen | [1342](https://www.gutenberg.org/ebooks/1342) | calibration | 41 |
| `dracula` | Dracula | Bram Stoker | [345](https://www.gutenberg.org/ebooks/345) | calibration | 40 |
| `moby_dick` | Moby Dick; Or, The Whale | Herman Melville | [2701](https://www.gutenberg.org/ebooks/2701) | calibration | 37 |
| `prince` | The Prince | Niccolò Machiavelli | [1232](https://www.gutenberg.org/ebooks/1232) | calibration | 37 |
| `gulliver` | Gulliver's Travels into Several Remote Nations of the World | Jonathan Swift | [829](https://www.gutenberg.org/ebooks/829) | evaluation | 42 |
| `jungle_book` | The Jungle Book | Rudyard Kipling | [236](https://www.gutenberg.org/ebooks/236) | evaluation | 42 |
| `odyssey` | The Odyssey (prose translation) | Homer (Samuel Butler, translator) | [1727](https://www.gutenberg.org/ebooks/1727) | evaluation | 38 |
| `sherlock` | The Adventures of Sherlock Holmes | Arthur Conan Doyle | [1661](https://www.gutenberg.org/ebooks/1661) | evaluation | 38 |

**Set assignment:** 4 books per set. The book files are shuffled with `random.Random(20261009)` and assigned to calibration and evaluation. Each set has 150 unmarked passages (50 per length group: 30–99, 100–199, 200–400 words) and its watermarking passages (5 calibration, 10 evaluation).

**Query-access forgery passages:** `eva_wm_01`, `eva_wm_03`, `eva_wm_06`, `eva_wm_07`, `eva_wm_10`, chosen with `random.Random(7).sample(...)` from the 10 evaluation watermarking passages during data prep, before any detector score existed.

Each passage's book, set, length group, total and distinct word counts, and forgery label are in `data/manifest.csv`. The method and counts are in `data/split_info.json`.

# Commands
Run commands from the project folder.

**READ** The commands are in experiment order, and each step depends on the work before it. `key.py`, `evaluate.py fix` and `evaluate.py evaluate` are one-time steps, they refuse to run again once the key, `results/settings.json` or `results/evaluation/` exists.

```python3 -m unittest discover -s tests -v```
Allows you to run full test suite. The key used for testing is ONLY used for testing.

```python3 prepare_text.py ```
Allows you to normalize the data (books in this case) into passages

```python3 key.py```
Creates the one random key in `keys/key.hex`

```python3 evaluate.py calibrate --key keys/key.hex --thresholds 0.55 0.60 0.65 0.70```
Scores the 150 unmarked calibration passages and any finished calibration watermarking outputs, and compares the listed thresholds.

```mkdir -p data/watermarked/cal_wm_01 && cp data/passages/cal_wm_01.txt data/watermarked/cal_wm_01/v01.txt```
Starts a watermarking attempt, copy the original into its own folder, then edit `v01.txt` by hand. Save each later version as `v02.txt`, `v03.txt`,etc. Then, copy the chosen one to `final.txt`.

```python3 evaluate.py score data/watermarked/cal_wm_01/v01.txt --key keys/key.hex```
Scores one file while you edit it and lists its red words.

```python3 evaluate.py fix --key keys/key.hex --threshold 0.65 --target 0.70 --stop "Stop as soon as the green fraction reaches 0.70, or when no further edit can raise it without changing the meaning."```
Freezes the key file, word rules, threshold, watermarking target and stopping rule in `results/settings.json`. These are the values used in this project. It cannot be overwritten.

**Quality check, before evaluating:** fill in `review/evaluation/quality_reviews.csv` with the columns `id,meaning_preserved,readable,notes` (answers `yes` or `no`). Any output without a review won't work since it cannot be used.

```python3 evaluate.py evaluate --key keys/key.hex```
Scores the evaluation set with the frozen settings and reports the false-positive rate, detection rate and usable success rate.

# Owner
Joshua Panchana Cedeno

During this first milestone, my main issue stemmed from being able to find passages. I was able to solve this issue using [gutenberg.org](https://www.gutenberg.org) and downloading .txt files of the books, parsing the files to create the passages I need and mark them. I was able to implement an organized way of breaking down the txt files into passages and storing their watermarked versions. The watermarked versions are in the `data/watermarked` directory, the quality reviews are in the `review` directory, and the calibration and evaluation results are in the `results` directory. Read the report for more information on the flow of watermarking and the final evaluation in `report.md`.

Contributions - Claude
Claude aided in the generation of evaluate.py and prepare_text.py. When creating prepare_text.py, I started by generating my own pseudocode to understand the layout of the program. Occasionally, there would be gaps I could not fill that caused my file to not parse the text correctly or crash. evaluate.py had the same start, but Claude generated suggestions for the code logic behind the cmd_x functions. Additionally, at my request, Claude made the quality reviews after I watermarked the passages.

# Milestone 
1