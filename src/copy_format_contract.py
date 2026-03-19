from __future__ import annotations

from dataclasses import dataclass, field
import re


COPY_FORMAT_PATTERN = re.compile(
    r"[\(（]复制专用[:：]\s*\$(?P<front>[^$]+)\$\s*\$(?P<back>[^$]+)\$[\)）]"
)


@dataclass(frozen=True)
class ExtractionRequest:
    input_word: str
    ai_response: str


@dataclass(frozen=True)
class ExtractedPhrasePair:
    front: str
    back: str


@dataclass(frozen=True)
class ExtractionResult:
    input_word: str
    phrases: list[ExtractedPhrasePair] = field(default_factory=list)


def make_front_dedupe_key(front_value: str) -> str:
    return front_value.strip()


def extract_copy_format_phrase_pairs(request: ExtractionRequest) -> ExtractionResult:
    phrases: list[ExtractedPhrasePair] = []

    for match in COPY_FORMAT_PATTERN.finditer(request.ai_response):
        front = make_front_dedupe_key(match.group("front"))
        back = match.group("back").strip()
        if not front or not back:
            continue
        phrases.append(ExtractedPhrasePair(front=front, back=back))

    return ExtractionResult(input_word=request.input_word, phrases=phrases)
