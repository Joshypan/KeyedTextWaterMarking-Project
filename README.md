# KeyedTextWaterMarking-Project
Text watermarking embeds a detectable signal in text. In a keyed scheme, the signal depends on a secret key. A detector reports a match to that signal. Authorship and policy violations require separate evidence. The full method and results are in `Milestone1_Report.docx`.

[Github Repo](https://github.com/Joshypan/KeyedTextWaterMarking-Project)

## Data sources

All 315 passages were extracted from 8 source documents from [Project Gutenberg](https://www.gutenberg.org), a library of free ebooks. Project Gutenberg follows US copyright law, and these titles are public domain in the US. Plain-text (UTF-8) files were used. `prepare_text.py` strips the Gutenberg header and footer, footnotes and footnote numbers, transcriber's notes, headings and all-caps lines.

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

**One-time steps:** `key.py`, `evaluate.py fix` and `evaluate.py evaluate` refuse to run again once `keys/key.hex`, `results/settings.json` or `results/evaluation/` exists. The saved results depend on the original key, which is not in this repo (`keys/` is git-ignored), so a new key will not reproduce them.

### 1. Run the tests
```bash
python3 -m unittest discover -s tests -v
```

### 2. Prepare the passages
Download the books into `data/books/` first (see [Data sources](#data-sources)).
```bash
python3 prepare_text.py
```

### 3. Create the key
This writes the one random key to `keys/key.hex`.
```bash
python3 key.py
```

### 4. Practice watermarking on the calibration passages
Repeat this for `cal_wm_01` to `cal_wm_05`. Copy the original into its own folder. This overwrites any existing `v01.txt`.
```bash
mkdir -p data/watermarked/cal_wm_01 && cp data/passages/cal_wm_01.txt data/watermarked/cal_wm_01/v01.txt
```

Edit `v01.txt` by hand, and score it as you go to see its green fraction and red words.
```bash
python3 evaluate.py score data/watermarked/cal_wm_01/v01.txt --key keys/key.hex
```

Save each later attempt as `v02.txt`, `v03.txt`, etc., then copy the chosen one to `final.txt`.

### 5. Compare thresholds
This scores the 150 unmarked calibration passages and any finished `final.txt` outputs. Running it again overwrites the calibration results.
```bash
python3 evaluate.py calibrate --key keys/key.hex --thresholds 0.55 0.60 0.65 0.70
```

### 6. Freeze the settings
This saves the key file path, word rules, threshold, watermarking target and stopping rule to `results/settings.json`. These are the values used in this project.
```bash
python3 evaluate.py fix --key keys/key.hex --threshold 0.65 --target 0.70 --stop "Stop as soon as the green fraction reaches 0.70, or when no further edit can raise it without changing the meaning."
```

### 7. Watermark and review the evaluation passages
Repeat step 4 for `eva_wm_01` to `eva_wm_10`, using the frozen settings.

Then fill in `review/evaluation/quality_reviews.csv` with the columns `id,meaning_preserved,readable,notes` (answers `yes` or `no`). Any output without a review counts as not usable.

### 8. Run the evaluation
This scores the evaluation set with the frozen settings and reports the false-positive rate, detection rate and usable success rate. To keep the original results after a design change, add `--rerun NAME`, which saves a separate run.
```bash
python3 evaluate.py evaluate --key keys/key.hex
```

# Owner
Joshua Panchana Cedeno

I designed the project, collected the books, and wrote and ran the scripts, with help from Claude on prepare_text.py and evaluate.py, I wrote the pseudocode and Claude helped fill gaps. Claude also acted as the quality reviewer: at my request, it compared each original with my edited version and answered the meaning and readability questions without seeing scores or detector decisions. I ensured to organize the files and data to be easy to find and read for this report. I utilized my resources to check code output and see that the results were what I desired. I implemented key.py, test_detector.py, the file organization, the structured csv files with the help of Claude, and detector.py, also with the help of Claude. Detector.py was the difficult portion of this milestone due to the fact that you have to define what a "word" is and how to handle exceptions such as hyphens, then to make sure it is consistent. Claude aided in this file by providing advice on those use cases and error handling.
All commits can be seen on the GitHub repo in the README.

# Milestone 
1