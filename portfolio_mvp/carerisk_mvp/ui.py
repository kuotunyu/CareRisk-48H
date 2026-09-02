"""Static, event-free Gradio presentation for the portfolio MVP."""

from __future__ import annotations

from html import escape

import gradio as gr

from .content import EVIDENCE_STATES

SAFETY_ZH = "本頁僅使用固定合成資料作研究展示；不提供個案風險、診斷、治療或照護決策。"
SAFETY_EN = "Synthetic research demonstration only — not for clinical or care decisions."


_STYLES = """
<style>
  :root { color-scheme: light; }
  html, body { overflow-x: hidden; }
  .cr-shell, .cr-shell * { box-sizing: border-box; }
  .cr-shell {
    --ink: #172238;
    --muted: #536076;
    --line: #d8dfeb;
    --paper: #ffffff;
    --wash: #f3f6fb;
    --accent: #225c70;
    width: min(100%, 940px);
    margin: 0 auto;
    padding: clamp(18px, 4vw, 42px);
    color: var(--ink);
    background: var(--paper);
    font-family: "Aptos", "Noto Sans TC", "Microsoft JhengHei", sans-serif;
  }
  .cr-kicker {
    margin: 0 0 8px;
    color: var(--accent);
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
  }
  .cr-shell h1 {
    margin: 0;
    font-family: "Iowan Old Style", "Palatino Linotype", "Noto Serif TC", serif;
    font-size: clamp(30px, 5vw, 52px);
    line-height: 1.05;
    letter-spacing: -.035em;
  }
  .cr-subtitle {
    margin: 10px 0 0;
    color: var(--muted);
    font-size: 18px;
  }
  .cr-boundary {
    margin: 24px 0;
    padding: 16px 18px;
    border: 1px solid var(--line);
    border-left: 5px solid var(--accent);
    border-radius: 12px;
    background: var(--wash);
  }
  .cr-boundary p { margin: 0; line-height: 1.55; }
  .cr-boundary p + p { margin-top: 5px; color: var(--muted); font-size: 14px; }
  .cr-picker { margin: 0; padding: 0; border: 0; }
  .cr-picker legend { margin-bottom: 10px; font-size: 17px; font-weight: 750; }
  .cr-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .cr-option {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 48px;
    padding: 10px 12px;
    border: 1px solid var(--line);
    border-radius: 10px;
    cursor: pointer;
    background: var(--paper);
  }
  .cr-option:hover { border-color: var(--accent); }
  .cr-option:has(input:checked) {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(34, 92, 112, .14);
  }
  .cr-option:has(input:focus-visible) { outline: 3px solid #f0a34a; outline-offset: 2px; }
  .cr-option input {
    width: 22px;
    height: 22px;
    margin: 0;
    accent-color: var(--accent);
    flex: 0 0 auto;
  }
  .cr-option input:focus-visible { outline: 3px solid #f0a34a; outline-offset: 3px; }
  .cr-label { display: grid; gap: 2px; }
  .cr-label small { color: var(--muted); }
  .cr-panels { margin-top: 18px; }
  .cr-panel {
    display: none;
    padding: clamp(18px, 3vw, 28px);
    border: 1px solid var(--line);
    border-radius: 14px;
    background: var(--wash);
  }
  .cr-panel h2 { margin: 0 0 10px; font-size: clamp(21px, 3vw, 28px); }
  .cr-panel p { margin: 0; line-height: 1.65; }
  .cr-panel p + p {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--line);
    color: var(--muted);
  }
  .cr-shell:has(#state-evidence_available:checked) .cr-panel[data-state="evidence_available"],
  .cr-shell:has(#state-evidence_withheld:checked) .cr-panel[data-state="evidence_withheld"],
  .cr-shell:has(#state-schema_withheld:checked) .cr-panel[data-state="schema_withheld"],
  .cr-shell:has(#state-provenance_withheld:checked)
  .cr-panel[data-state="provenance_withheld"] { display: block; }
  @media (max-width: 640px) {
    .cr-shell { padding: 16px 14px 24px; }
    .cr-options { grid-template-columns: 1fr; }
    .cr-boundary { margin: 18px 0; }
  }
</style>
"""


def _state_controls() -> str:
    controls: list[str] = []
    for index, state in enumerate(EVIDENCE_STATES):
        state_id = escape(state.state_id, quote=True)
        checked = " checked" if index == 0 else ""
        controls.append(
            f'<label class="cr-option" for="state-{state_id}">'
            f'<input id="state-{state_id}" name="evidence-state" type="radio" '
            f'value="{state_id}"{checked}>'
            '<span class="cr-label">'
            f"<span>{escape(state.label_zh, quote=True)}</span>"
            f'<small lang="en">{escape(state.label_en, quote=True)}</small>'
            "</span></label>"
        )
    return "".join(controls)


def _state_panels() -> str:
    panels: list[str] = []
    for state in EVIDENCE_STATES:
        state_id = escape(state.state_id, quote=True)
        panels.append(
            f'<article class="cr-panel" data-state="{state_id}" aria-live="polite">'
            f"<h2>{escape(state.heading_zh, quote=True)}</h2>"
            f"<p>{escape(state.body_zh, quote=True)}</p>"
            f"<p>{escape(state.process_note_zh, quote=True)}</p>"
            "</article>"
        )
    return "".join(panels)


def render_explorer_html() -> str:
    """Render the entire fixed explorer without request-derived content."""

    return (
        _STYLES + '<section class="cr-shell" lang="zh-TW">'
        '<header><p class="cr-kicker">Research process demo</p>'
        "<h1>CareRisk 48H</h1>"
        '<p class="cr-subtitle">Synthetic Evidence Explorer</p></header>'
        '<aside class="cr-boundary" aria-label="使用限制">'
        f"<p>{escape(SAFETY_ZH, quote=True)}</p>"
        f'<p lang="en">{escape(SAFETY_EN, quote=True)}</p></aside>'
        '<fieldset class="cr-picker"><legend>查看固定合成狀態</legend>'
        f'<div class="cr-options">{_state_controls()}</div></fieldset>'
        f'<div class="cr-panels">{_state_panels()}</div>'
        "</section>"
    )


def render_unavailable_html() -> str:
    """Return a claim-safe fallback without exposing exception details."""

    return (
        _STYLES + '<section class="cr-shell" lang="zh-TW"><h1>CareRisk 48H</h1>'
        "<p>固定合成展示目前無法顯示。</p>"
        f"<p>{escape(SAFETY_ZH, quote=True)}</p>"
        f'<p lang="en">{escape(SAFETY_EN, quote=True)}</p></section>'
    )


def create_demo() -> gr.Blocks:
    """Create one static Gradio surface with no registered event dependency."""

    try:
        markup = render_explorer_html()
    except Exception:
        markup = render_unavailable_html()

    with gr.Blocks(
        title="CareRisk 48H — Synthetic Evidence Explorer",
        analytics_enabled=False,
    ) as demo:
        gr.HTML(markup, elem_id="carerisk-static-explorer")
    demo.enable_queue = False
    return demo
