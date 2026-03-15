# Copy-format review workspace

## Run the local HTML site

1. Make sure the project dependencies are available with `uv sync`.
2. Start the local site with `uv run python -m src.web_entrypoint`.
3. Open `http://127.0.0.1:8031` in your browser.

## Optional configuration

- `COPY_FORMAT_WEB_PORT`: Override the local HTTP port without editing code.
- `COPY_FORMAT_GENERATION_CALLABLE`: Point the app at a local generation adapter using `<file-path>:<callable-name>`.

Example:

```bash
COPY_FORMAT_WEB_PORT=8042 \
COPY_FORMAT_GENERATION_CALLABLE=/absolute/path/to/local_generation_adapter.py:generate_word \
uv run python -m src.web_entrypoint
```

The configured callable must accept one input word string and return either a response string or a dict containing a string `content` field.

## Local prerequisites

- Python 3.12+
- `uv`
- A reachable local AnkiConnect service at `http://127.0.0.1:8765` for deck listing and submission
- A local generation adapter if you want to replace the built-in demo generation responses

Without `COPY_FORMAT_GENERATION_CALLABLE`, the site first tries to build a local Gemini adapter from the project `key` file and `英语二的备考prompt.txt`. If Gemini configuration is unavailable, it falls back to the built-in demo adapter so you can still review the HTML workflow without editing code.

## Use the bundled Gemini adapter

If you keep your Gemini key inside the project `key` file, the site can use it automatically.

Recommended safer alternative on Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your-new-key"
uv run python -m src.web_entrypoint
```

Optional environment variables:

- `GEMINI_API_KEY`: Override the key file and use the Gemini key from the environment.
- `COPY_FORMAT_GEMINI_KEY_FILE`: Override the local key file path.
- `COPY_FORMAT_PROMPT_FILE`: Override the prompt file path.
- `COPY_FORMAT_GEMINI_MODEL`: Override the Gemini model name. Default: `gemini-2.5-pro`.

Important:

- If you previously exposed a real Gemini key, rotate it in Google AI Studio or Google Cloud before continued use.
- The bundled adapter sends your prompt plus the input word to Gemini and returns the raw text response for the website to parse.
