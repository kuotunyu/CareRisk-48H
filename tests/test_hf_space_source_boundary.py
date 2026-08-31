"""AST-only contract for the isolated public Space application surface."""

from __future__ import annotations

import ast
import importlib
from collections.abc import Iterable
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SPACE_ROOT = REPOSITORY_ROOT / "space"
APP_SOURCES = (SPACE_ROOT / "app.py", *sorted((SPACE_ROOT / "carerisk_space").glob("*.py")))
APP_ENTRY = SPACE_ROOT / "app.py"
UI_SOURCE = SPACE_ROOT / "carerisk_space" / "ui.py"

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "collections",
    "dataclasses",
    "hashlib",
    "html",
    "json",
    "logging",
    "math",
    "pathlib",
    "re",
    "stat",
    "types",
    "typing",
    "fastapi",
    "gradio",
    "starlette",
    "uvicorn",
    "carerisk_space",
}
FORBIDDEN_IMPORT_ROOTS = {
    "app",
    "carerisk48h",
    "joblib",
    "pickle",
    "cloudpickle",
    "dill",
    "numpy",
    "pandas",
    "scipy",
    "sklearn",
    "lightgbm",
    "shap",
    "torch",
    "tensorflow",
    "onnx",
    "matplotlib",
    "plotly",
    "requests",
    "httpx",
    "urllib",
    "huggingface_hub",
    "socket",
    "subprocess",
}

_WRITE_METHODS = {
    "chmod",
    "chown",
    "mkdir",
    "rename",
    "replace",
    "rmdir",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
}
_READ_METHODS = {"open", "read_text", "read_bytes"}
_DYNAMIC_OR_PROCESS_CALLS = {
    "__import__",
    "eval",
    "exec",
    "execv",
    "execve",
    "import_module",
    "popen",
    "spawn",
    "system",
}
_DISCOVERY_METHODS = {"absolute", "cwd", "glob", "home", "site", "user"}
_NETWORK_OR_WATCHER_NAMES = {
    "AsyncClient",
    "Client",
    "Connection",
    "Session",
    "Watcher",
    "socket",
    "watch",
    "watchfiles",
}
_PROCESS_CALLS = {
    "asyncio.create_subprocess_exec",
    "asyncio.create_subprocess_shell",
    "os.execv",
    "os.execve",
    "os.popen",
    "os.spawn",
    "os.system",
    "subprocess.Popen",
    "subprocess.run",
}


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _called_attribute(node: ast.Call) -> str | None:
    return node.func.attr if isinstance(node.func, ast.Attribute) else None


def imported_roots(paths: Iterable[Path]) -> set[str]:
    """Return import roots without importing the public application package."""

    roots: set[str] = set()
    for path in paths:
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    roots.add("carerisk_space")
                elif node.module:
                    roots.add(node.module.split(".", 1)[0])
    return roots


def scan_capabilities(paths: Iterable[Path]) -> list[str]:
    """Find capability-bearing source constructs that have no public-Space role."""

    violations: list[str] = []
    for path in paths:
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Attribute) and node.attr == "environ":
                violations.append(f"{path.name}:environment")
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            attr = _called_attribute(node)
            if name == "open":
                mode = next((item.value for item in node.keywords if item.arg == "mode"), None)
                if len(node.args) > 1:
                    mode = node.args[1]
                if (
                    not isinstance(mode, ast.Constant)
                    or not isinstance(mode.value, str)
                    or any(marker in mode.value for marker in "wax+")
                ):
                    violations.append(f"{path.name}:open")
            if attr in _WRITE_METHODS:
                violations.append(f"{path.name}:{attr}")
            if attr in _READ_METHODS:
                if attr == "read_bytes" and path.name == "evidence.py":
                    continue
                violations.append(f"{path.name}:{attr}")
            if name in _DYNAMIC_OR_PROCESS_CALLS or name == "importlib.import_module":
                violations.append(f"{path.name}:{attr or name}")
            if name in _PROCESS_CALLS:
                violations.append(f"{path.name}:{attr}")
            if attr in _DISCOVERY_METHODS:
                violations.append(f"{path.name}:{attr}")
            if name == "Path" and node.args and isinstance(node.args[0], ast.Constant):
                value = node.args[0].value
                if isinstance(value, str) and (value.startswith("/") or value.startswith("~")):
                    violations.append(f"{path.name}:absolute_path")
            if name and name.startswith("os.path."):
                violations.append(f"{path.name}:os_path")
            if attr in _NETWORK_OR_WATCHER_NAMES or name in _NETWORK_OR_WATCHER_NAMES:
                violations.append(f"{path.name}:{attr or name}")
    return violations


def _imports(path: Path) -> set[tuple[str, tuple[str, ...]]]:
    records: set[tuple[str, tuple[str, ...]]] = set()
    for node in _tree(path).body:
        if isinstance(node, ast.Import):
            records.update((alias.name, (alias.asname or alias.name,)) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            records.add((prefix, tuple(alias.name for alias in node.names)))
    return records


def _ui_framework_violations(tree: ast.Module) -> list[str]:
    """Allow only the named Gradio and Starlette imports with their exact aliases."""

    violations: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "gradio" and alias.asname == "gr":
                    continue
                if alias.name.split(".", 1)[0] == "gradio":
                    violations.add("gradio_import")
                if alias.name.split(".", 1)[0] == "starlette":
                    violations.add("starlette_import")
        elif isinstance(node, ast.ImportFrom):
            imported = tuple((alias.name, alias.asname) for alias in node.names)
            if node.module == "gradio.routes":
                expected: tuple[tuple[str, str | None], ...] = (
                    ("BUILD_PATH_LIB", None),
                    ("STATIC_PATH_LIB", None),
                )
                if imported != expected:
                    violations.add("gradio_import")
            elif node.module and node.module.split(".", 1)[0] == "gradio":
                violations.add("gradio_import")
            elif node.module == "starlette.types":
                expected = (("ASGIApp", None), ("Receive", None), ("Scope", None), ("Send", None))
                if imported != expected:
                    violations.add("starlette_import")
            elif node.module and node.module.split(".", 1)[0] == "starlette":
                violations.add("starlette_import")
    gradio_members = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "gr"
    }
    if gradio_members != {"Blocks", "HTML"}:
        violations.add("gradio_member")
    return sorted(violations)


def _is_main_guard(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    return (
        len(node.test.ops) == len(node.test.comparators) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "__main__"
    )


def _entrypoint_violations(tree: ast.Module) -> list[str]:
    """Require the only server call to be reached solely through the main guard."""

    violations: set[str] = set()
    main_guards = [node for node in tree.body if _is_main_guard(node)]
    main_functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    uvicorn_calls = _calls(tree, "uvicorn.run")
    if len(main_guards) != 1 or len(main_functions) != 1 or len(uvicorn_calls) != 1:
        violations.add("uvicorn_main_guard")
    else:
        assert isinstance(main_guards[0], ast.If)
        guard_calls = [
            node
            for node in main_guards[0].body
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and _call_name(node.value.func) == "main"
            and not node.value.args
            and not node.value.keywords
        ]
        if len(guard_calls) != 1 or uvicorn_calls[0] not in ast.walk(main_functions[0]):
            violations.add("uvicorn_main_guard")
    mounts = _calls(tree, "gr.mount_gradio_app")
    if len(mounts) != 1:
        violations.add("mount_count")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name == "parent.add_middleware":
            violations.add("parent_middleware")
        if name in {
            "parent.add_api_route",
            "parent.get",
            "parent.include_router",
            "parent.post",
            "parent.route",
        }:
            violations.add("parent_route")
        if name == "setattr":
            violations.add("framework_monkeypatch")
    return sorted(violations)


def _guard_constructor_violations(constructor: ast.FunctionDef) -> list[str]:
    arguments = constructor.args
    if (
        arguments.posonlyargs
        or [item.arg for item in arguments.args] != ["self", "downstream", "package_asset_urls"]
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kwarg is not None
        or arguments.defaults
        or arguments.kw_defaults
    ):
        return ["guard_signature"]
    return []


def _calls(tree: ast.AST, dotted_name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node.func) == dotted_name
    ]


def _literal_keywords(call: ast.Call) -> dict[str, object]:
    return {
        item.arg: ast.literal_eval(item.value) for item in call.keywords if item.arg is not None
    }


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _asset_builder_violations(tree: ast.Module) -> list[str]:
    function = _function(tree, "build_package_asset_membership")
    root_loops = [
        node
        for node in function.body
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Tuple)
        and [item.id for item in node.target.elts if isinstance(item, ast.Name)]
        == ["raw_root", "prefix"]
        and isinstance(node.iter, ast.Tuple)
    ]
    names = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and node.id in {"BUILD_PATH_LIB", "STATIC_PATH_LIB"}
    }
    required_calls = {
        "root.is_symlink",
        "root.resolve",
        "resolved_root.is_dir",
        "root.rglob",
        "candidate.is_symlink",
        "candidate.is_dir",
        "candidate.is_file",
        "candidate.resolve",
        "resolved.relative_to",
    }
    calls = {
        _call_name(node.func)
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and _call_name(node.func) is not None
    }
    violations: list[str] = []
    if len(root_loops) != 1:
        violations.append("asset_root_dataflow")
    else:
        root_loop = root_loops[0]
        assert isinstance(root_loop, ast.For)
        assert isinstance(root_loop.iter, ast.Tuple)
        root_pairs = root_loop.iter.elts
        expected_pairs = (("BUILD_PATH_LIB", "/assets/"), ("STATIC_PATH_LIB", "/static/"))
        actual_pairs: list[tuple[str, str]] = []
        for pair in root_pairs:
            if (
                isinstance(pair, ast.Tuple)
                and len(pair.elts) == 2
                and isinstance(pair.elts[0], ast.Name)
                and isinstance(pair.elts[1], ast.Constant)
                and isinstance(pair.elts[1].value, str)
            ):
                actual_pairs.append((pair.elts[0].id, pair.elts[1].value))
        if tuple(actual_pairs) != expected_pairs:
            violations.append("asset_root_dataflow")
        root_assignments = [
            node
            for node in root_loop.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "root"
            and isinstance(node.value, ast.Call)
            and _call_name(node.value.func) == "Path"
            and len(node.value.args) == 1
            and isinstance(node.value.args[0], ast.Name)
            and node.value.args[0].id == "raw_root"
        ]
        if len(root_assignments) != 1:
            violations.append("asset_root_dataflow")
    if names != {"BUILD_PATH_LIB", "STATIC_PATH_LIB"}:
        violations.append("asset_roots")
    if not required_calls <= calls:
        violations.append("asset_read_only_walk")
    if not any(
        isinstance(node, ast.Call)
        and _call_name(node.func) == "root.resolve"
        and _literal_keywords(node).get("strict") is True
        for node in ast.walk(function)
    ):
        violations.append("asset_strict_root_resolution")
    if not any(
        isinstance(node, ast.Call)
        and _call_name(node.func) == "candidate.resolve"
        and _literal_keywords(node).get("strict") is True
        for node in ast.walk(function)
    ):
        violations.append("asset_strict_file_resolution")
    if not any(
        isinstance(node, ast.Attribute) and node.attr == "casefold" for node in ast.walk(function)
    ):
        violations.append("asset_case_sensitive_membership")
    return violations


def test_application_import_graph_is_allowlisted() -> None:
    roots = imported_roots(APP_SOURCES)
    assert not roots & FORBIDDEN_IMPORT_ROOTS
    assert roots <= ALLOWED_IMPORT_ROOTS


def test_application_has_no_write_env_process_network_or_dynamic_code_capability() -> None:
    assert scan_capabilities(APP_SOURCES) == []


def test_capability_scanner_rejects_each_publicly_forbidden_capability(tmp_path: Path) -> None:
    synthetic_source = tmp_path / "synthetic.py"
    synthetic_source.write_text(
        """
open('x', 'w')
Path('x').write_text('x')
Path('x').write_bytes(b'x')
Path('x').mkdir()
Path('x').rename('y')
Path('x').replace('y')
Path('x').unlink()
Path('private').open('w')
Path('private').read_text()
Path('private').read_bytes()
os.environ['CANARY']
eval('1')
importlib.import_module('x')
subprocess.run([])
httpx.Client()
watchfiles.watch('.')
Path('/absolute')
Path.cwd()
Path.home()
Path('*.py').glob('*')
os.path.join('a', 'b')
""",
        encoding="utf-8",
    )
    violations = set(scan_capabilities((synthetic_source,)))
    assert {
        "synthetic.py:open",
        "synthetic.py:write_text",
        "synthetic.py:write_bytes",
        "synthetic.py:mkdir",
        "synthetic.py:rename",
        "synthetic.py:replace",
        "synthetic.py:unlink",
        "synthetic.py:read_text",
        "synthetic.py:read_bytes",
        "synthetic.py:environment",
        "synthetic.py:eval",
        "synthetic.py:import_module",
        "synthetic.py:run",
        "synthetic.py:Client",
        "synthetic.py:watch",
        "synthetic.py:absolute_path",
        "synthetic.py:cwd",
        "synthetic.py:home",
        "synthetic.py:glob",
        "synthetic.py:os_path",
    } <= violations


def test_ui_framework_import_scanner_rejects_extra_members_and_aliases() -> None:
    mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
    mutated.body.insert(
        0,
        ast.ImportFrom(module="gradio", names=[ast.alias(name="Radio")], level=0),
    )
    mutated.body.insert(
        0,
        ast.ImportFrom(module="starlette.responses", names=[ast.alias(name="Response")], level=0),
    )
    assert _ui_framework_violations(mutated) == [
        "gradio_import",
        "starlette_import",
    ]


def test_ui_framework_scanner_rejects_gradio_alias_expansion() -> None:
    mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
    mutated.body.append(
        ast.Expr(
            value=ast.Call(
                func=ast.Attribute(value=ast.Name(id="gr"), attr="Radio"), args=[], keywords=[]
            )
        )
    )
    assert _ui_framework_violations(mutated) == ["gradio_member"]


def test_entrypoint_has_exact_framework_imports_and_one_fixed_composition() -> None:
    assert _imports(APP_ENTRY) == {
        ("gradio", ("gr",)),
        ("uvicorn", ("uvicorn",)),
        (
            "carerisk_space.ui",
            ("PublicSurfaceGuard", "build_package_asset_membership", "create_app"),
        ),
        ("fastapi", ("FastAPI",)),
    }
    tree = _tree(APP_ENTRY)
    fastapi_calls = _calls(tree, "FastAPI")
    assert len(fastapi_calls) == 1
    assert _literal_keywords(fastapi_calls[0]) == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }
    mount_calls = _calls(tree, "gr.mount_gradio_app")
    assert len(mount_calls) == 1
    assert _literal_keywords(mount_calls[0]) == {
        "path": "/",
        "server_name": "0.0.0.0",
        "server_port": 7860,
        "footer_links": [],
        "run_history": False,
        "root_path": "",
        "allowed_paths": ["/__carerisk_no_allowed_files__"],
        "blocked_paths": ["/"],
        "favicon_path": None,
        "show_error": False,
        "max_file_size": 0,
        "ssr_mode": False,
        "enable_monitoring": False,
        "pwa": False,
        "mcp_server": False,
    }
    guard_assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and _call_name(node.value.func) == "PublicSurfaceGuard"
    )
    guard_call = guard_assignment.value
    assert isinstance(guard_call, ast.Call)
    assert len(guard_call.args) == 2
    assert _call_name(guard_call.args[0]) == "parent"
    assert isinstance(guard_call.args[1], ast.Call)
    assert _call_name(guard_call.args[1].func) == "build_package_asset_membership"
    assert not guard_call.args[1].args and not guard_call.args[1].keywords
    assert not guard_call.keywords


def test_entrypoint_has_one_h11_uvicorn_call_under_main_guard_and_no_framework_expansion() -> None:
    tree = _tree(APP_ENTRY)
    assert _entrypoint_violations(tree) == []
    uvicorn_calls = _calls(tree, "uvicorn.run")
    assert len(uvicorn_calls) == 1
    assert _literal_keywords(uvicorn_calls[0]) == {
        "host": "0.0.0.0",
        "port": 7860,
        "workers": 1,
        "http": "h11",
        "proxy_headers": False,
        "forwarded_allow_ips": "",
        "access_log": False,
        "server_header": False,
        "date_header": False,
        "reload": False,
        "factory": False,
        "env_file": None,
        "log_config": None,
    }
    main_guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and any(
            isinstance(item, ast.Constant) and item.value == "__main__"
            for item in ast.walk(node.test)
        )
    ]
    assert len(main_guards) == 1
    prohibited = {
        "Blocks.launch",
        "FastAPI.add_middleware",
        "FastAPI.get",
        "FastAPI.post",
        "FastAPI.route",
        "gr.Radio",
    }
    calls = {_call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not prohibited & calls
    assert not any(
        name and name.rsplit(".", 1)[-1] in {"click", "change", "submit"} for name in calls
    )


def test_entrypoint_scanner_rejects_a_uvicorn_call_outside_main_and_parent_middleware() -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.append(
        ast.Expr(
            value=ast.Call(
                func=ast.Attribute(value=ast.Name(id="parent"), attr="add_middleware"),
                args=[],
                keywords=[],
            )
        )
    )
    assert _entrypoint_violations(mutated) == [
        "parent_middleware",
    ]


def test_entrypoint_scanner_rejects_second_uvicorn_and_parent_route() -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.extend(
        [
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id="uvicorn"), attr="run"),
                    args=[],
                    keywords=[],
                )
            ),
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id="parent"), attr="get"),
                    args=[],
                    keywords=[],
                )
            ),
        ]
    )
    assert _entrypoint_violations(mutated) == ["parent_route", "uvicorn_main_guard"]


def test_ui_uses_only_the_pinned_framework_surface_and_asset_builder_is_fail_closed() -> None:
    tree = _tree(UI_SOURCE)
    assert _ui_framework_violations(tree) == []
    gradio_members = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "gr"
    }
    assert gradio_members == {"Blocks", "HTML"}
    assert _asset_builder_violations(tree) == []


def test_asset_builder_scanner_rejects_a_mutated_missing_pinned_root() -> None:
    mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
    for node in ast.walk(_function(mutated, "build_package_asset_membership")):
        if isinstance(node, ast.Name) and node.id == "STATIC_PATH_LIB":
            node.id = "UNAPPROVED_ROOT"
            break
    assert "asset_roots" in _asset_builder_violations(mutated)


def test_asset_builder_scanner_rejects_dead_pinned_root_references() -> None:
    mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
    function = _function(mutated, "build_package_asset_membership")
    root_loop = next(node for node in function.body if isinstance(node, ast.For))
    assert isinstance(root_loop.iter, ast.Tuple)
    first_pair = root_loop.iter.elts[0]
    assert isinstance(first_pair, ast.Tuple) and isinstance(first_pair.elts[0], ast.Name)
    first_pair.elts[0].id = "UNAPPROVED_ROOT"
    function.body.insert(0, ast.Expr(value=ast.Name(id="BUILD_PATH_LIB")))
    assert "asset_root_dataflow" in _asset_builder_violations(mutated)


def test_asset_builder_scanner_rejects_every_required_fail_closed_step() -> None:
    required = {
        "root.resolve": "asset_read_only_walk",
        "root.is_symlink": "asset_read_only_walk",
        "resolved_root.is_dir": "asset_read_only_walk",
        "candidate.is_symlink": "asset_read_only_walk",
        "candidate.is_file": "asset_read_only_walk",
        "candidate.resolve": "asset_read_only_walk",
        "resolved.relative_to": "asset_read_only_walk",
        "casefold": "asset_case_sensitive_membership",
    }
    for target, expected in required.items():
        mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
        for node in ast.walk(_function(mutated, "build_package_asset_membership")):
            if isinstance(node, ast.Call) and _call_name(node.func) == target:
                assert isinstance(node.func, ast.Attribute)
                node.func.attr = "removed"
                break
            if target == "casefold" and isinstance(node, ast.Attribute) and node.attr == "casefold":
                node.attr = "removed"
                break
        assert expected in _asset_builder_violations(mutated)


def test_public_surface_guard_has_mandatory_membership_and_entrypoint_uses_the_builder() -> None:
    tree = _tree(UI_SOURCE)
    guard = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PublicSurfaceGuard"
    )
    constructor = next(
        node for node in guard.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    assert _guard_constructor_violations(constructor) == []
    assert [argument.arg for argument in constructor.args.args] == [
        "self",
        "downstream",
        "package_asset_urls",
    ]
    assert not constructor.args.defaults
    assert any(
        isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and _call_name(node.exc.func) == "ValueError"
        and node.exc.args
        and isinstance(node.exc.args[0], ast.Constant)
        and node.exc.args[0].value == "package_asset_membership_empty"
        for node in ast.walk(constructor)
    )
    assert "PublicSurfaceGuard(parent, build_package_asset_membership())" in APP_ENTRY.read_text(
        encoding="utf-8"
    )


def test_public_surface_guard_runtime_builder_is_nonempty_and_empty_membership_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(SPACE_ROOT))
    ui_module = importlib.import_module("carerisk_space.ui")
    membership = ui_module.build_package_asset_membership()
    assert type(membership) is frozenset
    assert membership
    with pytest.raises(ValueError, match="package_asset_membership_empty"):
        ui_module.PublicSurfaceGuard(lambda scope, receive, send: None, frozenset())


def test_asset_builder_runtime_rejects_missing_file_and_symlink_roots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.syspath_prepend(str(SPACE_ROOT))
    ui_module = importlib.import_module("carerisk_space.ui")
    static_root = tmp_path / "static"
    static_root.mkdir()
    (static_root / "asset.js").write_bytes(b"public synthetic asset")
    missing_root = tmp_path / "missing"
    monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", missing_root)
    monkeypatch.setattr(ui_module, "STATIC_PATH_LIB", static_root)
    with pytest.raises(ValueError, match="package_asset_root_invalid"):
        ui_module.build_package_asset_membership()

    file_root = tmp_path / "not-a-directory"
    file_root.write_bytes(b"public synthetic asset")
    monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", file_root)
    with pytest.raises(ValueError, match="package_asset_root_invalid"):
        ui_module.build_package_asset_membership()

    target_root = tmp_path / "target"
    target_root.mkdir()
    root_link = tmp_path / "root-link"
    try:
        root_link.symlink_to(target_root, target_is_directory=True)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows account lacks symlink creation privilege")
        raise
    monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", root_link)
    with pytest.raises(ValueError, match="package_asset_root_symlink"):
        ui_module.build_package_asset_membership()


def test_existing_guard_helpers_derive_membership_from_the_pinned_builder() -> None:
    tree = _tree(SPACE_ROOT / "tests" / "test_gradio_contract.py")
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    for function in functions:
        guard_calls = _calls(function, "ui_module.PublicSurfaceGuard")
        if not guard_calls:
            continue
        builder_calls = _calls(function, "ui_module.build_package_asset_membership")
        assert builder_calls
        assert all(len(call.args) == 2 and not call.keywords for call in guard_calls)


def test_guard_constructor_scanner_rejects_variadic_or_keyword_only_parameters() -> None:
    mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
    guard = next(
        node
        for node in mutated.body
        if isinstance(node, ast.ClassDef) and node.name == "PublicSurfaceGuard"
    )
    constructor = next(
        node for node in guard.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    constructor.args.kwonlyargs.append(ast.arg(arg="optional"))
    constructor.args.kw_defaults.append(ast.Constant(value=None))
    assert _guard_constructor_violations(constructor) == [
        "guard_signature",
    ]
