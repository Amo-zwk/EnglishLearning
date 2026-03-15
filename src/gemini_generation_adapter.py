from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Callable
from urllib import request


DEFAULT_MODEL = "gemini-2.5-pro"
GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
DEFAULT_KEY_FILE = Path(__file__).resolve().parent.parent / "key"
DEFAULT_PROMPT_FILE = Path(__file__).resolve().parent.parent / "英语二的备考prompt.txt"
KEY_ENV = "GEMINI_API_KEY"
KEY_FILE_ENV = "COPY_FORMAT_GEMINI_KEY_FILE"
MODEL_ENV = "COPY_FORMAT_GEMINI_MODEL"
PROMPT_FILE_ENV = "COPY_FORMAT_PROMPT_FILE"

API_KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_-]{20,}")


class MissingGeminiConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class GeminiAdapterConfig:
    api_key: str
    prompt_text: str
    model_name: str = DEFAULT_MODEL


def extract_api_key(raw_text: str) -> str:
    match = API_KEY_PATTERN.search(raw_text)
    if match is None:
        raise MissingGeminiConfigurationError(
            "No Gemini API key was found in the configured key source."
        )
    return match.group(0)


def load_api_key(
    environ: dict[str, str] | None = None,
    key_file: Path | None = None,
) -> str:
    environment = environ or dict(__import__("os").environ)
    env_value = environment.get(KEY_ENV, "").strip()
    if env_value:
        return env_value

    resolved_key_file = Path(
        environment.get(KEY_FILE_ENV, str(key_file or DEFAULT_KEY_FILE))
    )
    if not resolved_key_file.exists():
        raise MissingGeminiConfigurationError(
            f"Gemini key file was not found at {resolved_key_file}."
        )

    return extract_api_key(resolved_key_file.read_text(encoding="utf-8"))


def load_prompt_text(
    environ: dict[str, str] | None = None,
    prompt_file: Path | None = None,
) -> str:
    environment = environ or dict(__import__("os").environ)
    resolved_prompt_file = Path(
        environment.get(PROMPT_FILE_ENV, str(prompt_file or DEFAULT_PROMPT_FILE))
    )
    if not resolved_prompt_file.exists():
        raise MissingGeminiConfigurationError(
            f"Prompt file was not found at {resolved_prompt_file}."
        )

    prompt_text = resolved_prompt_file.read_text(encoding="utf-8").strip()
    if not prompt_text:
        raise MissingGeminiConfigurationError("Prompt file is empty.")
    return prompt_text


def build_generation_prompt(prompt_text: str, input_word: str) -> str:
    return (
        f"{prompt_text}\n\n"
        "现在只执行任务一：单词解析。"
        "请严格按照既有规则回答，并保留复制专用格式。"
        "如果没有值得记忆的搭配，就直接说明没有高价值搭配，不要虚构。"
        f"\n\n待解析单词：{input_word.strip()}\n"
    )


class GeminiGenerationAdapter:
    def __init__(
        self,
        config: GeminiAdapterConfig,
        post_json: Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]
        | None = None,
    ) -> None:
        self._config = config
        self._post_json = post_json or self._default_post_json

    @classmethod
    def from_local_files(
        cls,
        environ: dict[str, str] | None = None,
        post_json: Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]
        | None = None,
    ) -> "GeminiGenerationAdapter":
        environment = environ or dict(__import__("os").environ)
        config = GeminiAdapterConfig(
            api_key=load_api_key(environment),
            prompt_text=load_prompt_text(environment),
            model_name=environment.get(MODEL_ENV, DEFAULT_MODEL).strip()
            or DEFAULT_MODEL,
        )
        return cls(config=config, post_json=post_json)

    def generate_word(self, input_word: str) -> dict[str, str]:
        prompt = build_generation_prompt(self._config.prompt_text, input_word)
        url = GEMINI_API_URL_TEMPLATE.format(model=self._config.model_name)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.9,
                "responseMimeType": "text/plain",
            },
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._config.api_key,
        }
        response = self._post_json(url, payload, headers)
        return {"content": extract_response_text(response)}

    @staticmethod
    def _default_post_json(
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        request_body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url,
            data=request_body,
            headers=headers,
            method="POST",
        )
        with request.urlopen(http_request) as http_response:
            response_body = http_response.read().decode("utf-8")
        return json.loads(response_body)


def extract_response_text(response: dict[str, Any]) -> str:
    candidates = response.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError("Gemini response did not contain any candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not isinstance(parts, list):
        raise RuntimeError("Gemini response parts are missing.")

    text_chunks = [part.get("text", "") for part in parts if isinstance(part, dict)]
    text = "\n".join(chunk for chunk in text_chunks if isinstance(chunk, str)).strip()
    if not text:
        raise RuntimeError("Gemini response did not contain text content.")
    return text


def can_build_local_adapter(
    environ: dict[str, str] | None = None,
) -> bool:
    try:
        load_api_key(environ)
        load_prompt_text(environ)
    except MissingGeminiConfigurationError:
        return False
    return True
