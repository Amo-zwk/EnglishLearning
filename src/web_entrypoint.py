from __future__ import annotations

from dataclasses import dataclass
from importlib import util
from pathlib import Path
from typing import Callable, Protocol, cast
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from src.ai_generation_orchestrator import (
    EndpointWordGenerationApi,
    OrchestratedResultGroup,
    orchestrate_generation_requests,
)
from src.anki_submission_gateway import (
    AnkiConnectGateway,
    AnkiConnectHttpClient,
    SubmissionResult,
)
from src.copy_format_contract import ExtractedPhrasePair
from src.gemini_generation_adapter import (
    GeminiGenerationAdapter,
    can_build_local_adapter,
)
from src.review_workspace import ReviewWorkspaceController


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8031
GENERATION_CALLABLE_ENV = "COPY_FORMAT_GENERATION_CALLABLE"
PORT_ENV = "COPY_FORMAT_WEB_PORT"


GenerationCallable = Callable[[str], object]
ListDecksAction = Callable[[], list[str]]
SubmitAction = Callable[[str, list[ExtractedPhrasePair]], SubmissionResult]


class WorkspaceStateProtocol(Protocol):
    @property
    def input_blocks(self) -> list[object]: ...

    @property
    def result_groups(self) -> list[OrchestratedResultGroup]: ...


class WorkspaceControllerProtocol(Protocol):
    @property
    def state(self) -> WorkspaceStateProtocol: ...

    def add_input_block(self) -> None: ...

    def update_input_block(self, index: int, value: str) -> None: ...

    def generate_results(self) -> list[OrchestratedResultGroup]: ...

    def select_deck(self, deck_name: str) -> None: ...

    def edit_phrase(
        self,
        group_index: int,
        phrase_index: int,
        front_value: str | None = None,
        back_value: str | None = None,
    ) -> None: ...

    def set_phrase_selected(
        self,
        group_index: int,
        phrase_index: int,
        selected: bool,
    ) -> None: ...

    def set_phrase_locked(
        self,
        group_index: int,
        phrase_index: int,
        locked: bool,
    ) -> None: ...

    def submit_selected_pairs(self) -> list[object]: ...

    def render_html(self) -> str: ...


@dataclass(frozen=True)
class WebAppDependencies:
    generation_callable: GenerationCallable
    list_decks_action: ListDecksAction
    submit_action: SubmitAction
    initial_input_count: int = 2


def demo_generation_endpoint(input_word: str) -> dict[str, str]:
    return {
        "content": (
            f"Full response for {input_word}.\n"
            f"Useful phrase notes for {input_word}.\n"
            f"(复制专用: ${input_word} example phrase$ ${input_word} 示例含义$)\n"
            f"(复制专用: ${input_word} exam phrase$ ${input_word} 考研短语含义$)"
        )
    }


def load_generation_endpoint() -> GenerationCallable:
    configured_target = (
        __import__("os").environ.get(GENERATION_CALLABLE_ENV, "").strip()
    )
    if not configured_target:
        if can_build_local_adapter():
            return GeminiGenerationAdapter.from_local_files().generate_word
        return demo_generation_endpoint
    return _load_callable_from_target(configured_target)


def build_default_dependencies() -> WebAppDependencies:
    gateway = AnkiConnectGateway(AnkiConnectHttpClient())
    return WebAppDependencies(
        generation_callable=load_generation_endpoint(),
        list_decks_action=lambda: _safe_list_decks(gateway),
        submit_action=gateway.submit_phrase_pairs,
    )


def create_workspace_controller(
    dependencies: WebAppDependencies,
) -> ReviewWorkspaceController:
    generation_api = EndpointWordGenerationApi(dependencies.generation_callable)
    return ReviewWorkspaceController(
        generation_action=lambda input_words: orchestrate_generation_requests(
            input_words,
            generation_api,
        ),
        list_decks_action=dependencies.list_decks_action,
        submit_action=cast(SubmitAction, dependencies.submit_action),
        initial_input_count=dependencies.initial_input_count,
    )


def create_web_app(
    controller_factory: Callable[[], WorkspaceControllerProtocol] | None = None,
    dependencies: WebAppDependencies | None = None,
):
    resolved_dependencies = dependencies or build_default_dependencies()
    workspace_controller: WorkspaceControllerProtocol = (
        controller_factory()
        if controller_factory is not None
        else cast(
            WorkspaceControllerProtocol,
            create_workspace_controller(resolved_dependencies),
        )
    )

    def app(environ, start_response):
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))

        if path != "/":
            response_body = "Not Found".encode("utf-8")
            start_response(
                "404 Not Found",
                [
                    ("Content-Type", "text/plain; charset=utf-8"),
                    ("Content-Length", str(len(response_body))),
                ],
            )
            return [response_body]

        if method == "POST":
            form_data = _read_form_data(environ)
            _apply_request_to_workspace(workspace_controller, form_data)

        page = render_page(workspace_controller.render_html())
        response_body = page.encode("utf-8")
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(response_body))),
            ],
        )
        return [response_body]

    return app


def render_page(workspace_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <meta name=\"description\" content=\"个人英语词组制卡工具，生成解析、整理可复制词组，并提交到 Anki。\">
    <title>英语词组制卡工作台</title>
    <style>
        :root {{
            --page-bg: #f4efe7;
            --page-ink: #1f2933;
            --panel: rgba(255, 252, 247, 0.92);
            --panel-strong: #fffaf1;
            --line: rgba(112, 85, 58, 0.18);
            --hero-start: #183a37;
            --hero-end: #2f5d50;
            --accent: #c96f3b;
            --accent-deep: #a85128;
            --accent-soft: #f7d7bf;
            --muted: #6b6f76;
            --sky-soft: #d9e8f2;
            --gold-soft: #f8ebc9;
            --shadow: 0 24px 60px rgba(44, 33, 23, 0.12);
            --radius-xl: 24px;
            --radius-lg: 18px;
            --radius-md: 14px;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: Georgia, "Times New Roman", serif;
            margin: 0;
            background:
                radial-gradient(circle at top left, rgba(249, 212, 182, 0.45), transparent 32%),
                radial-gradient(circle at top right, rgba(205, 227, 219, 0.5), transparent 26%),
                linear-gradient(180deg, #f8f2e9 0%, var(--page-bg) 100%);
            color: var(--page-ink);
        }}
        body::before {{
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image: linear-gradient(rgba(95, 72, 52, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(95, 72, 52, 0.03) 1px, transparent 1px);
            background-size: 24px 24px;
            mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.5), transparent 85%);
        }}
        main {{ max-width: 1040px; margin: 0 auto; padding: 32px 20px 56px; position: relative; z-index: 1; }}
        .page-hero {{
            margin-bottom: 22px;
            padding: 28px;
            border-radius: 28px;
            background: linear-gradient(135deg, var(--hero-start) 0%, var(--hero-end) 62%, #507c66 100%);
            color: #f8f4eb;
            box-shadow: var(--shadow);
            overflow: hidden;
            position: relative;
        }}
        .page-hero::after {{
            content: "";
            position: absolute;
            width: 280px;
            height: 280px;
            right: -60px;
            top: -100px;
            border-radius: 50%;
            background: rgba(252, 243, 219, 0.08);
        }}
        .eyebrow {{
            display: inline-flex;
            margin-bottom: 14px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(248, 244, 235, 0.13);
            color: #f5dcb8;
            font-size: 12px;
            letter-spacing: 0.08em;
        }}
        h1 {{ margin: 0; font-size: clamp(30px, 5vw, 48px); line-height: 1.06; letter-spacing: 0.01em; }}
        .page-intro {{ max-width: 720px; margin: 12px 0 0; font-size: 17px; line-height: 1.7; color: rgba(248, 244, 235, 0.9); }}
        form {{ display: block; }}
        .review-workspace {{ display: grid; gap: 22px; }}
        .review-overview {{
            position: sticky;
            top: 18px;
            z-index: 2;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            padding: 14px;
            border-radius: var(--radius-xl);
            background: rgba(255, 250, 241, 0.94);
            border: 1px solid rgba(145, 112, 76, 0.12);
            box-shadow: 0 14px 30px rgba(62, 41, 22, 0.08);
            backdrop-filter: blur(12px);
        }}
        .review-overview-metric {{ display: grid; gap: 6px; padding: 12px 14px; border-radius: 18px; background: linear-gradient(180deg, rgba(255, 255, 252, 0.96) 0%, rgba(250, 243, 229, 0.92) 100%); border: 1px solid rgba(145, 112, 76, 0.1); }}
        .review-overview-label {{ font-size: 13px; color: #6b6f76; font-weight: 700; }}
        .review-overview-value {{ font-size: clamp(24px, 3vw, 32px); color: #3f2a18; }}
        .input-blocks, .grouped-results {{ display: grid; gap: 18px; }}
        .input-block, .phrase-box {{ display: grid; gap: 8px; }}
        .deck-selection-area, .copy-export-area, .grouped-result-card {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: var(--radius-xl);
            padding: 18px;
            backdrop-filter: blur(12px);
            box-shadow: 0 14px 35px rgba(62, 41, 22, 0.08);
        }}
        .copy-export-area {{ background: linear-gradient(180deg, rgba(255, 249, 236, 0.98) 0%, rgba(255, 245, 225, 0.92) 100%); gap: 12px; }}
        .copy-export-header {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }}
        .copy-export-header h2 {{ margin: 0; }}
        .deck-selection-area label, .input-block span, .phrase-box label {{ font-size: 14px; color: #5c4f43; font-weight: 700; }}
        textarea, select, input, button {{ font: inherit; }}
        textarea, select, input[type="search"] {{
            width: 100%;
            padding: 12px 14px;
            border-radius: var(--radius-md);
            border: 1px solid rgba(118, 93, 68, 0.18);
            background: rgba(255, 253, 249, 0.95);
            color: var(--page-ink);
            transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
        }}
        textarea:focus, select:focus, input[type="search"]:focus {{ outline: none; border-color: rgba(201, 111, 59, 0.7); box-shadow: 0 0 0 4px rgba(201, 111, 59, 0.14); }}
        .action-bar {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }}
        .generation-pending-banner {{
            display: none;
            margin: 0 0 20px;
            padding: 16px 18px;
            border-radius: 22px;
            border: 1px solid rgba(86, 130, 165, 0.18);
            background: linear-gradient(135deg, rgba(231, 241, 248, 0.96) 0%, rgba(245, 249, 252, 0.94) 100%);
            color: #23496b;
            box-shadow: 0 10px 24px rgba(61, 102, 129, 0.1);
        }}
        .generation-pending-banner.is-visible {{ display: grid; gap: 6px; }}
        .submission-pending-banner {{
            display: none;
            margin: 0 0 20px;
            padding: 16px 18px;
            border-radius: 22px;
            border: 1px solid rgba(115, 132, 78, 0.2);
            background: linear-gradient(135deg, rgba(241, 246, 228, 0.96) 0%, rgba(249, 251, 242, 0.94) 100%);
            color: #445b22;
            box-shadow: 0 10px 24px rgba(94, 117, 55, 0.1);
        }}
        .submission-pending-banner.is-visible {{ display: grid; gap: 6px; }}
        .generation-pending-label {{ margin: 0; font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.78; }}
        .generation-pending-text {{ margin: 0; font-size: 16px; line-height: 1.6; font-weight: 700; }}
        .submission-pending-label {{ margin: 0; font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.78; }}
        .submission-pending-text {{ margin: 0; font-size: 16px; line-height: 1.6; font-weight: 700; }}
        .generate-action.is-pending,
        .action-bar button[value="generate"].is-pending,
        .submission-preview-submit-button.is-pending,
        .action-bar button[value="submit"].is-pending {{
            opacity: 0.72;
            pointer-events: none;
            filter: saturate(0.92);
        }}
        .submission-global-banner {{
            display: grid;
            gap: 8px;
            margin-bottom: 18px;
            padding: 18px 20px;
            border-radius: var(--radius-xl);
            border: 1px solid rgba(145, 112, 76, 0.12);
            box-shadow: 0 14px 30px rgba(62, 41, 22, 0.08);
            background: rgba(255, 251, 243, 0.96);
        }}
        .submission-global-banner-submitted {{ background: linear-gradient(135deg, rgba(227, 244, 232, 0.98) 0%, rgba(242, 249, 244, 0.96) 100%); color: #244b2e; }}
        .submission-global-banner-mixed, .submission-global-banner-skipped {{ background: linear-gradient(135deg, rgba(251, 241, 214, 0.98) 0%, rgba(255, 248, 230, 0.96) 100%); color: #694d14; }}
        .submission-global-banner-partial, .submission-global-banner-failed {{ background: linear-gradient(135deg, rgba(252, 229, 222, 0.98) 0%, rgba(255, 242, 238, 0.96) 100%); color: #702f1f; }}
        .submission-global-banner-label {{ margin: 0; font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.82; }}
        .submission-global-banner-title {{ margin: 0; font-size: clamp(24px, 4vw, 32px); }}
        .submission-global-banner-metrics, .submission-global-banner-text {{ margin: 0; line-height: 1.6; font-weight: 700; }}
        button {{
            border: 0;
            border-radius: 999px;
            padding: 11px 18px;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-deep) 100%);
            color: #fffaf5;
            cursor: pointer;
            font-weight: 700;
            letter-spacing: 0.01em;
            box-shadow: 0 12px 24px rgba(169, 81, 40, 0.22);
            transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
        }}
        button:hover {{ transform: translateY(-1px); filter: saturate(1.03); }}
        button.secondary-action {{ background: linear-gradient(135deg, #5b6c75 0%, #42525a 100%); box-shadow: 0 10px 20px rgba(66, 82, 90, 0.18); }}
        .copy-export-button {{ white-space: nowrap; }}
        .copy-export-help, .copy-export-feedback {{ margin: 0; color: var(--muted); font-size: 14px; }}
        .copy-export-options {{ display: flex; gap: 12px; flex-wrap: wrap; }}
        .copy-export-option {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: rgba(255, 250, 241, 0.92); border: 1px solid rgba(145, 112, 76, 0.12); color: #6b5745; font-size: 14px; font-weight: 700; }}
        .copy-export-option-input {{ width: 16px; height: 16px; accent-color: var(--accent-deep); }}
        .copy-export-text {{ background: rgba(255, 251, 238, 0.95); }}
        .copy-export-format-bar {{ display: flex; gap: 10px; flex-wrap: wrap; }}
        .copy-export-format-button {{
            padding: 9px 14px;
            background: rgba(255, 248, 235, 0.92);
            color: #6e4d31;
            border: 1px solid rgba(201, 111, 59, 0.2);
            box-shadow: none;
        }}
        .copy-export-format-button.is-active {{
            background: linear-gradient(135deg, #f2c9a9 0%, #e8a777 100%);
            color: #4a2813;
            border-color: rgba(168, 81, 40, 0.26);
            box-shadow: 0 10px 20px rgba(169, 81, 40, 0.12);
        }}
        .copy-export-panels {{ display: grid; }}
        .copy-export-text {{ display: none; }}
        .copy-export-text.is-active {{ display: block; }}
        .deck-selection-area {{ display: grid; gap: 12px; }}
        .deck-selection-header {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(220px, 320px); gap: 12px; align-items: end; }}
        .deck-selection-header label {{ display: inline-flex; align-items: center; min-height: 46px; }}
        .deck-search-input {{ background: rgba(255, 252, 247, 0.98); }}
        .deck-selection-feedback {{ min-height: 20px; margin: 0; font-size: 14px; color: var(--muted); }}
        .submission-preview-area {{ display: grid; gap: 10px; padding: 14px 16px; border-radius: var(--radius-lg); background: rgba(255, 252, 244, 0.78); border: 1px solid rgba(145, 112, 76, 0.12); }}
        .submission-preview-header {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }}
        .submission-preview-header h3 {{ margin: 0; font-size: 18px; color: #5b4129; }}
        .submission-preview-submit-button {{ white-space: nowrap; }}
        .submission-preview-help {{ margin: 0; color: var(--muted); font-size: 14px; }}
        .phrase-select-toggle, .phrase-lock-toggle {{ display: inline-flex; align-items: center; gap: 8px; width: fit-content; padding: 7px 12px; border-radius: 999px; background: rgba(255, 249, 238, 0.92); border: 1px solid rgba(145, 112, 76, 0.12); color: #6b5745; }}
        .phrase-select-input, .phrase-lock-input {{ width: 16px; height: 16px; accent-color: var(--accent-deep); }}
        .submission-preview-cards {{ display: grid; gap: 14px; }}
        .submission-preview-group {{ display: grid; gap: 10px; padding: 14px; border-radius: var(--radius-lg); border: 1px solid rgba(145, 112, 76, 0.12); background: linear-gradient(180deg, rgba(255, 251, 242, 0.95) 0%, rgba(252, 246, 233, 0.88) 100%); }}
        .submission-preview-group-title {{ margin: 0; font-size: 16px; color: #5b4129; }}
        .submission-preview-card-list {{ display: grid; gap: 10px; }}
        .submission-preview-card {{ display: grid; gap: 6px; padding: 12px 14px; border-radius: 16px; background: rgba(255, 253, 248, 0.95); border: 1px solid rgba(166, 126, 88, 0.14); box-shadow: 0 8px 18px rgba(92, 62, 30, 0.06); }}
        .submission-preview-card-front {{ margin: 0; font-weight: 700; color: #3f2a18; }}
        .submission-preview-card-back {{ margin: 0; color: #62584d; line-height: 1.6; }}
        .generation-timing-banner {{
            margin: 4px 0 0;
            padding: 16px 18px;
            border-radius: 22px;
            border: 1px solid rgba(107, 157, 195, 0.28);
            background: linear-gradient(135deg, rgba(224, 238, 247, 0.95) 0%, rgba(213, 228, 238, 0.88) 100%);
            color: #23496b;
            box-shadow: 0 10px 24px rgba(61, 102, 129, 0.12);
        }}
        .generation-timing-label {{ margin: 0; font-size: 13px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }}
        .generation-timing-value {{ margin: 8px 0 0; font-size: clamp(28px, 4vw, 38px); font-weight: 800; }}
        .result-card-header {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }}
        .result-card-header h2 {{ margin: 0; font-size: 24px; }}
        .group-generation-timing {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 7px 11px; background: linear-gradient(135deg, var(--sky-soft) 0%, #edf5fb 100%); color: #2a6288; font-weight: 700; font-size: 13px; border: 1px solid rgba(86, 130, 165, 0.18); }}
        .generation-failure-banner {{
            display: grid;
            gap: 8px;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid rgba(181, 83, 52, 0.18);
            background: linear-gradient(135deg, rgba(255, 236, 228, 0.98) 0%, rgba(255, 246, 242, 0.96) 100%);
            color: #702f1f;
            box-shadow: 0 10px 20px rgba(181, 83, 52, 0.08);
        }}
        .generation-failure-label {{ margin: 0; font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.82; }}
        .generation-failure-message {{ margin: 0; line-height: 1.7; font-weight: 700; }}
        .full-response-panel {{ margin: 0; border: 1px solid rgba(105, 132, 188, 0.14); border-radius: var(--radius-lg); background: rgba(243, 246, 255, 0.72); overflow: hidden; }}
        .full-response-toggle {{ cursor: pointer; list-style: none; padding: 14px 16px; font-weight: 700; color: #36516f; background: rgba(232, 239, 252, 0.86); }}
        .full-response-toggle::-webkit-details-marker {{ display: none; }}
        .full-response-toggle::after {{ content: "展开"; float: right; font-size: 13px; color: #52708d; }}
        .full-response-panel[open] .full-response-toggle::after {{ content: "收起"; }}
        .full-ai-response {{ white-space: pre-wrap; background: linear-gradient(180deg, rgba(236, 242, 252, 0.95) 0%, rgba(243, 246, 255, 0.95) 100%); padding: 14px; border-radius: var(--radius-lg); border: 1px solid rgba(105, 132, 188, 0.14); line-height: 1.72; }}
        .grouped-results {{ align-items: start; }}
        .grouped-result-card {{ display: grid; gap: 14px; padding: 22px; }}
        .extracted-review-area {{ display: grid; gap: 16px; margin-top: 14px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); align-items: start; }}
        .phrase-box {{ background: rgba(255, 253, 248, 0.92); border: 1px solid rgba(145, 112, 76, 0.12); border-radius: var(--radius-lg); padding: 14px; box-shadow: 0 8px 20px rgba(92, 62, 30, 0.05); }}
        .submission-feedback {{ display: grid; gap: 12px; margin-top: 14px; }}
        .submission-outcome-summary {{ padding: 16px 18px; border-radius: 18px; border: 1px solid rgba(145, 112, 76, 0.12); }}
        .submission-outcome-summary-submitted {{ background: linear-gradient(135deg, rgba(227, 244, 232, 0.96) 0%, rgba(242, 249, 244, 0.96) 100%); color: #244b2e; }}
        .submission-outcome-summary-mixed, .submission-outcome-summary-skipped {{ background: linear-gradient(135deg, rgba(251, 241, 214, 0.96) 0%, rgba(255, 248, 230, 0.96) 100%); color: #694d14; }}
        .submission-outcome-summary-partial, .submission-outcome-summary-failed {{ background: linear-gradient(135deg, rgba(252, 229, 222, 0.96) 0%, rgba(255, 242, 238, 0.96) 100%); color: #702f1f; }}
        .submission-outcome-summary-label {{ margin: 0; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.8; }}
        .submission-outcome-summary-title {{ margin: 6px 0 0; font-size: 22px; }}
        .submission-outcome-summary-text {{ margin: 8px 0 0; line-height: 1.6; }}
        .submission-outcome {{ border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 12px; background: rgba(248, 251, 252, 0.92); display: grid; gap: 10px; }}
        .submission-outcome-header h3, .submission-outcome-header p {{ margin: 0; }}
        .submission-outcome-header {{ display: grid; gap: 4px; }}
        .submission-outcome-list {{ display: grid; gap: 8px; padding-left: 20px; margin: 0; }}
        .submission-outcome-item {{ display: grid; gap: 2px; }}
        .submission-outcome-front {{ font-weight: 700; color: #2f2d2b; }}
        .submission-outcome-back {{ color: #6b6f76; }}
        .submission-error-message {{ margin: 0; padding: 12px 14px; border-radius: 14px; background: rgba(255, 240, 235, 0.92); border: 1px solid rgba(181, 83, 52, 0.16); color: #7f321c; }}
        @media (max-width: 720px) {{
            main {{ padding: 20px 14px 40px; }}
            .page-hero {{ padding: 22px 18px; border-radius: 24px; }}
            .review-overview {{ position: static; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .deck-selection-area, .copy-export-area, .grouped-result-card {{ padding: 16px; border-radius: 20px; }}
            .deck-selection-header {{ grid-template-columns: 1fr; }}
            .action-bar {{ display: grid; }}
            button {{ width: 100%; justify-content: center; }}
        }}
    </style>
</head>
<body>
    <main>
        <section class=\"page-hero\">
            <span class=\"eyebrow\">个人英语词组卡片台</span>
            <h1>英语词组制卡工作台</h1>
            <p class=\"page-intro\">输入一个或多个单词，生成完整解析，核对复制专用提取结果，再把真正有价值的词组送进你的 Anki Deck。</p>
        </section>
        <form method=\"post\"><div class=\"generation-pending-banner\" data-generation-pending-banner aria-live=\"polite\"><p class=\"generation-pending-label\">生成中</p><p class=\"generation-pending-text\">正在等待 AI 返回结果，请稍候，页面会在完成后自动刷新。</p></div><div class=\"submission-pending-banner\" data-submission-pending-banner aria-live=\"polite\"><p class=\"submission-pending-label\">提交中</p><p class=\"submission-pending-text\">正在提交选中词组到 Anki，请稍候，完成后会在页面顶部显示结果摘要。</p></div>{workspace_html}<div class=\"action-bar\"><button type=\"submit\" name=\"action\" value=\"add-input\" class=\"secondary-action\">新增输入框</button><button type=\"submit\" name=\"action\" value=\"generate\">开始生成</button><button type=\"submit\" name=\"action\" value=\"submit\">提交选中词组</button></div></form>
    </main>
    <script>
        var EXPORT_OPTION_STORAGE_KEY = "copy-format-export-options";

        function escapeHtml(value) {{
            return value
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
        }}

        function loadExportOptions() {{
            try {{
                var raw = window.localStorage.getItem(EXPORT_OPTION_STORAGE_KEY);
                return raw ? JSON.parse(raw) : {{}};
            }} catch (error) {{
                return {{}};
            }}
        }}

        function saveExportOptions(container) {{
            try {{
                var payload = {{
                    trim: !!container.querySelector('[data-export-option="trim"]:checked'),
                    dedupeFront: !!container.querySelector('[data-export-option="dedupe-front"]:checked')
                }};
                window.localStorage.setItem(EXPORT_OPTION_STORAGE_KEY, JSON.stringify(payload));
            }} catch (error) {{
                return;
            }}
        }}

        function restoreExportOptions(container) {{
            var options = loadExportOptions();
            var trimInput = container.querySelector('[data-export-option="trim"]');
            var dedupeInput = container.querySelector('[data-export-option="dedupe-front"]');
            if (trimInput instanceof HTMLInputElement && typeof options.trim === "boolean") {{
                trimInput.checked = options.trim;
            }}
            if (dedupeInput instanceof HTMLInputElement && typeof options.dedupeFront === "boolean") {{
                dedupeInput.checked = options.dedupeFront;
            }}
        }}

        function buildExportPayload(container) {{
            var shouldTrim = !!container.querySelector('[data-export-option="trim"]:checked');
            var shouldDedupeFront = !!container.querySelector('[data-export-option="dedupe-front"]:checked');
            var cards = document.querySelectorAll(".grouped-result-card");
            var grouped = [];
            var orderedFrontKeys = [];
            var chosenEntriesByFront = new Map();

            cards.forEach(function(card) {{
                if (!(card instanceof HTMLElement)) {{
                    return;
                }}
                var inputWord = card.getAttribute("data-input-word") || "";
                var phraseBoxes = card.querySelectorAll(".phrase-box");
                var phrases = [];
                phraseBoxes.forEach(function(box) {{
                    if (!(box instanceof HTMLElement)) {{
                        return;
                    }}
                    var checkbox = box.querySelector(".phrase-select-input");
                    var lockInput = box.querySelector(".phrase-lock-input");
                    var frontField = box.querySelector(".phrase-front-input");
                    var backField = box.querySelector(".phrase-back-input");
                    if (!(checkbox instanceof HTMLInputElement) || !(lockInput instanceof HTMLInputElement) || !(frontField instanceof HTMLTextAreaElement) || !(backField instanceof HTMLTextAreaElement) || !checkbox.checked) {{
                        return;
                    }}
                    var front = shouldTrim ? frontField.value.trim() : frontField.value;
                    var back = shouldTrim ? backField.value.trim() : backField.value;
                    if (!front.trim() || !back.trim()) {{
                        return;
                    }}
                    if (!shouldDedupeFront) {{
                        phrases.push({{ front: front, back: back }});
                        return;
                    }}
                    var frontKey = front.toLocaleLowerCase();
                    var nextEntry = {{
                        inputWord: inputWord,
                        phrase: {{ front: front, back: back }},
                        locked: lockInput.checked
                    }};
                    if (!chosenEntriesByFront.has(frontKey)) {{
                        orderedFrontKeys.push(frontKey);
                        chosenEntriesByFront.set(frontKey, nextEntry);
                        return;
                    }}
                    var existingEntry = chosenEntriesByFront.get(frontKey);
                    if (nextEntry.locked && existingEntry && !existingEntry.locked) {{
                        chosenEntriesByFront.set(frontKey, nextEntry);
                    }}
                }});
                if (phrases.length) {{
                    grouped.push({{ inputWord: inputWord, phrases: phrases }});
                }}
            }});

            if (shouldDedupeFront) {{
                grouped = [];
                orderedFrontKeys.forEach(function(frontKey) {{
                    var chosenEntry = chosenEntriesByFront.get(frontKey);
                    if (!chosenEntry) {{
                        return;
                    }}
                    var lastGroup = grouped[grouped.length - 1];
                    if (lastGroup && lastGroup.inputWord === chosenEntry.inputWord) {{
                        lastGroup.phrases.push(chosenEntry.phrase);
                        return;
                    }}
                    grouped.push({{
                        inputWord: chosenEntry.inputWord,
                        phrases: [chosenEntry.phrase]
                    }});
                }});
            }}

            return grouped;
        }}

        function buildPlainText(grouped) {{
            return grouped.map(function(group) {{
                var lines = ["[" + group.inputWord + "]"];
                group.phrases.forEach(function(item) {{
                    lines.push(item.front + " - " + item.back);
                }});
                return lines.join("\\\\n");
            }}).join("\\\\n\\\\n");
        }}

        function buildMarkdown(grouped) {{
            return grouped.map(function(group) {{
                var lines = ["## " + group.inputWord];
                group.phrases.forEach(function(item) {{
                    lines.push("- " + item.front + ": " + item.back);
                }});
                return lines.join("\\\\n");
            }}).join("\\\\n\\\\n");
        }}

        function buildAnkiText(grouped) {{
            var lines = [];
            grouped.forEach(function(group) {{
                group.phrases.forEach(function(item) {{
                    lines.push(item.front + "\t" + item.back);
                }});
            }});
            return lines.join("\\\\n");
        }}

        function setPanelValue(panel, value) {{
            panel.value = value;
            panel.textContent = value;
            panel.setAttribute("rows", String(Math.max(value.split("\\\\n").length, 1)));
        }}

        function buildSubmissionPreviewCards(grouped) {{
            return grouped.map(function(group) {{
                var cards = group.phrases.map(function(item) {{
                    return [
                        '<article class="submission-preview-card">',
                        '<p class="submission-preview-card-front">' + escapeHtml(item.front) + '</p>',
                        '<p class="submission-preview-card-back">' + escapeHtml(item.back) + '</p>',
                        '</article>'
                    ].join("");
                }}).join("");
                return [
                    '<section class="submission-preview-group">',
                    '<h4 class="submission-preview-group-title">' + escapeHtml(group.inputWord) + '</h4>',
                    '<div class="submission-preview-card-list">' + cards + '</div>',
                    '</section>'
                ].join("");
            }}).join("");
        }}

        function refreshCopyExportArea() {{
            var container = document.querySelector(".copy-export-area");
            if (!(container instanceof HTMLElement)) {{
                return;
            }}
            var grouped = buildExportPayload(container);
            var values = {{
                plain: buildPlainText(grouped),
                markdown: buildMarkdown(grouped),
                anki: buildAnkiText(grouped)
            }};
            ["plain", "markdown", "anki"].forEach(function(format) {{
                var panel = document.getElementById("copy-export-text-" + format);
                if (panel instanceof HTMLTextAreaElement) {{
                    setPanelValue(panel, values[format]);
                }}
            }});
            var help = container.querySelector(".copy-export-help");
            if (help instanceof HTMLElement) {{
                help.textContent = grouped.length ? "仅汇总当前勾选的词组，默认会清理首尾空白并按英文词组去重。" : "当前没有可导出的已勾选词组。";
            }}
            var submissionPreview = document.getElementById("submission-preview-cards");
            if (submissionPreview instanceof HTMLElement) {{
                submissionPreview.innerHTML = buildSubmissionPreviewCards(grouped);
            }}
            var feedback = container.querySelector("[data-copy-feedback]");
            if (feedback instanceof HTMLElement) {{
                feedback.textContent = "";
            }}
        }}

        function filterDeckOptions(searchInput, select, feedback) {{
            var query = searchInput.value.trim().toLocaleLowerCase();
            var currentValue = select.value;
            var originalOptions = select.__originalDeckOptions || [];
            var matchingCount = 0;
            select.innerHTML = "";

            originalOptions.forEach(function(optionData) {{
                var matches = !query || optionData.label.toLocaleLowerCase().indexOf(query) !== -1;
                var shouldKeep = matches || optionData.value === currentValue;
                if (!shouldKeep) {{
                    return;
                }}
                if (matches) {{
                    matchingCount += 1;
                }}
                var option = document.createElement("option");
                option.value = optionData.value;
                option.textContent = optionData.label;
                if (optionData.value === currentValue) {{
                    option.selected = true;
                }}
                select.appendChild(option);
            }});

            if (!select.options.length && originalOptions.length) {{
                originalOptions.forEach(function(optionData) {{
                    var option = document.createElement("option");
                    option.value = optionData.value;
                    option.textContent = optionData.label;
                    select.appendChild(option);
                }});
                select.value = currentValue;
            }}

            if (!(feedback instanceof HTMLElement)) {{
                return;
            }}
            if (!query) {{
                feedback.textContent = "";
            }} else if (matchingCount > 0) {{
                feedback.textContent = "已筛出 " + matchingCount + " 个 deck";
            }} else if (currentValue) {{
                feedback.textContent = "没有匹配的 deck，已保留当前选中项。";
            }} else {{
                feedback.textContent = "没有匹配的 deck";
            }}
        }}

        function initDeckSearch() {{
            var searchInput = document.querySelector("[data-deck-search]");
            var select = document.querySelector("[data-deck-selection]");
            var feedback = document.querySelector("[data-deck-feedback]");
            if (!(searchInput instanceof HTMLInputElement) || !(select instanceof HTMLSelectElement)) {{
                return;
            }}
            select.__originalDeckOptions = Array.prototype.map.call(select.options, function(option) {{
                return {{ value: option.value, label: option.textContent || option.value }};
            }});
            searchInput.addEventListener("input", function() {{
                filterDeckOptions(searchInput, select, feedback);
            }});
            select.addEventListener("change", function() {{
                filterDeckOptions(searchInput, select, feedback);
            }});
            filterDeckOptions(searchInput, select, feedback);
        }}

        function initGenerationPendingState() {{
            var form = document.querySelector("form");
            if (!(form instanceof HTMLFormElement)) {{
                return;
            }}
            form.addEventListener("submit", function(event) {{
                var submitEvent = event;
                var submitter = submitEvent.submitter;
                if (!(submitter instanceof HTMLButtonElement) || submitter.value !== "generate") {{
                    return;
                }}
                var banner = form.querySelector("[data-generation-pending-banner]");
                if (banner instanceof HTMLElement) {{
                    banner.classList.add("is-visible");
                }}
                form.querySelectorAll('button[name="action"][value="generate"]').forEach(function(button) {{
                    if (button instanceof HTMLButtonElement) {{
                        button.classList.add("is-pending");
                        button.setAttribute("aria-disabled", "true");
                        button.textContent = "生成中...";
                    }}
                }});
            }});
        }}

        function initSubmissionPendingState() {{
            var form = document.querySelector("form");
            if (!(form instanceof HTMLFormElement)) {{
                return;
            }}
            form.addEventListener("submit", function(event) {{
                var submitEvent = event;
                var submitter = submitEvent.submitter;
                if (!(submitter instanceof HTMLButtonElement) || submitter.value !== "submit") {{
                    return;
                }}
                var banner = form.querySelector("[data-submission-pending-banner]");
                if (banner instanceof HTMLElement) {{
                    banner.classList.add("is-visible");
                }}
                form.querySelectorAll('button[name="action"][value="submit"]').forEach(function(button) {{
                    if (button instanceof HTMLButtonElement) {{
                        button.classList.add("is-pending");
                        button.setAttribute("aria-disabled", "true");
                        button.textContent = "提交中...";
                    }}
                }});
            }});
        }}

        function activateExportFormat(button) {{
            var format = button.getAttribute("data-export-format");
            if (!format) {{
                return;
            }}
            var container = button.closest(".copy-export-area");
            if (!(container instanceof HTMLElement)) {{
                return;
            }}
            var buttons = container.querySelectorAll(".copy-export-format-button");
            buttons.forEach(function(item) {{
                if (item instanceof HTMLElement) {{
                    item.classList.toggle("is-active", item === button);
                }}
            }});
            var panels = container.querySelectorAll(".copy-export-text");
            panels.forEach(function(panel) {{
                if (!(panel instanceof HTMLElement)) {{
                    return;
                }}
                var isActive = panel.getAttribute("data-export-panel") === format;
                panel.classList.toggle("is-active", isActive);
                panel.hidden = !isActive;
            }});
            var copyButton = container.querySelector("[data-copy-target]");
            if (copyButton instanceof HTMLElement) {{
                copyButton.setAttribute("data-copy-target", "copy-export-text-" + format);
            }}
            var feedback = container.querySelector("[data-copy-feedback]");
            if (feedback instanceof HTMLElement) {{
                feedback.textContent = "";
            }}
        }}

        document.addEventListener("input", function(event) {{
            var target = event.target;
            if (!(target instanceof HTMLElement)) {{
                return;
            }}
            if (target.matches(".phrase-front-input, .phrase-back-input")) {{
                refreshCopyExportArea();
            }}
        }});

        document.addEventListener("change", function(event) {{
            var target = event.target;
            if (!(target instanceof HTMLElement)) {{
                return;
            }}
            if (target.matches(".phrase-select-input, .phrase-lock-input, .copy-export-option-input")) {{
                var exportContainer = document.querySelector(".copy-export-area");
                if (exportContainer instanceof HTMLElement) {{
                    saveExportOptions(exportContainer);
                }}
                refreshCopyExportArea();
            }}
        }});

        document.addEventListener("click", function(event) {{
            var target = event.target;
            if (!(target instanceof HTMLElement)) {{
                return;
            }}
            if (target.matches(".copy-export-format-button")) {{
                activateExportFormat(target);
                return;
            }}
            if (!target.matches("[data-copy-target]")) {{
                return;
            }}
            var textAreaId = target.getAttribute("data-copy-target");
            if (!textAreaId) {{
                return;
            }}
            var textArea = document.getElementById(textAreaId);
            if (!(textArea instanceof HTMLTextAreaElement)) {{
                return;
            }}
            textArea.select();
            textArea.setSelectionRange(0, textArea.value.length);
            var container = target.closest(".copy-export-area");
            var feedback = container ? container.querySelector("[data-copy-feedback]") : null;
            var onSuccess = function(message) {{
                if (feedback instanceof HTMLElement) {{
                    feedback.textContent = message;
                }}
            }};
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(textArea.value).then(
                    function() {{ onSuccess("已复制到剪贴板"); }},
                    function() {{
                        document.execCommand("copy");
                        onSuccess("已复制到剪贴板");
                    }}
                );
                return;
            }}
            document.execCommand("copy");
            onSuccess("已复制到剪贴板");
        }});

        var initialExportContainer = document.querySelector(".copy-export-area");
        if (initialExportContainer instanceof HTMLElement) {{
            restoreExportOptions(initialExportContainer);
        }}
        initDeckSearch();
        initGenerationPendingState();
        initSubmissionPendingState();
        refreshCopyExportArea();
    </script>
</body>
</html>"""


def run_local_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    app = create_web_app()
    try:
        with make_server(host, port, app) as httpd:
            print(f"Serving review workspace on http://{host}:{port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping review workspace server.")


def main() -> None:
    port_value = __import__("os").environ.get(PORT_ENV, str(DEFAULT_PORT)).strip()
    run_local_server(host=DEFAULT_HOST, port=int(port_value))


def _read_form_data(environ) -> dict[str, str]:
    content_length_value = str(environ.get("CONTENT_LENGTH", "0") or "0")
    content_length = int(content_length_value) if content_length_value.isdigit() else 0
    raw_body = environ["wsgi.input"].read(content_length)
    parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def _apply_request_to_workspace(
    workspace: WorkspaceControllerProtocol,
    form_data: dict[str, str],
) -> None:
    _sync_input_blocks(workspace, form_data)

    action = form_data.get("action", "").strip()
    if action == "add-input":
        workspace.add_input_block()
        return

    if action == "generate":
        workspace.generate_results()
        return

    if action == "submit":
        workspace.select_deck(form_data.get("selected_deck", ""))
        _sync_phrase_edits(workspace, form_data)
        workspace.submit_selected_pairs()
        return


def _sync_input_blocks(
    workspace: WorkspaceControllerProtocol,
    form_data: dict[str, str],
) -> None:
    indexed_fields = sorted(
        (
            int(key.removeprefix("input_word_")),
            value,
        )
        for key, value in form_data.items()
        if key.startswith("input_word_") and key.removeprefix("input_word_").isdigit()
    )
    if not indexed_fields:
        return

    while len(workspace.state.input_blocks) < len(indexed_fields):
        workspace.add_input_block()

    for index, value in indexed_fields:
        workspace.update_input_block(index, value)


def _sync_phrase_edits(
    workspace: WorkspaceControllerProtocol,
    form_data: dict[str, str],
) -> None:
    for group_index, result_group in enumerate(workspace.state.result_groups):
        for phrase_index, _phrase_pair in enumerate(result_group.extracted_phrases):
            front_key = f"phrase_front_{group_index}_{phrase_index}"
            back_key = f"phrase_back_{group_index}_{phrase_index}"
            selected_key = f"phrase_selected_{group_index}_{phrase_index}"
            locked_key = f"phrase_lock_{group_index}_{phrase_index}"

            if front_key in form_data:
                workspace.edit_phrase(
                    group_index=group_index,
                    phrase_index=phrase_index,
                    front_value=form_data[front_key],
                )
            if back_key in form_data:
                workspace.edit_phrase(
                    group_index=group_index,
                    phrase_index=phrase_index,
                    back_value=form_data[back_key],
                )

            workspace.set_phrase_selected(
                group_index=group_index,
                phrase_index=phrase_index,
                selected=selected_key in form_data,
            )
            workspace.set_phrase_locked(
                group_index=group_index,
                phrase_index=phrase_index,
                locked=locked_key in form_data,
            )


def _load_callable_from_target(target: str) -> GenerationCallable:
    module_path_text, separator, callable_name = target.partition(":")
    if not separator or not module_path_text.strip() or not callable_name.strip():
        raise ValueError(
            f"{GENERATION_CALLABLE_ENV} must use '<file-path>:<callable-name>' format."
        )

    module_path = Path(module_path_text).expanduser().resolve()
    module_name = f"copy_format_generation_adapter_{module_path.stem}"
    spec = util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ValueError(
            f"Could not load generation adapter module from {module_path}."
        )

    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded_callable = getattr(module, callable_name)
    if not callable(loaded_callable):
        raise TypeError(
            f"Configured generation adapter '{callable_name}' is not callable."
        )
    return loaded_callable


def _safe_list_decks(gateway: AnkiConnectGateway) -> list[str]:
    try:
        return gateway.list_deck_names()
    except Exception:
        return []


if __name__ == "__main__":
    main()
