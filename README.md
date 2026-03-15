# EnglishLearning

[中文说明](README.zh-CN.md)

EnglishLearning is a personal English phrase card workspace. You enter one or more English words, generate full explanations with Gemini, extract phrase pairs from a copy-only format, review the results, and then submit selected cards to Anki.

## Quick View

- Multi-word input blocks for batch generation
- Full AI response kept visible for manual review
- Editable phrase pairs before submission
- Card-based final submission preview
- Duplicate `Front` handling with manual lock priority
- Local Anki deck selection through AnkiConnect

## What It Does

- Generates full AI explanations for one or more input words
- Extracts phrase pairs from the special copy format output
- Lets you review, edit, select, and lock duplicate `Front` values before submission
- Shows the final Anki submission set with a card-based preview
- Submits selected phrase pairs to Anki through AnkiConnect

## Workflow

1. Enter one or more English words in the local web page.
2. Click the generate button to request AI output.
3. Review the full response and the extracted phrase pairs.
4. Edit `Front` and `Back` values when needed.
5. Optionally uncheck low-value pairs or lock a duplicate `Front` to keep a preferred version.
6. Preview the final submission cards.
7. Select a target deck and submit to Anki.

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
- A card-based preview of the exact notes that will be sent to Anki

This keeps the AI output visible while still letting you manually curate the final study cards.

## Interface Highlights

Even without a bundled screenshot, the review page is organized around a few practical panels:

- input blocks for one or more words
- the full Gemini response for each word
- extracted phrase pairs with editable `Front` and `Back`
- selection and lock controls for duplicate handling
- a card-based submission preview before sending notes to Anki

This layout is meant to preserve context from the AI output while keeping the final Anki submission set easy to inspect.

## Roadmap

- GitHub roadmap issue: [#1 Track next workflow improvements](https://github.com/Amo-zwk/EnglishLearning/issues/1)
- Planned polish includes a README screenshot or GIF once browser capture tooling is available in this environment.
- Future items stay focused on practical workflow improvements rather than turning the project into a public SaaS product.

## Key Rules

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

## Optional Configuration

- `COPY_FORMAT_WEB_PORT`: override the local HTTP port
- `COPY_FORMAT_GENERATION_CALLABLE`: use a custom local generation adapter with `<file-path>:<callable-name>`
- `GEMINI_API_KEY`: use a Gemini key from the environment instead of a local file
- `COPY_FORMAT_GEMINI_KEY_FILE`: override the local key file path
- `COPY_FORMAT_PROMPT_FILE`: override the local prompt file path
- `COPY_FORMAT_GEMINI_MODEL`: override the Gemini model name, default is `gemini-2.5-pro`

Example:

```bash
COPY_FORMAT_WEB_PORT=8042 \
COPY_FORMAT_GENERATION_CALLABLE=/absolute/path/to/local_generation_adapter.py:generate_word \
uv run python -m src.web_entrypoint
```

## Local Files Kept Out Of Git

These files are intentionally ignored:

- `key`
- `英语二的备考prompt.txt`

This keeps personal credentials and local prompt tuning out of version control.

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
- If local Gemini configuration is unavailable, the app falls back to the built-in demo generation adapter.
- If you previously exposed a real Gemini key, rotate it before continued use.
