from __future__ import annotations

from dataclasses import dataclass, field, replace
from html import escape
import time
import math
from typing import Callable

from src.ai_generation_orchestrator import OrchestratedResultGroup
from src.anki_submission_gateway import SubmissionResult
from src.copy_format_contract import ExtractedPhrasePair


@dataclass(frozen=True)
class ExportedGroupPairs:
    group_index: int
    result_group: OrchestratedResultGroup
    phrase_pairs: list[ExtractedPhrasePair] = field(default_factory=list)


@dataclass(frozen=True)
class InputBlock:
    value: str = ""


@dataclass(frozen=True)
class ReviewWorkspaceState:
    input_blocks: list[InputBlock] = field(default_factory=list)
    result_groups: list[OrchestratedResultGroup] = field(default_factory=list)
    available_decks: list[str] = field(default_factory=list)
    selected_deck: str = ""
    selected_pairs_by_group: list[list[bool]] = field(default_factory=list)
    locked_pairs_by_group: list[list[bool]] = field(default_factory=list)
    submission_outcomes: list[GroupSubmissionOutcome] = field(default_factory=list)
    last_generation_duration_seconds: float | None = None


@dataclass(frozen=True)
class GroupSubmissionOutcome:
    input_word: str
    submitted_count: int
    skipped_count: int
    failed_count: int
    submitted_pairs: list[ExtractedPhrasePair] = field(default_factory=list)
    skipped_pairs: list[ExtractedPhrasePair] = field(default_factory=list)
    failed_pairs: list[ExtractedPhrasePair] = field(default_factory=list)
    error_message: str = ""


class ReviewWorkspaceController:
    def __init__(
        self,
        generation_action: Callable[[list[str]], list[OrchestratedResultGroup]],
        list_decks_action: Callable[[], list[str]],
        submit_action: Callable[[str, list[ExtractedPhrasePair]], SubmissionResult],
        initial_input_count: int = 1,
    ) -> None:
        safe_input_count = max(initial_input_count, 1)
        self._generation_action = generation_action
        self._list_decks_action = list_decks_action
        self._submit_action = submit_action
        available_decks = list(self._list_decks_action())
        self.state = ReviewWorkspaceState(
            input_blocks=[InputBlock() for _ in range(safe_input_count)],
            available_decks=available_decks,
        )

    def add_input_block(self) -> None:
        self.state = replace(
            self.state,
            input_blocks=[*self.state.input_blocks, InputBlock()],
        )

    def update_input_block(self, index: int, value: str) -> None:
        updated_blocks = list(self.state.input_blocks)
        updated_blocks[index] = InputBlock(value=value)
        self.state = replace(self.state, input_blocks=updated_blocks)

    def generate_results(self) -> list[OrchestratedResultGroup]:
        input_words = [block.value.strip() for block in self.state.input_blocks]
        filtered_input_words = [input_word for input_word in input_words if input_word]
        start_time = time.perf_counter()
        result_groups = self._generation_action(filtered_input_words)
        generation_duration_seconds = time.perf_counter() - start_time
        selected_pairs_by_group = [
            [True for _phrase in result_group.extracted_phrases]
            for result_group in result_groups
        ]
        locked_pairs_by_group = [
            [False for _phrase in result_group.extracted_phrases]
            for result_group in result_groups
        ]
        self.state = replace(
            self.state,
            result_groups=result_groups,
            selected_pairs_by_group=selected_pairs_by_group,
            locked_pairs_by_group=locked_pairs_by_group,
            submission_outcomes=[],
            last_generation_duration_seconds=generation_duration_seconds,
        )
        return result_groups

    def edit_phrase(
        self,
        group_index: int,
        phrase_index: int,
        front_value: str | None = None,
        back_value: str | None = None,
    ) -> None:
        target_group = self.state.result_groups[group_index]
        updated_phrases = list(target_group.extracted_phrases)
        target_phrase = updated_phrases[phrase_index]
        updated_phrases[phrase_index] = ExtractedPhrasePair(
            front=target_phrase.front if front_value is None else front_value,
            back=target_phrase.back if back_value is None else back_value,
        )
        updated_groups = list(self.state.result_groups)
        updated_groups[group_index] = replace(
            target_group,
            extracted_phrases=updated_phrases,
        )
        self.state = replace(self.state, result_groups=updated_groups)

    def select_deck(self, deck_name: str) -> None:
        self.state = replace(self.state, selected_deck=deck_name)

    def set_phrase_selected(
        self,
        group_index: int,
        phrase_index: int,
        selected: bool,
    ) -> None:
        updated_selection = [
            list(group_selection)
            for group_selection in self.state.selected_pairs_by_group
        ]
        updated_selection[group_index][phrase_index] = selected
        self.state = replace(self.state, selected_pairs_by_group=updated_selection)

    def set_phrase_locked(
        self,
        group_index: int,
        phrase_index: int,
        locked: bool,
    ) -> None:
        updated_locking = [
            list(group_locking) for group_locking in self.state.locked_pairs_by_group
        ]
        updated_locking[group_index][phrase_index] = locked
        self.state = replace(self.state, locked_pairs_by_group=updated_locking)

    def submit_selected_pairs(self) -> list[GroupSubmissionOutcome]:
        submission_outcomes: list[GroupSubmissionOutcome] = []
        exported_groups = self._export_phrase_pairs_by_group()

        for group_index, group in enumerate(self.state.result_groups):
            selected_pairs = exported_groups[group_index].phrase_pairs
            if not selected_pairs:
                submission_outcomes.append(
                    GroupSubmissionOutcome(
                        input_word=group.input_word,
                        submitted_count=0,
                        skipped_count=0,
                        failed_count=0,
                    )
                )
                continue

            try:
                result: SubmissionResult = self._submit_action(
                    self.state.selected_deck,
                    selected_pairs,
                )
                submission_outcomes.append(
                    self._build_group_submission_outcome(group.input_word, result)
                )
            except Exception as error:
                submission_outcomes.append(
                    GroupSubmissionOutcome(
                        input_word=group.input_word,
                        submitted_count=0,
                        skipped_count=0,
                        failed_count=len(selected_pairs),
                        failed_pairs=list(selected_pairs),
                        error_message=str(error).strip(),
                    )
                )

        self.state = replace(self.state, submission_outcomes=submission_outcomes)
        return submission_outcomes

    def render_html(self) -> str:
        input_blocks_html = "".join(
            self._render_input_block(index=index, input_block=input_block)
            for index, input_block in enumerate(self.state.input_blocks)
        )
        result_cards_html = "".join(
            self._render_result_group(group_index, result_group)
            for group_index, result_group in enumerate(self.state.result_groups)
        )
        deck_options_html = "".join(
            self._render_deck_option(deck_name, self.state.selected_deck)
            for deck_name in self.state.available_decks
        )
        copy_export_html = self._render_copy_export_area()
        review_overview_html = self._render_review_overview()
        return (
            '<section class="review-workspace">'
            '<div class="input-blocks">'
            f"{input_blocks_html}"
            "</div>"
            '<button type="submit" name="action" value="generate" class="generate-action">开始生成</button>'
            f"{self._render_generation_timing()}"
            f"{review_overview_html}"
            f"{copy_export_html}"
            '<section class="deck-selection-area">'
            '<label for="deck-selection">目标 Deck</label>'
            f'<select id="deck-selection" name="selected_deck" class="deck-selection">{deck_options_html}</select>'
            "</section>"
            '<section class="grouped-results">'
            f"{result_cards_html}"
            "</section>"
            "</section>"
        )

    def _render_review_overview(self) -> str:
        group_count = len(self.state.result_groups)
        phrase_count = sum(
            len(result_group.extracted_phrases)
            for result_group in self.state.result_groups
        )
        selected_count = sum(
            len(exported_group.phrase_pairs)
            for exported_group in self._export_phrase_pairs_by_group()
        )
        locked_count = sum(
            1
            for group_index, result_group in enumerate(self.state.result_groups)
            for phrase_index, _phrase_pair in enumerate(result_group.extracted_phrases)
            if self._is_phrase_locked(group_index, phrase_index)
        )
        if not group_count and not phrase_count:
            return ""
        return (
            '<section class="review-overview" aria-label="审核概览">'
            '<div class="review-overview-metric"><span class="review-overview-label">批次</span>'
            f'<strong class="review-overview-value">{group_count}</strong></div>'
            '<div class="review-overview-metric"><span class="review-overview-label">提取词组</span>'
            f'<strong class="review-overview-value">{phrase_count}</strong></div>'
            '<div class="review-overview-metric"><span class="review-overview-label">当前将提交</span>'
            f'<strong class="review-overview-value">{selected_count}</strong></div>'
            '<div class="review-overview-metric"><span class="review-overview-label">锁定优先</span>'
            f'<strong class="review-overview-value">{locked_count}</strong></div>'
            "</section>"
        )

    @staticmethod
    def _build_group_submission_outcome(
        input_word: str,
        result: SubmissionResult,
    ) -> GroupSubmissionOutcome:
        return GroupSubmissionOutcome(
            input_word=input_word,
            submitted_count=result.submitted_count,
            skipped_count=result.skipped_count,
            failed_count=result.failed_count,
            submitted_pairs=list(result.submitted_pairs),
            skipped_pairs=list(result.skipped_pairs),
            failed_pairs=list(result.failed_pairs),
        )

    @staticmethod
    def _build_phrase_pair(front: str, back: str) -> ExtractedPhrasePair:
        return ExtractedPhrasePair(front=front, back=back)

    @staticmethod
    def _build_result_group(
        input_word: str,
        full_ai_response: str,
        extracted_phrases: list[ExtractedPhrasePair],
    ) -> OrchestratedResultGroup:
        return OrchestratedResultGroup(
            input_word=input_word,
            full_ai_response=full_ai_response,
            extracted_phrases=extracted_phrases,
        )

    @staticmethod
    def _render_input_block(index: int, input_block: InputBlock) -> str:
        return (
            f'<label class="input-block" for="input-word-{index}">'
            f"<span>输入单词 {index + 1}</span>"
            f'<textarea id="input-word-{index}" name="input_word_{index}" class="input-word-field">{escape(input_block.value)}</textarea>'
            "</label>"
        )

    def _render_result_group(
        self,
        group_index: int,
        result_group: OrchestratedResultGroup,
    ) -> str:
        full_response = escape(result_group.full_ai_response or "")
        generation_failure = self._render_generation_failure(result_group)
        review_area = self._render_extracted_review_area(group_index, result_group)
        submission_feedback = self._render_submission_feedback(group_index)
        return (
            f'<article class="grouped-result-card" data-input-word="{escape(result_group.input_word)}">'
            '<div class="result-card-header">'
            f"<h2>单词：{escape(result_group.input_word)}</h2>"
            f"{self._render_group_generation_timing(result_group)}"
            "</div>"
            f"{generation_failure}"
            '<details class="full-response-panel" open>'
            '<summary class="full-response-toggle">完整 AI 响应</summary>'
            f'<div class="full-ai-response">{full_response}</div>'
            "</details>"
            f"{review_area}"
            f"{submission_feedback}"
            "</article>"
        )

    def _render_extracted_review_area(
        self,
        group_index: int,
        result_group: OrchestratedResultGroup,
    ) -> str:
        if not result_group.extracted_phrases:
            empty_state_message = "没有可提交的提取词组。"
            if result_group.failure is not None:
                empty_state_message = (
                    "这次生成没有产出可提交词组，请先根据上面的失败原因检查配置或重试。"
                )
            return (
                '<section class="extracted-review-area">'
                f"<p>{empty_state_message}</p>"
                "</section>"
            )

        phrase_boxes_html = "".join(
            self._render_phrase_box(
                group_index,
                phrase_index,
                phrase_pair,
                self._is_phrase_selected(group_index, phrase_index),
                self._is_phrase_locked(group_index, phrase_index),
            )
            for phrase_index, phrase_pair in enumerate(result_group.extracted_phrases)
        )
        return f'<section class="extracted-review-area">{phrase_boxes_html}</section>'

    @staticmethod
    def _render_phrase_box(
        group_index: int,
        phrase_index: int,
        phrase_pair: ExtractedPhrasePair,
        is_selected: bool,
        is_locked: bool,
    ) -> str:
        front_rows = ReviewWorkspaceController._measure_rows(phrase_pair.front)
        back_rows = ReviewWorkspaceController._measure_rows(phrase_pair.back)
        checked_attribute = " checked" if is_selected else ""
        locked_attribute = " checked" if is_locked else ""
        return (
            f'<div class="phrase-box" data-input-word-index="{group_index}" data-phrase-index="{phrase_index}">'
            f'<label class="phrase-select-toggle" for="phrase-select-{group_index}-{phrase_index}">'
            f'<input id="phrase-select-{group_index}-{phrase_index}" name="phrase_selected_{group_index}_{phrase_index}" class="phrase-select-input" type="checkbox" value="true"{checked_attribute}>'
            "提交时包含这条"
            "</label>"
            f'<label class="phrase-lock-toggle" for="phrase-lock-{group_index}-{phrase_index}">'
            f'<input id="phrase-lock-{group_index}-{phrase_index}" name="phrase_lock_{group_index}_{phrase_index}" class="phrase-lock-input" type="checkbox" value="true"{locked_attribute}>'
            "同 Front 重复时优先保留这条"
            "</label>"
            f'<label for="phrase-front-{group_index}-{phrase_index}">英文词组</label>'
            f'<textarea id="phrase-front-{group_index}-{phrase_index}" name="phrase_front_{group_index}_{phrase_index}" class="phrase-front-input" rows="{front_rows}" style="width: 100%; min-height: fit-content; resize: vertical; overflow: visible;">{escape(phrase_pair.front)}</textarea>'
            f'<label for="phrase-back-{group_index}-{phrase_index}">中文释义</label>'
            f'<textarea id="phrase-back-{group_index}-{phrase_index}" name="phrase_back_{group_index}_{phrase_index}" class="phrase-back-input" rows="{back_rows}" style="width: 100%; min-height: fit-content; resize: vertical; overflow: visible;">{escape(phrase_pair.back)}</textarea>'
            "</div>"
        )

    def _render_generation_timing(self) -> str:
        duration = self.state.last_generation_duration_seconds
        if duration is None:
            return ""
        return (
            '<section class="generation-timing-banner">'
            '<p class="generation-timing-label">本次生成总耗时</p>'
            f'<p class="generation-timing-value">{duration:.3f} 秒</p>'
            "</section>"
        )

    @staticmethod
    def _render_group_generation_timing(result_group: OrchestratedResultGroup) -> str:
        duration = result_group.generation_duration_seconds
        if duration is None:
            return ""
        return f'<span class="group-generation-timing">{duration:.3f} 秒</span>'

    @staticmethod
    def _render_generation_failure(result_group: OrchestratedResultGroup) -> str:
        if result_group.failure is None:
            return ""
        status = escape(result_group.failure.status)
        message = escape(result_group.failure.message)
        return (
            '<section class="generation-failure-banner" '
            f'data-failure-status="{status}" aria-live="polite">'
            '<p class="generation-failure-label">生成失败</p>'
            f'<p class="generation-failure-message">{message}</p>'
            "</section>"
        )

    def _render_copy_export_area(self) -> str:
        plain_text = self._build_copy_export_text()
        markdown_text = self._build_copy_export_markdown()
        anki_text = self._build_copy_export_anki()
        submission_preview = self._build_submission_preview_cards_html()
        if not plain_text:
            return ""
        return (
            '<section class="copy-export-area">'
            '<div class="copy-export-header">'
            "<h2>提取结果汇总</h2>"
            '<button type="button" class="secondary-action copy-export-button" data-copy-target="copy-export-text-plain">复制当前格式</button>'
            "</div>"
            '<p class="copy-export-help">仅汇总当前勾选的词组，默认会清理首尾空白并按英文词组去重。</p>'
            '<div class="copy-export-options">'
            '<label class="copy-export-option" for="copy-export-trim">'
            '<input id="copy-export-trim" class="copy-export-option-input" type="checkbox" data-export-option="trim" checked>'
            "清理首尾空白"
            "</label>"
            '<label class="copy-export-option" for="copy-export-dedupe-front">'
            '<input id="copy-export-dedupe-front" class="copy-export-option-input" type="checkbox" data-export-option="dedupe-front" checked>'
            "按英文词组去重"
            "</label>"
            "</div>"
            '<div class="copy-export-format-bar">'
            '<button type="button" class="copy-export-format-button is-active" data-export-format="plain">纯文本</button>'
            '<button type="button" class="copy-export-format-button" data-export-format="markdown">Markdown</button>'
            '<button type="button" class="copy-export-format-button" data-export-format="anki">Anki 风格</button>'
            "</div>"
            '<div class="copy-export-panels">'
            f'<textarea id="copy-export-text-plain" class="copy-export-text is-active" data-export-panel="plain" rows="{self._measure_rows(plain_text)}" readonly>{escape(plain_text)}</textarea>'
            f'<textarea id="copy-export-text-markdown" class="copy-export-text" data-export-panel="markdown" rows="{self._measure_rows(markdown_text)}" readonly hidden>{escape(markdown_text)}</textarea>'
            f'<textarea id="copy-export-text-anki" class="copy-export-text" data-export-panel="anki" rows="{self._measure_rows(anki_text)}" readonly hidden>{escape(anki_text)}</textarea>'
            "</div>"
            '<p class="copy-export-feedback" data-copy-feedback="copy-export-text-plain" aria-live="polite"></p>'
            '<section class="submission-preview-area">'
            '<div class="submission-preview-header">'
            "<h3>最终提交预览</h3>"
            "</div>"
            '<p class="submission-preview-help">这里展示按当前勾选、去空白和去重规则后，真正会提交到 Anki 的词组集合。</p>'
            f'<div id="submission-preview-cards" class="submission-preview-cards">{submission_preview}</div>'
            "</section>"
            "</section>"
        )

    def _build_copy_export_text(self) -> str:
        lines: list[str] = []
        for exported_group in self._export_phrase_pairs_by_group():
            if not exported_group.phrase_pairs:
                continue
            lines.append(f"[{exported_group.result_group.input_word}]")
            lines.extend(
                f"{phrase_pair.front} - {phrase_pair.back}"
                for phrase_pair in exported_group.phrase_pairs
            )
            lines.append("")
        return "\n".join(lines).strip()

    def _build_copy_export_markdown(self) -> str:
        lines: list[str] = []
        for exported_group in self._export_phrase_pairs_by_group():
            if not exported_group.phrase_pairs:
                continue
            lines.append(f"## {exported_group.result_group.input_word}")
            lines.extend(
                f"- {phrase_pair.front}: {phrase_pair.back}"
                for phrase_pair in exported_group.phrase_pairs
            )
            lines.append("")
        return "\n".join(lines).strip()

    def _build_copy_export_anki(self) -> str:
        lines: list[str] = []
        for exported_group in self._export_phrase_pairs_by_group():
            for phrase_pair in exported_group.phrase_pairs:
                lines.append(f"{phrase_pair.front}\t{phrase_pair.back}")
        return "\n".join(lines).strip()

    def _build_submission_preview_cards_html(self) -> str:
        cards_html: list[str] = []
        for exported_group in self._export_phrase_pairs_by_group():
            if not exported_group.phrase_pairs:
                continue
            items_html = "".join(
                '<article class="submission-preview-card">'
                f'<p class="submission-preview-card-front">{escape(phrase_pair.front)}</p>'
                f'<p class="submission-preview-card-back">{escape(phrase_pair.back)}</p>'
                "</article>"
                for phrase_pair in exported_group.phrase_pairs
            )
            cards_html.append(
                '<section class="submission-preview-group">'
                f'<h4 class="submission-preview-group-title">{escape(exported_group.result_group.input_word)}</h4>'
                f'<div class="submission-preview-card-list">{items_html}</div>'
                "</section>"
            )
        return "".join(cards_html)

    def _export_phrase_pairs_by_group(
        self,
        trim_whitespace: bool = True,
        dedupe_front: bool = True,
    ) -> list[ExportedGroupPairs]:
        grouped_pairs = [
            ExportedGroupPairs(group_index=index, result_group=result_group)
            for index, result_group in enumerate(self.state.result_groups)
        ]
        ordered_front_keys: list[str] = []
        chosen_entries_by_front: dict[str, tuple[int, ExtractedPhrasePair, bool]] = {}
        for group_index, result_group in enumerate(self.state.result_groups):
            for phrase_index, phrase_pair in enumerate(result_group.extracted_phrases):
                if not self._is_phrase_selected(group_index, phrase_index):
                    continue
                normalized_pair = self._normalize_export_phrase_pair(
                    phrase_pair,
                    trim_whitespace=trim_whitespace,
                )
                if normalized_pair is None:
                    continue
                normalized_front_key = normalized_pair.front.casefold()
                is_locked = self._is_phrase_locked(group_index, phrase_index)
                if not dedupe_front:
                    grouped_pairs[group_index].phrase_pairs.append(normalized_pair)
                    continue
                existing_entry = chosen_entries_by_front.get(normalized_front_key)
                if existing_entry is None:
                    ordered_front_keys.append(normalized_front_key)
                    chosen_entries_by_front[normalized_front_key] = (
                        group_index,
                        normalized_pair,
                        is_locked,
                    )
                    continue
                existing_group_index, _existing_pair, existing_locked = existing_entry
                if is_locked and not existing_locked:
                    chosen_entries_by_front[normalized_front_key] = (
                        group_index,
                        normalized_pair,
                        is_locked,
                    )
        if dedupe_front:
            for front_key in ordered_front_keys:
                group_index, phrase_pair, _is_locked = chosen_entries_by_front[
                    front_key
                ]
                grouped_pairs[group_index].phrase_pairs.append(phrase_pair)
        return grouped_pairs

    @staticmethod
    def _normalize_export_phrase_pair(
        phrase_pair: ExtractedPhrasePair,
        trim_whitespace: bool,
    ) -> ExtractedPhrasePair | None:
        front = phrase_pair.front.strip() if trim_whitespace else phrase_pair.front
        back = phrase_pair.back.strip() if trim_whitespace else phrase_pair.back
        if not front.strip() or not back.strip():
            return None
        return ExtractedPhrasePair(front=front, back=back)

    def _render_submission_feedback(self, group_index: int) -> str:
        if group_index >= len(self.state.submission_outcomes):
            return ""

        outcome = self.state.submission_outcomes[group_index]
        total_count = (
            outcome.submitted_count + outcome.skipped_count + outcome.failed_count
        )
        status_tone = "submitted"
        status_message = "本组词组已全部加入目标 Deck。"
        if outcome.failed_count and outcome.submitted_count:
            status_tone = "partial"
            status_message = "本组有一部分提交成功，另一部分失败，建议优先处理失败项。"
        elif outcome.failed_count and not outcome.submitted_count:
            status_tone = "failed"
            status_message = "本组提交未完成，请检查失败项和错误信息。"
        elif outcome.skipped_count and not outcome.submitted_count:
            status_tone = "skipped"
            status_message = "本组没有新增卡片，通常是因为重复或当前没有可提交项。"
        elif outcome.skipped_count:
            status_tone = "mixed"
            status_message = "本组包含已加入卡片和重复跳过项。"
        return (
            '<section class="submission-feedback">'
            f'<div class="submission-outcome-summary submission-outcome-summary-{status_tone}">'
            '<p class="submission-outcome-summary-label">提交反馈</p>'
            f'<h3 class="submission-outcome-summary-title">{escape(outcome.input_word)}: 已处理 {total_count} 条</h3>'
            f'<p class="submission-outcome-summary-text">{status_message}</p>'
            "</div>"
            f"{self._render_outcome_bucket('submitted', outcome.submitted_count, outcome.submitted_pairs)}"
            f"{self._render_outcome_bucket('skipped', outcome.skipped_count, outcome.skipped_pairs)}"
            f"{self._render_outcome_bucket('failed', outcome.failed_count, outcome.failed_pairs)}"
            f"{self._render_error_message(outcome.error_message)}"
            "</section>"
        )

    @staticmethod
    def _render_outcome_bucket(
        status: str,
        count: int,
        phrase_pairs: list[ExtractedPhrasePair],
    ) -> str:
        title_by_status = {
            "submitted": "已加入 Anki",
            "skipped": "已跳过",
            "failed": "提交失败",
        }
        help_by_status = {
            "submitted": "这些词组已经写入目标 Deck。",
            "skipped": "这些词组没有新建卡片，通常是 Front 重复或当前未进入最终提交集合。",
            "failed": "这些词组本次没有成功写入，请检查网络、AnkiConnect 或字段内容。",
        }
        items_html = "".join(
            '<li class="submission-outcome-item">'
            f'<span class="submission-outcome-front">{escape(phrase_pair.front)}</span>'
            f'<span class="submission-outcome-back">{escape(phrase_pair.back)}</span>'
            "</li>"
            for phrase_pair in phrase_pairs
        )
        return (
            f'<div class="submission-outcome {status}-outcome">'
            f'<div class="submission-outcome-header"><h3>{title_by_status.get(status, status)}: {count}</h3>'
            f"<p>{help_by_status.get(status, '')}</p></div>"
            f'<ul class="submission-outcome-list">{items_html}</ul>'
            "</div>"
        )

    @staticmethod
    def _render_error_message(error_message: str) -> str:
        if not error_message:
            return ""
        return f'<p class="submission-error-message">{escape(error_message)}</p>'

    def _is_phrase_selected(self, group_index: int, phrase_index: int) -> bool:
        if group_index >= len(self.state.selected_pairs_by_group):
            return True
        if phrase_index >= len(self.state.selected_pairs_by_group[group_index]):
            return True
        return self.state.selected_pairs_by_group[group_index][phrase_index]

    def _is_phrase_locked(self, group_index: int, phrase_index: int) -> bool:
        if group_index >= len(self.state.locked_pairs_by_group):
            return False
        if phrase_index >= len(self.state.locked_pairs_by_group[group_index]):
            return False
        return self.state.locked_pairs_by_group[group_index][phrase_index]

    @staticmethod
    def _render_deck_option(deck_name: str, selected_deck: str) -> str:
        selected_attribute = " selected" if deck_name == selected_deck else ""
        return f'<option value="{escape(deck_name)}"{selected_attribute}>{escape(deck_name)}</option>'

    @staticmethod
    def _measure_rows(value: str) -> int:
        line_count = max(value.count("\n") + 1, 1)
        wrapped_line_count = max(math.ceil(len(value) / 32), 1)
        return max(line_count, wrapped_line_count)
