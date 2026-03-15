# EnglishLearning

一个给个人使用的英语词组制卡工作台：输入一个或多个单词，调用 Gemini 生成完整解析，提取可复制词组，人工筛选后提交到 Anki。

## What It Does

- Generate full AI explanations for one or more input words
- Extract phrase pairs from the special copy format output
- Review, edit, select, and lock duplicate Front values before submission
- Preview the final Anki submission set with card-based UI
- Submit the final selected phrase pairs to Anki through AnkiConnect

## Current Workflow

1. Enter one or more English words in the local web page
2. Click the generate button to request AI output
3. Review the full response and the extracted phrase pairs
4. Edit Front and Back values when needed
5. Optionally uncheck low-value pairs or lock a duplicate Front to keep a preferred version
6. Preview the final submission cards
7. Select a target deck and submit to Anki

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
- `GEMINI_API_KEY`: use Gemini key from environment instead of local file
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

That keeps personal credentials and local prompt tuning out of version control.

## Anki Notes

- The project submits notes through AnkiConnect
- Decks are listed from local Anki
- Notes use the built-in `Basic` note type
- `Front` is the English phrase
- `Back` is the Chinese explanation
- Duplicate checks are based on `Front`

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

- This repository is designed for personal workflow rather than a public SaaS product
- If local Gemini configuration is unavailable, the app falls back to the built-in demo generation adapter
- If you previously exposed a real Gemini key, rotate it before continued use
