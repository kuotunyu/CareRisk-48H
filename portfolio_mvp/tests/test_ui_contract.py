from __future__ import annotations

import ast
import re
from html.parser import HTMLParser
from pathlib import Path

import gradio as gr
from carerisk_mvp.ui import (
    SAFETY_EN,
    SAFETY_ZH,
    create_demo,
    render_explorer_html,
)

EXPECTED_SAFETY_ZH = "本頁僅使用固定合成資料作研究展示；不提供個案風險、診斷、治療或照護決策。"
EXPECTED_SAFETY_EN = "Synthetic research demonstration only — not for clinical or care decisions."


class MarkupRecorder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.start_tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.start_tags.append((tag, dict(attrs)))


def test_safety_copy_precedes_every_control() -> None:
    markup = render_explorer_html()
    assert SAFETY_ZH == EXPECTED_SAFETY_ZH
    assert SAFETY_EN == EXPECTED_SAFETY_EN
    assert markup.index(SAFETY_ZH) < markup.index("<input")
    assert markup.index(SAFETY_EN) < markup.index("<input")


def test_rendered_document_has_one_heading_and_four_labeled_radios() -> None:
    markup = render_explorer_html()
    parser = MarkupRecorder()
    parser.feed(markup)

    assert sum(tag == "h1" for tag, _ in parser.start_tags) == 1
    assert any(attrs.get("lang") == "zh-TW" for _, attrs in parser.start_tags)
    radios = [
        attrs for tag, attrs in parser.start_tags if tag == "input" and attrs.get("type") == "radio"
    ]
    assert len(radios) == 4
    assert {attrs["value"] for attrs in radios} == {
        "evidence_available",
        "evidence_withheld",
        "schema_withheld",
        "provenance_withheld",
    }
    label_targets = {
        attrs["for"] for tag, attrs in parser.start_tags if tag == "label" and attrs.get("for")
    }
    assert {attrs["id"] for attrs in radios} == label_targets


def test_all_states_are_prerendered_and_css_controls_visibility() -> None:
    markup = render_explorer_html()
    for state_id in (
        "evidence_available",
        "evidence_withheld",
        "schema_withheld",
        "provenance_withheld",
    ):
        assert markup.count(f'<article class="cr-panel" data-state="{state_id}"') == 1
        assert f"#{'state-' + state_id}:checked" in markup
    assert ":has(" in markup
    assert ":focus-visible" in markup
    target_height = re.search(r"\.cr-option\s*\{[^}]*min-height:\s*(\d+)px", markup)
    assert target_height and int(target_height.group(1)) >= 44
    assert re.search(r"@media\s*\(max-width:\s*640px\)", markup)
    assert "overflow-x:hidden" in markup.replace(" ", "")


def test_authored_markup_has_no_active_or_editable_surface() -> None:
    markup = render_explorer_html().casefold()
    assert not re.search(r"<(?:script|form|textarea|button|select)\b", markup)
    assert not re.search(r"\son[a-z]+\s*=", markup)
    assert 'type="file"' not in markup
    assert "contenteditable" not in markup
    assert "http://" not in markup and "https://" not in markup
    for term in ("score", "probability", "threshold", "metric", "model"):
        assert term not in markup


def test_gradio_tree_has_one_html_component_and_no_app_event() -> None:
    demo = create_demo()
    assert isinstance(demo, gr.Blocks)
    config = demo.get_config_file()
    html_components = [
        component for component in config["components"] if component["type"] == "html"
    ]
    assert len(html_components) == 1
    assert config["dependencies"] == []
    assert demo.enable_queue is False


def test_product_modules_import_no_capability_bearing_library() -> None:
    source_root = Path(__file__).parents[1]
    allowed_imports = {"__future__", "dataclasses", "html", "gradio"}
    forbidden_calls = {"open", "eval", "exec", "compile", "__import__"}

    for path in (
        source_root / "app.py",
        source_root / "carerisk_mvp" / "content.py",
        source_root / "carerisk_mvp" / "ui.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
        allowed_imports.update({"carerisk_mvp", "content"})
        assert imports <= allowed_imports
        assert (
            not {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            & forbidden_calls
        )
