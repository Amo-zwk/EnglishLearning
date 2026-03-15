# EnglishLearning

[中文说明](README.zh-CN.md)

Turn Gemini-generated English phrase explanations into manually reviewed Anki cards.

EnglishLearning is a local workspace for generating, reviewing, editing, and submitting useful phrase cards without losing the full AI context.

## GitHub Quick Intro

- Personal tool, not a public SaaS product
- The bundled prompt file is required for the intended output contract
- Generate phrase explanations with Gemini from one or more input words
- Review the full AI output before choosing what actually goes into Anki
- Edit extracted `Front` and `Back` pairs, handle duplicate `Front` values, and submit only the good cards
- Save a review session, restore it later, and keep the whole workflow local

Short repo description:

```text
Personal English phrase card workspace with Gemini generation, manual review, and Anki submission.
```

## Documentation

- English docs index: [`docs/README.md`](docs/README.md)
- Chinese docs index: [`docs/README.zh-CN.md`](docs/README.zh-CN.md)
- English scenario index: [`docs/scenario/README.md`](docs/scenario/README.md)
- Chinese scenario index: [`docs/scenario/README.zh-CN.md`](docs/scenario/README.zh-CN.md)
- English contribution guide: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Chinese contribution guide: [`CONTRIBUTING.zh-CN.md`](CONTRIBUTING.zh-CN.md)

## 3-Minute Quick Start

1. Install `Python 3.12+` and `uv`.
2. Clone the repo and run `uv sync`.
3. Put your Gemini key in `key`, or set `GEMINI_API_KEY`.
4. Keep `英语二的备考prompt.txt` in the project root.
5. If you want Anki submission, open Anki with AnkiConnect enabled.
6. Start the app:

```bash
uv run python -m src.web_entrypoint
```

7. Open:

```text
http://127.0.0.1:8031
```

If you only need the most important setup locations, jump to [`Where To Change URL And API Key`](#where-to-change-url-and-api-key).

If `uv` does not work on your machine yet, read [`Install Python And uv By OS`](#install-python-and-uv-by-os) first.

## Quick View

- Multi-word input blocks for batch generation
- Sticky review overview for larger review batches
- Full AI response kept visible for manual review
- Editable phrase pairs before submission
- Card-based final submission preview
- Duplicate `Front` handling with manual lock priority
- Session save and restore without regenerating results
- Clearer Anki submission feedback for submitted, skipped, and failed items
- Local Anki deck selection through AnkiConnect

## Screenshot

![Review workspace screenshot](docs/images/review-workspace.png)

## What It Does

- Generates full AI explanations for one or more input words
- Extracts phrase pairs from the special copy format output
- Lets you review, edit, select, and lock duplicate `Front` values before submission
- Keeps a review summary visible while you work through larger batches
- Shows the final Anki submission set with a card-based preview
- Lets you save the current review session and restore it later from a JSON payload
- Shows clearer post-submit feedback with grouped submitted, skipped, and failed results
- Submits selected phrase pairs to Anki through AnkiConnect

## Workflow

1. Enter one or more English words in the local web page.
2. Click the generate button to request AI output.
3. Review the full response and the extracted phrase pairs.
4. Edit `Front` and `Back` values when needed.
5. Optionally uncheck low-value pairs or lock a duplicate `Front` to keep a preferred version.
6. Optionally save the current review session if you want to continue later.
7. Preview the final submission cards.
8. Select a target deck and submit to Anki.
9. Review grouped submission feedback for added, skipped, and failed items.

## Example Session

Input words:

```text
take
bring
```

What you review on the page:

- The full Gemini response for each input word
- Extracted phrase pairs from the copy-only format
- Checkboxes for whether each pair should be submitted
- Lock controls for choosing the preferred item when duplicate `Front` values appear
- A sticky review overview that keeps batch counts visible
- A card-based preview of the exact notes that will be sent to Anki
- A session export area for saving and restoring the current review state
- Submission feedback grouped by submitted, skipped, and failed results

This keeps the AI output visible while still letting you manually curate the final study cards.

## Interface Highlights

Even without a bundled screenshot, the review page is organized around a few practical panels:

- input blocks for one or more words
- a sticky review overview for batch progress
- the full Gemini response for each word
- extracted phrase pairs with editable `Front` and `Back`
- selection and lock controls for duplicate handling
- a card-based submission preview before sending notes to Anki
- a session save and restore panel for pausing and resuming review work
- clearer submission feedback cards after sending notes to Anki

This layout is meant to preserve context from the AI output while keeping the final Anki submission set easy to inspect.

## Roadmap

- GitHub roadmap issue: [#1 Track next workflow improvements](https://github.com/Amo-zwk/EnglishLearning/issues/1)
- Done: [#2 Improve review layout for larger batches](https://github.com/Amo-zwk/EnglishLearning/issues/2)
- Done: [#3 Support saving and restoring review sessions](https://github.com/Amo-zwk/EnglishLearning/issues/3)
- Done: [#4 Add clearer Anki submission feedback](https://github.com/Amo-zwk/EnglishLearning/issues/4)
- Planned polish includes a README screenshot or GIF once browser capture tooling is available in this environment.
- Future items stay focused on practical workflow improvements rather than turning the project into a public SaaS product.

## Key Rules

- The bundled prompt file `英语二的备考prompt.txt` is a required project file.
- This workflow is tied to that prompt and does not support replacing it with a different prompt while expecting the same extraction contract.
- Only content extracted from the copy-only format is used for Anki submission.
- Low-value phrase pairs should be skipped instead of added.
- Notes use the built-in `Basic` note type.
- `Front` is the English phrase.
- `Back` is the Chinese explanation.
- Duplicate checks are based on `Front`.
- If duplicate `Front` values exist, a locked item wins; otherwise the first selected item wins.

## Tech Stack

- Python 3.12+
- `uv` for environment and command execution
- Standard library WSGI server for the local site
- Gemini REST integration for generation
- AnkiConnect for deck listing and note submission

## Project Structure

- `src/web_entrypoint.py`: local web entrypoint and browser-side UI script
- `src/review_workspace.py`: review state, export logic, preview logic, submission flow
- `src/gemini_generation_adapter.py`: Gemini adapter and local config loading
- `src/anki_submission_gateway.py`: AnkiConnect integration and duplicate handling
- `src/ai_generation_orchestrator.py`: multi-input generation orchestration and timing
- `tests/`: unit and integration-style coverage for the workflow

## Installation

If you just want the shortest path to a working local setup:

1. Install Python 3.12 or newer.
2. Install `uv`.
3. Clone this repository.
4. Run `uv sync` in the project root.
5. Put your Gemini key into the local `key` file, or set `GEMINI_API_KEY`.
6. Make sure `英语二的备考prompt.txt` stays in the project root.
7. If you want Anki submission, open Anki with AnkiConnect enabled.
8. Start the site with `uv run python -m src.web_entrypoint`.

### Install Python And uv By OS

If `uv sync` or `uv run` fails immediately, the usual reason is that Python or `uv` was never installed correctly, or the shell has not reloaded after installation.

#### Windows

1. Install Python 3.12+ from `https://www.python.org/downloads/windows/`.
2. During installation, enable `Add python.exe to PATH`.
3. Open PowerShell and install `uv`:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4. Close PowerShell and open it again.
5. Confirm installation:

```powershell
python --version
uv --version
```

If `python` is still missing, try `py --version`.

#### macOS

1. Install Python 3.12+ from `https://www.python.org/downloads/macos/`, or install it with Homebrew.
2. Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Reload your shell:

```bash
source ~/.zshrc
```

4. Confirm installation:

```bash
python3 --version
uv --version
```

If you use a shell other than `zsh`, reload the matching shell config file instead.

#### Ubuntu Or Debian

1. Install Python and common setup tools:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
```

2. Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Reload your shell:

```bash
source ~/.bashrc
```

4. Confirm installation:

```bash
python3 --version
uv --version
```

#### Fedora

1. Install Python and curl:

```bash
sudo dnf install -y python3 python3-pip curl
```

2. Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Reload your shell and confirm:

```bash
source ~/.bashrc
python3 --version
uv --version
```

### If uv Still Does Not Work

- Open a new terminal window and run `uv --version` again.
- If the shell says `uv: command not found`, the install succeeded but `PATH` was not reloaded.
- On macOS or Linux, try `source ~/.zshrc` or `source ~/.bashrc`, then re-run `uv --version`.
- On Windows, fully close PowerShell or CMD and open a new one.
- If Python is missing, install Python first and then repeat the `uv` installation.
- If `uv sync` fails inside the repo, run `uv python list` to confirm that `uv` can see Python.

Example install commands:

```bash
git clone git@github.com:Amo-zwk/EnglishLearning.git
cd EnglishLearning
uv sync
uv run python -m src.web_entrypoint
```

If `uv` is not installed yet, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After that, open `http://127.0.0.1:8031` in your browser.

## Run Locally

1. Install dependencies:

```bash
uv sync
```

2. Start the local site:

```bash
uv run python -m src.web_entrypoint
```

3. Open the local page:

```text
http://127.0.0.1:8031
```

## Where To Change URL And API Key

If you are trying to adapt this project in another place, these are the settings people usually spend too long trying to find:

- Gemini API key source:
  - default local file: `key`
  - environment override: `GEMINI_API_KEY`
  - alternate key file path: `COPY_FORMAT_GEMINI_KEY_FILE`
- Gemini request URL:
  - defined in `src/gemini_generation_adapter.py:12`
  - default endpoint template: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- Prompt file path:
  - default file: `英语二的备考prompt.txt`
  - relocation override: `COPY_FORMAT_PROMPT_FILE`
- Local web page URL:
  - default address: `http://127.0.0.1:8031`
  - port override: `COPY_FORMAT_WEB_PORT`
- AnkiConnect URL:
  - defined in `src/anki_submission_gateway.py:11`
  - default address: `http://127.0.0.1:8765`

Most users only need to touch `key`, `GEMINI_API_KEY`, or `COPY_FORMAT_WEB_PORT`.

## Optional Configuration

- `COPY_FORMAT_WEB_PORT`: override the local HTTP port
- `COPY_FORMAT_GENERATION_CALLABLE`: use a custom local generation adapter with `<file-path>:<callable-name>`
- `GEMINI_API_KEY`: use a Gemini key from the environment instead of a local file
- `COPY_FORMAT_GEMINI_KEY_FILE`: override the local key file path
- `COPY_FORMAT_PROMPT_FILE`: override the prompt file path only if you are relocating the same required project prompt
- `COPY_FORMAT_GEMINI_MODEL`: override the Gemini model name, default is `gemini-2.5-pro`

Example:

```bash
COPY_FORMAT_WEB_PORT=8042 \
COPY_FORMAT_GENERATION_CALLABLE=/absolute/path/to/local_generation_adapter.py:generate_word \
uv run python -m src.web_entrypoint
```

## Required Project Files

These files are part of the intended project setup:

- `英语二的备考prompt.txt`

The prompt file is versioned because the generation contract depends on it.

Why this prompt must stay fixed:

- The extractor depends on the copy-only output pattern produced by this prompt.
- Review, duplicate handling, preview, and Anki submission all assume that stable output contract.
- Replacing the prompt is likely to break extraction quality or the `Front` and `Back` mapping, even if generation still returns fluent text.

## Local Files Kept Out Of Git

These files are intentionally ignored:

- `key`

This keeps personal credentials out of version control while preserving the required project prompt.

## Verification

Run the test suite:

```bash
uv run python -m unittest discover -s tests
```

Compile-check key modules:

```bash
uv run python -m py_compile "src/web_entrypoint.py" "src/review_workspace.py"
```

## Notes

- This repository is designed for a personal workflow rather than a public SaaS product.
- The bundled prompt file is part of the product behavior, not an optional example.
- If local Gemini configuration is unavailable, the app falls back to the built-in demo generation adapter.
- If you previously exposed a real Gemini key, rotate it before continued use.

## FAQ

- Why does the `uv` command not work?
  - Make sure both Python and `uv` are installed first.
  - Use the OS-specific steps in [`Install Python And uv By OS`](#install-python-and-uv-by-os).
  - After installing `uv`, open a new terminal or reload your shell config.
  - Check `uv --version` before running `uv sync`.
  - If `uv` exists but cannot find Python, install Python 3.12+ and run `uv python list`.
- Why is generation not working?
  - Check whether `key` exists or `GEMINI_API_KEY` is set.
  - Check whether `英语二的备考prompt.txt` is still in the project root.
  - Check whether the local page is running at `http://127.0.0.1:8031` or your overridden port.
- Why is Anki submission not working?
  - Make sure Anki is open.
  - Make sure AnkiConnect is installed and reachable at `http://127.0.0.1:8765`.
  - Make sure you selected a target deck before submission.
- Why can I not swap in another prompt?
  - This workflow depends on the copy-only extraction contract produced by the bundled prompt.
  - Replacing the prompt may still generate text, but it can break extraction and `Front` or `Back` mapping.
