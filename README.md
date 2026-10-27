# KeyedTextWaterMarking-Project
Text watermarking embeds a detectable signal in text. In a keyed scheme, the signal depends on a secret key. A detector reports a match to that signal. Authorship and policy violations require separate evidence.

## Data sources

All 315 passages were extracted from 8 source documents from [Project Gutenberg](https://www.gutenberg.org), a library of free ebooks. Project Gutenberg follows US copyright law, and these titles are public domain in the US. Plain-text (UTF-8) files were used, and the Gutenberg header and footer are stripped by `prepare_data.py`.

| Book ID (file name) | Title | Author (translator) | Gutenberg link |
|---|---|---|---|
| `beowulf` | Beowulf: An Anglo-Saxon Epic Poem | J. Lesslie Hall (translator) | [16328](https://www.gutenberg.org/ebooks/16328) |
| `dracula` | Dracula | Bram Stoker | [345](https://www.gutenberg.org/ebooks/345) |
| `sherlock` | The Adventures of Sherlock Holmes | Arthur Conan Doyle | [1661](https://www.gutenberg.org/ebooks/1661) |
| `prince` | The Prince | Niccolò Machiavelli | [1232](https://www.gutenberg.org/ebooks/1232) |
| `odyssey` | The Odyssey (prose translation) | Homer (Samuel Butler, translator) | [1727](https://www.gutenberg.org/ebooks/1727) |
| `moby_dick` | Moby Dick; Or, The Whale | Herman Melville | [2701](https://www.gutenberg.org/ebooks/2701) |
| `jungle_book` | The Jungle Book | Rudyard Kipling | [236](https://www.gutenberg.org/ebooks/236) |
| `gulliver` | Gulliver's Travels into Several Remote Nations of the World | Jonathan Swift | [829](https://www.gutenberg.org/ebooks/829) |

**Set assignment** (from `data/split_info.json`): `[TODO: list which 4 books are calibration and which 4 are evaluation after running prepare_data.py]`
File name (book ID)	Title	Author	Gutenberg URL
austen_pride	Pride and Prejudice	Jane Austen	https://www.gutenberg.org/ebooks/1342

# Commands
```python3 -m unittest discover -s tests -v```
Allows you to run full test suite. The key used for testing is ONLY used for testing.

```python3 prepare_text.py ```
Allows you to normallize the data (books in this case) into passages

# Owner
Joshua Panchana Cedeno
    During this first milestone, my main issue stemmed from being able to find passages. I was able to solve this issue using [gutenberg.org](https://www.gutenberg.org) and downloading .txt files of the books, parsing the files to create the passages I need and mark them. 
    I utilized Github as my source control to and to create issues for the required tasks. 

# Milestone 
1