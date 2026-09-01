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
_FORBIDDEN_REFLECTION_NAMES = frozenset(
    {
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "vars",
        "globals",
        "locals",
        "eval",
        "exec",
        "compile",
        "__import__",
        "__builtins__",
    }
)
_ALLOWED_DUNDER_NAME_LOADS = frozenset({"__name__", "__file__"})
_ALLOWED_DUNDER_DEFINITIONS = frozenset({"__init__", "__call__"})
_FORBIDDEN_DYNAMIC_PROTOCOL_LITERALS = frozenset(
    {"__getattribute__", "__getattr__", "__setattr__", "__delattr__"}
)
_FORBIDDEN_REFLECTION_HELPERS = frozenset(
    {"operator.attrgetter", "operator.methodcaller", "inspect.getattr_static"}
)
_FORBIDDEN_STDLIB_CLASS_FACTORIES = frozenset(
    {"make_dataclass", "namedtuple", "NamedTuple", "TypedDict"}
)
_SENSITIVE_COMPOSITION_MEMBERS = frozenset(
    {
        "mount_gradio_app",
        "run",
        "add_middleware",
        "add_api_route",
        "include_router",
        "get",
        "post",
        "route",
        "build_package_asset_membership",
        "PublicSurfaceGuard",
    }
)
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
_EXPECTED_EVIDENCE_PUBLIC_PATHS = frozenset(
    {
        "deployment-manifest.json",
        "evidence/final-result-receipt.json",
        "evidence/release-v0.2.0.json",
    }
)


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


def _module_literal_assignment(tree: ast.Module, name: str) -> object | None:
    assignments = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            or isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
        )
    ]
    if len(assignments) != 1:
        return None
    value = assignments[0].value
    if value is None:
        return None
    try:
        return ast.literal_eval(value)
    except (TypeError, ValueError):
        return None


def _is_literal_path_join(node: ast.expr, receiver: str) -> bool:
    if not isinstance(node, ast.Call) or _call_name(node.func) != f"{receiver}.joinpath":
        return False
    if len(node.args) != 1 or node.keywords or not isinstance(node.args[0], ast.Starred):
        return False
    split = node.args[0].value
    return (
        isinstance(split, ast.Call)
        and _call_name(split.func) == "relative_path.split"
        and len(split.args) == 1
        and isinstance(split.args[0], ast.Constant)
        and split.args[0].value == "/"
        and not split.keywords
    )


def _approved_evidence_read_calls(tree: ast.Module) -> set[ast.Call]:
    """Prove the sole byte read is rooted in the three public evidence names."""

    source_paths = _module_literal_assignment(tree, "_SOURCE_PATHS")
    literal_paths = _module_literal_assignment(tree, "_LITERAL_EVIDENCE_PATHS")
    if not isinstance(source_paths, dict):
        return set()
    if not isinstance(literal_paths, (set, frozenset)):
        return set()
    if set(literal_paths) != _EXPECTED_EVIDENCE_PUBLIC_PATHS:
        return set()
    if not set(source_paths) >= _EXPECTED_EVIDENCE_PUBLIC_PATHS:
        return set()

    readers = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "read_regular_file"
    ]
    if len(readers) != 1:
        return set()
    reader = readers[0]
    if (
        reader.args.posonlyargs
        or [argument.arg for argument in reader.args.args] != ["bundle_root", "relative_path"]
        or reader.args.vararg is not None
        or reader.args.kwonlyargs
        or reader.args.kwarg is not None
        or reader.args.defaults
        or reader.args.kw_defaults
    ):
        return set()
    membership_guards = [
        node
        for node in reader.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "relative_path"
        and len(node.test.ops) == len(node.test.comparators) == 1
        and isinstance(node.test.ops[0], ast.NotIn)
        and isinstance(node.test.comparators[0], ast.Name)
        and node.test.comparators[0].id == "_LITERAL_EVIDENCE_PATHS"
        and any(isinstance(item, ast.Raise) for item in node.body)
    ]
    if len(membership_guards) != 1:
        return set()
    path_assignments = [
        node
        for node in reader.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and _is_literal_path_join(node.value, "bundle_root")
    ]
    if len(path_assignments) != 1:
        return set()
    assert isinstance(path_assignments[0].targets[0], ast.Name)
    path_name = path_assignments[0].targets[0].id
    if (
        sum(
            isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == path_name
            for node in ast.walk(reader)
        )
        != 1
    ):
        return set()
    required_regular_file_calls = {
        f"{path_name}.lstat",
        "stat.S_ISLNK",
        "stat.S_ISREG",
    }
    actual_calls = {
        _call_name(node.func)
        for node in ast.walk(reader)
        if isinstance(node, ast.Call) and _call_name(node.func) is not None
    }
    if not required_regular_file_calls <= actual_calls:
        return set()
    mode_assignments = [
        node
        for node in ast.walk(reader)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "mode"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "st_mode"
        and isinstance(node.value.value, ast.Call)
        and _call_name(node.value.value.func) == f"{path_name}.lstat"
        and not node.value.value.args
        and not node.value.value.keywords
    ]
    regular_guards = [
        node
        for node in reader.body
        if isinstance(node, ast.If)
        and ast.unparse(node.test) == "stat.S_ISLNK(mode) or not stat.S_ISREG(mode)"
        and any(
            isinstance(item, ast.Raise)
            and isinstance(item.exc, ast.Name)
            and item.exc.id == "FileNotFoundError"
            for item in node.body
        )
    ]
    if len(mode_assignments) != 1 or len(regular_guards) != 1:
        return set()
    reads = [
        node
        for node in ast.walk(reader)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "read_bytes"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == path_name
    ]
    if len(reads) != 1 or not any(
        isinstance(node, ast.Return) and node.value is reads[0] for node in ast.walk(reader)
    ):
        return set()
    if not (
        membership_guards[0].lineno
        < path_assignments[0].lineno
        < mode_assignments[0].lineno
        < regular_guards[0].lineno
        < reads[0].lineno
    ):
        return set()
    reader_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node.func) == "read_regular_file"
    ]
    if (
        len(reader_calls) != len(_EXPECTED_EVIDENCE_PUBLIC_PATHS)
        or {
            call.args[1].value
            for call in reader_calls
            if len(call.args) == 2
            and not call.keywords
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == "bundle_root"
            and isinstance(call.args[1], ast.Constant)
            and isinstance(call.args[1].value, str)
        }
        != _EXPECTED_EVIDENCE_PUBLIC_PATHS
    ):
        return set()
    return {reads[0]}


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _permitted_all_target(tree: ast.AST) -> ast.Name | None:
    if not isinstance(tree, ast.Module):
        return None
    declarations: list[ast.Assign | ast.AnnAssign] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(
            isinstance(name, ast.Name) and name.id == "__all__"
            for target in targets
            for name in ast.walk(target)
        ):
            declarations.append(node)
    if len(declarations) != 1:
        return None
    declaration = declarations[0]
    if isinstance(declaration, ast.Assign):
        if (
            len(declaration.targets) != 1
            or not isinstance(declaration.targets[0], ast.Name)
            or declaration.targets[0].id != "__all__"
        ):
            return None
        target = declaration.targets[0]
    else:
        if not isinstance(declaration.target, ast.Name) or declaration.target.id != "__all__":
            return None
        target = declaration.target
    value = declaration.value
    if not isinstance(value, (ast.List, ast.Tuple)) or not all(
        isinstance(item, ast.Constant) and isinstance(item.value, str) for item in value.elts
    ):
        return None
    return target


def _has_type_binding(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id == "type"
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ):
            return True
        if isinstance(node, ast.arg) and node.arg == "type":
            return True
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == "type"
        ):
            return True
        if isinstance(node, ast.alias):
            effective_name = node.asname or node.name.split(".", 1)[0]
            if effective_name == "type":
                return True
        if isinstance(node, ast.ExceptHandler) and node.name == "type":
            return True
        if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name == "type":
            return True
        if isinstance(node, ast.MatchMapping) and node.rest == "type":
            return True
    return False


def _alias_original_and_effective_names(
    node: ast.alias,
    parent: ast.AST | None,
) -> tuple[str, str]:
    original_name = node.name.rsplit(".", 1)[-1]
    if isinstance(parent, ast.Import):
        effective_name = node.asname or node.name.split(".", 1)[0]
    else:
        effective_name = node.asname or node.name
    return original_name, effective_name


def _semantic_dunder_bindings(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    permitted_all_target: ast.Name | None,
) -> set[str]:
    violations: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            try:
                context = node.ctx
            except AttributeError:
                context = ast.Load()
            if (
                isinstance(context, (ast.Store, ast.Del))
                and _is_dunder(node.id)
                and node is not permitted_all_target
            ):
                violations.add(node.id)
        elif isinstance(node, ast.arg) and _is_dunder(node.arg):
            violations.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_exception = node.name in _ALLOWED_DUNDER_DEFINITIONS and isinstance(
                parents.get(node), ast.ClassDef
            )
            if _is_dunder(node.name) and not method_exception:
                violations.add(node.name)
        elif isinstance(node, ast.ClassDef) and _is_dunder(node.name):
            violations.add(node.name)
        elif isinstance(node, ast.alias):
            for name in _alias_original_and_effective_names(node, parents.get(node)):
                if _is_dunder(name):
                    violations.add(name)
        elif isinstance(node, ast.ExceptHandler) and node.name and _is_dunder(node.name):
            violations.add(node.name)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            if _is_dunder(node.name):
                violations.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest and _is_dunder(node.rest):
            violations.add(node.rest)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            violations.update(name for name in node.names if _is_dunder(name))
    return violations


def _permitted_type_loads(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> set[ast.Name]:
    permitted: set[ast.Name] = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Name) and node.id == "type" and isinstance(node.ctx, ast.Load)
        ):
            continue
        call = parents.get(node)
        if not (
            isinstance(call, ast.Call)
            and call.func is node
            and len(call.args) == 1
            and not isinstance(call.args[0], ast.Starred)
            and not call.keywords
        ):
            continue
        compare = parents.get(call)
        if not (
            isinstance(compare, ast.Compare)
            and compare.left is call
            and len(compare.ops) == 1
            and len(compare.comparators) == 1
            and isinstance(compare.ops[0], (ast.Is, ast.IsNot))
            and isinstance(compare.comparators[0], ast.Name)
            and compare.comparators[0].id in {"str", "int", "frozenset"}
        ):
            continue
        permitted.add(node)
    return permitted


def _dynamic_reflection_violations(tree: ast.AST) -> list[str]:
    violations: set[str] = set()
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    permitted_all_target = _permitted_all_target(tree)
    violations.update(_semantic_dunder_bindings(tree, parents, permitted_all_target))
    has_type_binding = _has_type_binding(tree)
    permitted_type_loads = set() if has_type_binding else _permitted_type_loads(tree, parents)
    if has_type_binding:
        violations.add("dynamic_type_binding")

    class_factory_modules = {"types", "dataclasses", "collections", "typing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            try:
                context = node.ctx
            except AttributeError:
                context = ast.Load()
            if isinstance(context, ast.Load):
                if node.id in _FORBIDDEN_REFLECTION_NAMES or (
                    _is_dunder(node.id) and node.id not in _ALLOWED_DUNDER_NAME_LOADS
                ):
                    violations.add(node.id)
                elif node.id == "type" and node not in permitted_type_loads:
                    violations.add("dynamic_type")
        elif isinstance(node, ast.Attribute):
            if _is_dunder(node.attr):
                violations.add(node.attr)
            call_name = _call_name(node)
            if call_name in _FORBIDDEN_REFLECTION_HELPERS:
                assert call_name is not None
                violations.add(call_name)
            if node.attr in _FORBIDDEN_STDLIB_CLASS_FACTORIES:
                violations.add("dynamic_class_factory")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in _FORBIDDEN_DYNAMIC_PROTOCOL_LITERALS
        ):
            violations.add(node.value)
        elif isinstance(node, ast.Import):
            if any(alias.name == "types" for alias in node.names):
                violations.add("dynamic_class_factory")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root == "types" and any(alias.name != "MappingProxyType" for alias in node.names):
                violations.add("dynamic_class_factory")
            if root in {"dataclasses", "collections", "typing"} and any(
                alias.name in _FORBIDDEN_STDLIB_CLASS_FACTORIES for alias in node.names
            ):
                violations.add("dynamic_class_factory")
            if root in class_factory_modules and any(alias.name == "*" for alias in node.names):
                violations.add("dynamic_class_factory")
    return sorted(violations)


def scan_capabilities(paths: Iterable[Path]) -> list[str]:
    """Find capability-bearing source constructs that have no public-Space role."""

    violations: set[str] = set()
    for path in paths:
        tree = _tree(path)
        violations.update(
            f"{path.name}:{suffix}" for suffix in _dynamic_reflection_violations(tree)
        )
        approved_evidence_reads = (
            _approved_evidence_read_calls(tree)
            if path == SPACE_ROOT / "carerisk_space" / "evidence.py"
            else set()
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "environ":
                violations.add(f"{path.name}:environment")
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
                    violations.add(f"{path.name}:open")
            if attr in _WRITE_METHODS:
                violations.add(f"{path.name}:{attr}")
            if attr in _READ_METHODS:
                if node in approved_evidence_reads:
                    continue
                violations.add(f"{path.name}:{attr}")
            if name in _DYNAMIC_OR_PROCESS_CALLS or name == "importlib.import_module":
                violations.add(f"{path.name}:{attr or name}")
            if name in _PROCESS_CALLS:
                violations.add(f"{path.name}:{attr}")
            if attr in _DISCOVERY_METHODS:
                violations.add(f"{path.name}:{attr}")
            if name == "Path" and node.args and isinstance(node.args[0], ast.Constant):
                value = node.args[0].value
                if isinstance(value, str) and (value.startswith("/") or value.startswith("~")):
                    violations.add(f"{path.name}:absolute_path")
            if name and name.startswith("os.path."):
                violations.add(f"{path.name}:os_path")
            if attr in _NETWORK_OR_WATCHER_NAMES or name in _NETWORK_OR_WATCHER_NAMES:
                violations.add(f"{path.name}:{attr or name}")
    return sorted(violations)


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
    for node in ast.walk(tree):
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


def _resolved_name(node: ast.expr, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = _resolved_name(node.value, aliases)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call) and _resolved_name(node.func, aliases) == "getattr":
        if len(node.args) != 2 or node.keywords:
            return None
        parent = _resolved_name(node.args[0], aliases)
        member = node.args[1]
        if parent and isinstance(member, ast.Constant) and isinstance(member.value, str):
            return f"{parent}.{member.value}"
    return None


def _assignment_targets(node: ast.AST) -> list[ast.expr]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    else:
        return []
    flattened: list[ast.expr] = []
    pending = list(targets)
    while pending:
        target = pending.pop()
        if isinstance(target, (ast.Tuple, ast.List)):
            pending.extend(target.elts)
        elif isinstance(target, ast.Starred):
            pending.append(target.value)
        else:
            flattened.append(target)
    return flattened


def _bounded_aliases(
    tree: ast.AST,
    roots: frozenset[str],
) -> tuple[dict[str, str], set[str]]:
    aliases: dict[str, str] = {}
    sensitive_assignments: set[str] = set()
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None
    ]
    for _ in range(len(assignments) + 1):
        changed = False
        for assignment in assignments:
            value = assignment.value
            if value is None:
                continue
            resolved = _resolved_name(value, aliases)
            if resolved is None or not any(
                resolved == root or resolved.startswith(f"{root}.") for root in roots
            ):
                continue
            for target in _assignment_targets(assignment):
                if isinstance(target, ast.Name) and aliases.get(target.id) != resolved:
                    aliases[target.id] = resolved
                    sensitive_assignments.add(resolved)
                    changed = True
        if not changed:
            break
    return aliases, sensitive_assignments


def _simple_aliases(tree: ast.Module) -> tuple[dict[str, str], set[str]]:
    return _bounded_aliases(tree, frozenset({"getattr", "gr", "main", "parent", "uvicorn"}))


def _resolved_calls(tree: ast.AST, aliases: dict[str, str], name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _resolved_name(node.func, aliases) == name
    ]


def _entrypoint_violations(tree: ast.Module) -> list[str]:
    """Require the only server call to be reached solely through the main guard."""

    violations: set[str] = set()
    if _dynamic_reflection_violations(tree):
        violations.add("builtin_reflection")
    aliases, sensitive_assignments = _simple_aliases(tree)
    main_guards = [node for node in tree.body if _is_main_guard(node)]
    main_functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    uvicorn_calls = _resolved_calls(tree, aliases, "uvicorn.run")
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
    module_main_calls = [
        node
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and _resolved_name(node.value.func, aliases) == "main"
    ]
    module_main_aliases = {
        _resolved_name(node.value, aliases)
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None
    }
    if module_main_calls or "main" in module_main_aliases:
        violations.add("uvicorn_main_guard")
    mounts = _resolved_calls(tree, aliases, "gr.mount_gradio_app")
    if len(mounts) != 1:
        violations.add("mount_count")
    if sensitive_assignments & {"gr", "uvicorn", "gr.mount_gradio_app", "uvicorn.run"}:
        violations.add("framework_alias")
    if "getattr" in sensitive_assignments or any(
        isinstance(node, ast.Call) and _resolved_name(node.func, aliases) == "getattr"
        for node in ast.walk(tree)
    ):
        violations.add("builtin_reflection")
    for node in ast.walk(tree):
        for target in _assignment_targets(node):
            if isinstance(target, ast.Attribute) and _resolved_name(target, aliases) in {
                "gr.mount_gradio_app",
                "uvicorn.run",
            }:
                violations.add("framework_monkeypatch")
        if not isinstance(node, ast.Call):
            continue
        name = _resolved_name(node.func, aliases)
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
    required_conditions = {
        "root.is_symlink()",
        "not resolved_root.is_dir()",
        "candidate.is_symlink()",
        "candidate.is_dir()",
        "not candidate.is_file()",
        "url in urls",
        "folded_url in casefold_urls",
        "not urls",
    }
    actual_conditions = {
        ast.unparse(node.test) for node in ast.walk(function) if isinstance(node, ast.If)
    }
    if not required_conditions <= actual_conditions:
        violations.append("asset_fail_closed_branches")
    containment_handlers = [
        handler
        for node in ast.walk(function)
        if isinstance(node, ast.Try)
        and any(
            isinstance(item, ast.Call) and _call_name(item.func) == "candidate.resolve"
            for item in ast.walk(ast.Module(body=node.body, type_ignores=[]))
        )
        and any(
            isinstance(item, ast.Call) and _call_name(item.func) == "resolved.relative_to"
            for item in ast.walk(ast.Module(body=node.body, type_ignores=[]))
        )
        for handler in node.handlers
        if handler.type is not None
        and ast.unparse(handler.type) == "(OSError, ValueError)"
        and any(
            isinstance(item, ast.Raise)
            and isinstance(item.exc, ast.Call)
            and _call_name(item.exc.func) == "ValueError"
            and item.exc.args
            and isinstance(item.exc.args[0], ast.Constant)
            and item.exc.args[0].value == "package_asset_containment_invalid"
            for item in handler.body
        )
    ]
    if len(containment_handlers) != 1:
        violations.append("asset_containment_failure")
    return violations


def test_application_import_graph_is_allowlisted() -> None:
    roots = imported_roots(APP_SOURCES)
    assert not roots & FORBIDDEN_IMPORT_ROOTS
    assert roots <= ALLOWED_IMPORT_ROOTS


def test_application_has_no_write_env_process_network_or_dynamic_code_capability() -> None:
    assert scan_capabilities(APP_SOURCES) == []


@pytest.mark.parametrize(
    "forbidden_name",
    (
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "vars",
        "globals",
        "locals",
        "eval",
        "exec",
        "compile",
        "__import__",
    ),
)
def test_application_forbidden_reflection_name_load_is_denied(
    tmp_path: Path,
    forbidden_name: str,
) -> None:
    for source in (
        forbidden_name,
        f"alias = {forbidden_name}",
        f"def capture(value={forbidden_name}):\n    return value",
        f"capture = lambda: {forbidden_name}",
        f"captured = ({forbidden_name} := {forbidden_name})",
        f"captured = [{forbidden_name}]",
    ):
        synthetic = tmp_path / "synthetic.py"
        synthetic.write_text(source, encoding="utf-8")
        assert f"synthetic.py:{forbidden_name}" in scan_capabilities((synthetic,))


@pytest.mark.parametrize(
    "forbidden_name",
    (
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "vars",
        "globals",
        "locals",
        "eval",
        "exec",
        "compile",
        "__import__",
    ),
)
def test_application_implicit_builtins_mapping_is_denied(
    tmp_path: Path,
    forbidden_name: str,
) -> None:
    for source in (
        f'captured = __builtins__["{forbidden_name}"]',
        f'captured = __builtins__.get("{forbidden_name}")',
    ):
        synthetic = tmp_path / "synthetic.py"
        synthetic.write_text(source, encoding="utf-8")
        assert "synthetic.py:__builtins__" in scan_capabilities((synthetic,))


@pytest.mark.parametrize(
    ("expression", "expected_suffix"),
    (
        ("target.__getattribute__", "__getattribute__"),
        ("target.__getattr__", "__getattr__"),
        ("target.__setattr__", "__setattr__"),
        ("target.__delattr__", "__delattr__"),
        ("target.__dict__", "__dict__"),
        ("target.__globals__", "__globals__"),
        ("target.__class__", "__class__"),
        ("operator.attrgetter", "operator.attrgetter"),
        ("operator.methodcaller", "operator.methodcaller"),
        ("inspect.getattr_static", "inspect.getattr_static"),
    ),
)
def test_application_forbidden_reflective_attribute_load_is_denied(
    tmp_path: Path,
    expression: str,
    expected_suffix: str,
) -> None:
    for source in (expression, f"alias = {expression}"):
        synthetic = tmp_path / "synthetic.py"
        synthetic.write_text(source, encoding="utf-8")
        assert f"synthetic.py:{expected_suffix}" in scan_capabilities((synthetic,))


@pytest.mark.parametrize(
    "hook_name",
    ("__getattribute__", "__getattr__", "__setattr__", "__delattr__", "__iter__"),
)
def test_application_dynamic_protocol_definitions_are_denied(
    tmp_path: Path,
    hook_name: str,
) -> None:
    synthetic = tmp_path / "synthetic.py"
    synthetic.write_text(
        f"class Dynamic:\n    def {hook_name}(self, *args):\n        return None\n",
        encoding="utf-8",
    )
    assert f"synthetic.py:{hook_name}" in scan_capabilities((synthetic,))


def test_application_dunder_assignment_and_dynamic_class_construction_are_denied(
    tmp_path: Path,
) -> None:
    mutations = (
        (
            "class Dynamic:\n    __getattr__ = lambda self, name: None",
            "__getattr__",
        ),
        (
            "class Dynamic:\n    __getattr__: object = handler",
            "__getattr__",
        ),
        (
            "class Dynamic:\n    __getattr__ += handler",
            "__getattr__",
        ),
        ("del __getattr__", "__getattr__"),
        (
            "Dynamic = type('Dynamic', (), {'__getattr__': handler})",
            "dynamic_type",
        ),
        (
            "class_factory = type\nDynamic = class_factory('Dynamic', (), {})",
            "dynamic_type",
        ),
        (
            "factory = type(ExistingClass)\nDynamic = factory('Dynamic', (), {})",
            "dynamic_type",
        ),
        (
            "Dynamic = type(ExistingClass)('Dynamic', (), {})",
            "dynamic_type",
        ),
        ("Dynamic = type(*args)", "dynamic_type"),
        ("type = factory\ntype(value) is str", "dynamic_type_binding"),
        (
            "def validate(type):\n    return type(value) is str",
            "dynamic_type_binding",
        ),
        ("def type(value):\n    return value", "dynamic_type_binding"),
        ("class type:\n    pass", "dynamic_type_binding"),
        (
            "import dataclasses as type\ntype.make_dataclass('Dynamic', [])",
            "dynamic_type_binding",
        ),
        (
            "from dataclasses import make_dataclass as type\ntype('Dynamic', []) is str",
            "dynamic_type_binding",
        ),
        (
            "try:\n    raise RuntimeError\nexcept RuntimeError as type:\n    pass",
            "dynamic_type_binding",
        ),
        ("match value:\n    case type:\n        pass", "dynamic_type_binding"),
        ("type: object = factory", "dynamic_type_binding"),
        ("type += factory", "dynamic_type_binding"),
        ("captured = (type := factory)", "dynamic_type_binding"),
        ("for type in values:\n    pass", "dynamic_type_binding"),
        ("captured = [value for type in values]", "dynamic_type_binding"),
        ("with manager() as type:\n    pass", "dynamic_type_binding"),
        ("def positional_only(type, /):\n    pass", "dynamic_type_binding"),
        ("def variadic(*type):\n    pass", "dynamic_type_binding"),
        ("def keyword_only(*, type):\n    pass", "dynamic_type_binding"),
        ("def variadic_keyword(**type):\n    pass", "dynamic_type_binding"),
        ("capture = lambda type: type", "dynamic_type_binding"),
        ("async def type():\n    pass", "dynamic_type_binding"),
        ("match values:\n    case [*type]:\n        pass", "dynamic_type_binding"),
        ("match mapping:\n    case {**type}:\n        pass", "dynamic_type_binding"),
        (
            "from types import new_class\nDynamic = new_class('Dynamic')",
            "dynamic_class_factory",
        ),
        ("import types", "dynamic_class_factory"),
        ("import types as t", "dynamic_class_factory"),
        ("from types import new_class as factory", "dynamic_class_factory"),
        (
            "from types import MappingProxyType, new_class",
            "dynamic_class_factory",
        ),
        (
            "import dataclasses\nDynamic = dataclasses.make_dataclass('Dynamic', [])",
            "dynamic_class_factory",
        ),
        (
            "from dataclasses import make_dataclass as factory\nDynamic = factory('Dynamic', [])",
            "dynamic_class_factory",
        ),
        (
            "import collections as c\nDynamic = c.namedtuple('Dynamic', 'value')",
            "dynamic_class_factory",
        ),
        (
            "from collections import namedtuple as factory\nDynamic = factory('Dynamic', 'value')",
            "dynamic_class_factory",
        ),
        (
            "import typing\nDynamic = typing.NamedTuple('Dynamic', [('value', int)])",
            "dynamic_class_factory",
        ),
        (
            "from typing import TypedDict as factory\nDynamic = factory('Dynamic', {'value': int})",
            "dynamic_class_factory",
        ),
        ("from typing import *", "dynamic_class_factory"),
        ("class __all__:\n    pass", "__all__"),
        ("class __init__:\n    pass", "__init__"),
        ("def __init__():\n    pass", "__init__"),
        ("import json as __all__", "__all__"),
        ("from json import loads as __all__", "__all__"),
        (
            "from carerisk_space.ui import __builtins__ as builtin_map",
            "__builtins__",
        ),
        ("def validate(__all__):\n    pass", "__all__"),
        (
            "try:\n    raise RuntimeError\nexcept RuntimeError as __all__:\n    pass",
            "__all__",
        ),
        ("match value:\n    case __all__:\n        pass", "__all__"),
        ("match values:\n    case [*__all__]:\n        pass", "__all__"),
        ("match mapping:\n    case {**__all__}:\n        pass", "__all__"),
        ("def declare():\n    global __all__", "__all__"),
    )
    synthetic = tmp_path / "synthetic.py"
    for source, expected_suffix in mutations:
        synthetic.write_text(source, encoding="utf-8")
        assert f"synthetic.py:{expected_suffix}" in scan_capabilities((synthetic,))

    for source in (
        'class Dynamic:\n    __all__ = ["NotAllowed"]',
        '__all__ = ["Allowed"]\n__all__: tuple[str, ...] = ("AlsoAllowed",)',
        "__all__ = [runtime_name]",
    ):
        synthetic.write_text(source, encoding="utf-8")
        assert "synthetic.py:__all__" in scan_capabilities((synthetic,))

    for source in (
        '__all__ = ["Allowed"]',
        '__all__: tuple[str, ...] = ("Allowed",)',
        "type(value) is not str",
        "type(value) is not int",
        "type(value) is not frozenset",
    ):
        synthetic.write_text(source, encoding="utf-8")
        assert scan_capabilities((synthetic,)) == []

    for source in (
        "type(value)",
        "type(type(value)) is str",
        "type(*values) is str",
    ):
        synthetic.write_text(source, encoding="utf-8")
        assert "synthetic.py:dynamic_type" in scan_capabilities((synthetic,))


def test_application_syntax_identities_are_not_reflection(tmp_path: Path) -> None:
    synthetic = tmp_path / "synthetic.py"
    synthetic.write_text(
        """from __future__ import annotations

__all__ = ["CallableGuard"]

class CallableGuard:
    def __init__(self) -> None:
        self.source = __file__

    def __call__(self) -> str:
        return __name__
""",
        encoding="utf-8",
    )
    assert scan_capabilities((synthetic,)) == []


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


def test_evidence_named_source_does_not_receive_a_filename_wide_read_exception(
    tmp_path: Path,
) -> None:
    synthetic_evidence = tmp_path / "evidence.py"
    synthetic_evidence.write_text("Path('private').read_bytes()", encoding="utf-8")
    assert scan_capabilities((synthetic_evidence,)) == ["evidence.py:read_bytes"]


def _scan_mutated_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    tree: ast.Module,
) -> list[str]:
    fake_space_root = tmp_path / "space"
    synthetic_evidence = fake_space_root / "carerisk_space" / "evidence.py"
    synthetic_evidence.parent.mkdir(parents=True)
    synthetic_evidence.write_text(ast.unparse(tree), encoding="utf-8")
    with monkeypatch.context() as patch:
        patch.setitem(scan_capabilities.__globals__, "SPACE_ROOT", fake_space_root)
        return scan_capabilities((synthetic_evidence,))


def test_evidence_reader_rejects_same_receiver_in_an_arbitrary_function(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mutated = ast.parse(ast.unparse(_tree(SPACE_ROOT / "carerisk_space" / "evidence.py")))
    mutated.body.extend(
        ast.parse(
            """
def arbitrary_reader(bundle_root):
    path = bundle_root.joinpath("README.md")
    return path.read_bytes()
"""
        ).body
    )
    assert _scan_mutated_evidence(monkeypatch, tmp_path, mutated) == ["evidence.py:read_bytes"]


def test_evidence_reader_rejects_an_arbitrary_path_inside_the_approved_function(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mutated = ast.parse(ast.unparse(_tree(SPACE_ROOT / "carerisk_space" / "evidence.py")))
    reader = _function(mutated, "read_regular_file")
    path_assignment = next(
        node
        for node in reader.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "path" for target in node.targets)
    )
    path_assignment.value = ast.Call(
        func=ast.Name(id="Path", ctx=ast.Load()),
        args=[ast.Constant(value="private")],
        keywords=[],
    )
    assert _scan_mutated_evidence(monkeypatch, tmp_path, mutated) == ["evidence.py:read_bytes"]


def test_evidence_reader_rejects_expansion_beyond_exact_public_source_names(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mutated = ast.parse(ast.unparse(_tree(SPACE_ROOT / "carerisk_space" / "evidence.py")))
    literal_paths = next(
        node
        for node in mutated.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_LITERAL_EVIDENCE_PATHS"
            for target in node.targets
        )
    )
    assert isinstance(literal_paths.value, ast.Set)
    literal_paths.value.elts.append(ast.Constant(value="README.md"))
    assert _scan_mutated_evidence(monkeypatch, tmp_path, mutated) == ["evidence.py:read_bytes"]


def test_evidence_reader_rejects_a_disabled_regular_file_guard(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mutated = ast.parse(ast.unparse(_tree(SPACE_ROOT / "carerisk_space" / "evidence.py")))
    reader = _function(mutated, "read_regular_file")
    regular_guard = next(
        node
        for node in reader.body
        if isinstance(node, ast.If) and "stat.S_ISREG" in ast.unparse(node.test)
    )
    regular_guard.test = ast.BoolOp(
        op=ast.And(), values=[ast.Constant(value=False), regular_guard.test]
    )
    assert _scan_mutated_evidence(monkeypatch, tmp_path, mutated) == ["evidence.py:read_bytes"]


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
    _function(mutated, "render_claim_header").body.insert(
        0,
        ast.ImportFrom(
            module="gradio", names=[ast.alias(name="Radio", asname="LocalRadio")], level=0
        ),
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


@pytest.mark.parametrize("method", ("add_middleware", "get"))
def test_entrypoint_scanner_rejects_parent_alias_lineage(method: str) -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.extend(
        ast.parse(
            f"parent_alias = parent\nsecond_alias = parent_alias\nsecond_alias.{method}()"
        ).body
    )
    expected = "parent_middleware" if method == "add_middleware" else "parent_route"
    assert expected in _entrypoint_violations(mutated)


def test_entrypoint_scanner_rejects_mount_and_uvicorn_alias_calls() -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.extend(
        ast.parse("mount = gr.mount_gradio_app\nmount(parent, demo)\nserver_main = main").body
    )
    _function(mutated, "main").body.extend(ast.parse("runner = uvicorn.run\nrunner(app)").body)
    violations = _entrypoint_violations(mutated)
    assert "framework_alias" in violations
    assert "mount_count" in violations
    assert "uvicorn_main_guard" in violations


def test_entrypoint_scanner_rejects_module_scope_main_alias_assignment() -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.extend(ast.parse("server_main = main").body)
    assert "uvicorn_main_guard" in _entrypoint_violations(mutated)


@pytest.mark.parametrize(
    "statement",
    (
        "canary = gr.mount_gradio_app = replacement",
        "gr.mount_gradio_app: object = replacement",
        "uvicorn.run += replacement",
        "framework = gr\nframework.mount_gradio_app = replacement",
    ),
)
def test_entrypoint_scanner_rejects_every_framework_assignment_form(statement: str) -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.extend(ast.parse(statement).body)
    assert "framework_monkeypatch" in _entrypoint_violations(mutated)


@pytest.mark.parametrize(
    ("source", "expected"),
    (
        (
            'getattr(gr, "mount_gradio_app")(parent, demo)',
            {"builtin_reflection", "mount_count"},
        ),
        (
            'reflect = getattr\nmount = reflect(gr, "mount_gradio_app")\n'
            "mount_alias = mount\nmount_alias(parent, demo)",
            {"builtin_reflection", "framework_alias", "mount_count"},
        ),
        (
            'route = getattr(parent, "get")\n@route("/hidden")\ndef hidden():\n    pass',
            {"builtin_reflection", "parent_route"},
        ),
        (
            "reflect = getattr\nparent_alias = parent\n"
            'middleware = reflect(parent_alias, "add_middleware")\n'
            "middleware(object)",
            {"builtin_reflection", "parent_middleware"},
        ),
        (
            "reflected = getattr(gr, runtime_member)",
            {"builtin_reflection"},
        ),
    ),
)
def test_entrypoint_scanner_rejects_builtin_reflection_alias_chains(
    source: str,
    expected: set[str],
) -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.extend(ast.parse(source).body)
    assert expected <= set(_entrypoint_violations(mutated))


@pytest.mark.parametrize(
    "source",
    (
        'mount = gr.__getattribute__("mount_gradio_app")\nmount(parent, demo)',
        'route = parent.__getattribute__("get")\n@route("/hidden")\ndef hidden():\n    pass',
        "member = runtime_member\nmount = gr.__getattribute__(member)\nmount(parent, demo)",
        'mount = vars(gr)["mount_gradio_app"]\nmount(parent, demo)',
        'mount = gr.__dict__["mount_gradio_app"]\nmount(parent, demo)',
        "from carerisk_space.ui import __builtins__ as builtin_map\n"
        'reflect = builtin_map["getattr"]\n'
        'hidden_mount = reflect(gr, "mount_gradio_app")\n'
        "hidden_mount(parent, demo)",
    ),
)
def test_entrypoint_scanner_rejects_reflection_without_resolving_forbidden_flow(
    source: str,
) -> None:
    mutated = ast.parse(ast.unparse(_tree(APP_ENTRY)))
    mutated.body.extend(ast.parse(source).body)
    assert {"builtin_reflection"} <= set(_entrypoint_violations(mutated))


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


@pytest.mark.parametrize(
    "condition",
    (
        "root.is_symlink()",
        "not resolved_root.is_dir()",
        "candidate.is_symlink()",
        "candidate.is_dir()",
        "not candidate.is_file()",
        "url in urls",
        "folded_url in casefold_urls",
        "not urls",
    ),
)
def test_asset_builder_scanner_rejects_fail_closed_branch_disable_mutations(
    condition: str,
) -> None:
    mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
    function = _function(mutated, "build_package_asset_membership")
    branch = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.If) and ast.unparse(node.test) == condition
    )
    branch.test = ast.BoolOp(op=ast.And(), values=[ast.Constant(value=False), branch.test])
    assert "asset_fail_closed_branches" in _asset_builder_violations(mutated)


def test_asset_builder_scanner_rejects_a_disabled_containment_failure_handler() -> None:
    mutated = ast.parse(ast.unparse(_tree(UI_SOURCE)))
    function = _function(mutated, "build_package_asset_membership")
    containment_try = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Try)
        and any(
            isinstance(item, ast.Call) and _call_name(item.func) == "resolved.relative_to"
            for item in ast.walk(node)
        )
    )
    containment_try.handlers[0].body = [ast.Pass()]
    assert "asset_containment_failure" in _asset_builder_violations(mutated)


class _FakeAssetPath:
    def __init__(
        self,
        relative: str,
        *,
        symlink: bool = False,
        directory: bool = False,
        regular: bool = True,
        children: tuple[_FakeAssetPath, ...] = (),
        contained: bool = True,
    ) -> None:
        self.relative = relative
        self.symlink = symlink
        self.directory = directory
        self.regular = regular
        self.children = children
        self.contained = contained

    def is_symlink(self) -> bool:
        return self.symlink

    def resolve(self, *, strict: bool) -> _FakeAssetPath:
        assert strict is True
        return self

    def is_dir(self) -> bool:
        return self.directory

    def is_file(self) -> bool:
        return self.regular

    def rglob(self, pattern: str) -> tuple[_FakeAssetPath, ...]:
        assert pattern == "*"
        return self.children

    def relative_to(self, root: _FakeAssetPath) -> Path:
        assert root.directory
        if not self.contained:
            raise ValueError("synthetic containment escape")
        return Path(self.relative)


def _install_fake_asset_roots(
    monkeypatch: pytest.MonkeyPatch,
    ui_module: object,
    build_candidates: tuple[_FakeAssetPath, ...],
    *,
    build_symlink: bool = False,
) -> None:
    build_root = _FakeAssetPath(
        "build", symlink=build_symlink, directory=True, regular=False, children=build_candidates
    )
    static_root = _FakeAssetPath(
        "static",
        directory=True,
        regular=False,
        children=(_FakeAssetPath("logo.svg"),),
    )

    def fake_path(value: object) -> _FakeAssetPath | Path:
        if isinstance(value, _FakeAssetPath):
            return value
        assert isinstance(value, (str, Path))
        return Path(value)

    monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", build_root)
    monkeypatch.setattr(ui_module, "STATIC_PATH_LIB", static_root)
    monkeypatch.setattr(ui_module, "Path", fake_path)


def test_asset_builder_fake_root_symlink_branch_fails_without_platform_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(SPACE_ROOT))
    ui_module = importlib.import_module("carerisk_space.ui")
    _install_fake_asset_roots(monkeypatch, ui_module, (), build_symlink=True)
    with pytest.raises(ValueError, match="package_asset_root_symlink"):
        ui_module.build_package_asset_membership()


@pytest.mark.parametrize("directory", (False, True))
def test_asset_builder_fake_file_and_directory_symlink_branches_fail(
    monkeypatch: pytest.MonkeyPatch,
    directory: bool,
) -> None:
    monkeypatch.syspath_prepend(str(SPACE_ROOT))
    ui_module = importlib.import_module("carerisk_space.ui")
    candidate = _FakeAssetPath(
        "linked" if directory else "linked.js",
        symlink=True,
        directory=directory,
        regular=not directory,
    )
    _install_fake_asset_roots(monkeypatch, ui_module, (candidate,))
    with pytest.raises(ValueError, match="package_asset_symlink"):
        ui_module.build_package_asset_membership()


def test_asset_builder_fake_special_file_and_containment_escape_branches_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(SPACE_ROOT))
    ui_module = importlib.import_module("carerisk_space.ui")
    special = _FakeAssetPath("special.sock", regular=False)
    _install_fake_asset_roots(monkeypatch, ui_module, (special,))
    with pytest.raises(ValueError, match="package_asset_special_file"):
        ui_module.build_package_asset_membership()

    escaped = _FakeAssetPath("escape.js", contained=False)
    _install_fake_asset_roots(monkeypatch, ui_module, (escaped,))
    with pytest.raises(ValueError, match="package_asset_containment_invalid"):
        ui_module.build_package_asset_membership()


def test_asset_builder_and_request_case_aliases_fail_deterministically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(SPACE_ROOT))
    ui_module = importlib.import_module("carerisk_space.ui")
    _install_fake_asset_roots(
        monkeypatch,
        ui_module,
        (_FakeAssetPath("CaseAlias.js"), _FakeAssetPath("casealias.js")),
    )
    with pytest.raises(ValueError, match="package_asset_case_alias"):
        ui_module.build_package_asset_membership()
    membership = frozenset({"/assets/CaseAlias.js"})
    assert ui_module._allowed_request("GET", "/assets/CaseAlias.js", b"", membership)
    assert not ui_module._allowed_request("GET", "/assets/casealias.js", b"", membership)


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


def _expected_rejection_guard_calls(function: ast.FunctionDef) -> set[ast.Call]:
    calls: set[ast.Call] = set()
    for node in ast.walk(function):
        if not isinstance(node, (ast.With, ast.AsyncWith)) or not any(
            isinstance(item.context_expr, ast.Call)
            and _call_name(item.context_expr.func) == "pytest.raises"
            for item in node.items
        ):
            continue
        calls.update(
            call
            for statement in node.body
            for call in ast.walk(statement)
            if isinstance(call, ast.Call)
            and _call_name(call.func) == "ui_module.PublicSurfaceGuard"
        )
    return calls


_GRADIO_CANONICAL_IMPORT_SOURCE = """\
from __future__ import annotations
import asyncio
import hashlib
import importlib.util
import inspect
import io
import json
import logging
import os
import re
import socket
import sys
import threading
import time
from collections import Counter, deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast, get_args
import carerisk_space.evidence as evidence_module
import carerisk_space.ui as ui_module
import gradio as gr
import gradio.routes as gradio_routes
import httpx
import pytest
import uvicorn
from carerisk_space.contracts import PRODUCT_NAME, EvidenceFailureCode, EvidenceViewModel
from carerisk_space.evidence import load_evidence
from carerisk_space.scenarios import SCENARIOS, render_scenario
from fastapi import FastAPI
from gradio.routes import BUILD_PATH_LIB, STATIC_PATH_LIB
from test_claim_contract import EXPECTED_EN, EXPECTED_ZH_TW
from test_evidence_contract import receipt_raw, release_raw, valid_manifest_bytes
from test_scenario_contract import EXPECTED_IDS
"""
_GRADIO_CANONICAL_IMPORT_DUMPS = tuple(
    ast.dump(node, include_attributes=False)
    for node in ast.parse(_GRADIO_CANONICAL_IMPORT_SOURCE).body
)
_GRADIO_ALL_FAILURE_CODES_DUMP = ast.dump(
    ast.parse(
        "ALL_FAILURE_CODES = cast(tuple[EvidenceFailureCode, ...], get_args(EvidenceFailureCode))"
    ).body[0],
    include_attributes=False,
)
_GRADIO_SPACE_ROOT_DUMP = ast.dump(
    ast.parse("SPACE_ROOT = Path(__file__).resolve().parents[1]").body[0],
    include_attributes=False,
)
_GRADIO_PROTECTED_IDENTITIES = frozenset(
    {
        "getattr",
        "type",
        "isinstance",
        "super",
        "frozenset",
        "inspect",
        "importlib",
        "socket",
        "sys",
        "pytest",
        "ui_module",
        "gr",
        "uvicorn",
        "Path",
        "SPACE_ROOT",
        "AppEntryMarker",
    }
)
_GRADIO_FORBIDDEN_BUILTIN_LOADS = frozenset(
    set(_FORBIDDEN_REFLECTION_NAMES) | {"breakpoint", "help", "dir"}
)
_GRADIO_FORBIDDEN_PATCH_NAMES = frozenset({"unittest", "mock", "patch", "pytest_mock", "mocker"})
_GRADIO_FORBIDDEN_DYNAMIC_MEMBERS = frozenset(
    {
        "import_module",
        "load_module",
        "load",
        "importorskip",
        "importer",
        "import_from_string",
        "resolve_name",
        "locate",
        "find_spec",
        "import_plugin",
        "load_setuptools_entrypoints",
        "pluginmanager",
    }
)
_GRADIO_FORBIDDEN_FRAME_MEMBERS = frozenset(
    {
        "gi_frame",
        "cr_frame",
        "ag_frame",
        "tb_frame",
        "f_builtins",
        "f_globals",
        "f_locals",
        "f_back",
        "_getframe",
        "_current_frames",
        "sys",
    }
)
_GRADIO_PROTECTED_MEMBERS = frozenset(
    {
        "getattr",
        "type",
        "isinstance",
        "super",
        "frozenset",
        "signature",
        "Parameter",
        "empty",
        "__version__",
        "AF_UNIX",
        "spec_from_file_location",
        "module_from_spec",
        "exec_module",
        "Config",
        "Server",
        "PublicSurfaceGuard",
        "create_app",
        "build_package_asset_membership",
        "mount_gradio_app",
        "run",
    }
)
_GRADIO_EXACT_MEMBER_NAMES = frozenset(
    {
        "signature",
        "Parameter",
        "empty",
        "spec_from_file_location",
        "module_from_spec",
        "exec_module",
        "Config",
        "Server",
        "mount_gradio_app",
    }
)
_GRADIO_PROTECTED_ATTRIBUTE_NAMES = frozenset(
    {
        "inspect",
        "importlib",
        "socket",
        "sys",
        "pytest",
        "ui_module",
        "gr",
        "uvicorn",
        "Path",
        "SPACE_ROOT",
        "AppEntryMarker",
    }
)
_GRADIO_LOADER_CAPABILITY_MEMBERS = frozenset(
    {"get_code", "get_data", "create_module", "exec_module"}
)
_GRADIO_CANONICAL_MONKEYPATCH_SETATTR_SOURCE = (
    (
        "test_static_document_prerenders_four_exact_scenarios_once",
        "monkeypatch.setattr(ui_module, 'render_scenario', recording_render)",
    ),
    (
        "test_package_asset_missing_root_fails_closed",
        "monkeypatch.setattr(ui_module, 'BUILD_PATH_LIB', tmp_path / 'missing')",
    ),
    ("_fake_asset_roots", "monkeypatch.setattr(ui_module, 'BUILD_PATH_LIB', build)"),
    ("_fake_asset_roots", "monkeypatch.setattr(ui_module, 'STATIC_PATH_LIB', static)"),
    (
        "test_linux_symlink_fixture_failure_is_a_failure_not_a_skip",
        "monkeypatch.setattr(sys, 'platform', 'linux')",
    ),
    (
        "test_linux_symlink_fixture_failure_is_a_failure_not_a_skip",
        "monkeypatch.setattr(Path, 'symlink_to', unavailable)",
    ),
    (
        "test_package_asset_root_symlink_fails_closed",
        "monkeypatch.setattr(ui_module, 'BUILD_PATH_LIB', build_link)",
    ),
    (
        "test_package_asset_root_symlink_fails_closed",
        "monkeypatch.setattr(ui_module, 'STATIC_PATH_LIB', static)",
    ),
    (
        "test_package_asset_containment_escape_fails_closed",
        "monkeypatch.setattr(Path, 'is_symlink', "
        "lambda path: False if path == escape else real_is_symlink(path))",
    ),
    (
        "test_package_asset_duplicate_url_fails_closed",
        "monkeypatch.setattr(ui_module, '_canonical_asset_relative', lambda relative: 'same.js')",
    ),
    (
        "test_direct_outer_boundary_blocks_file_and_upload_before_receive",
        "monkeypatch.setattr(gradio_routes, 'secure_url_stream_response', bomb)",
    ),
    (
        "test_direct_outer_boundary_blocks_file_and_upload_before_receive",
        "monkeypatch.setattr(gradio_routes, 'file_fetch', bomb)",
    ),
    (
        "test_direct_outer_boundary_blocks_file_and_upload_before_receive",
        "monkeypatch.setattr(gradio_routes.tempfile, 'NamedTemporaryFile', bomb)",
    ),
    (
        "test_direct_outer_boundary_blocks_file_and_upload_before_receive",
        "monkeypatch.setattr(gradio_routes.tempfile, 'TemporaryDirectory', bomb)",
    ),
    (
        "test_direct_outer_boundary_blocks_file_and_upload_before_receive",
        "monkeypatch.setattr(gradio_routes.tempfile, 'tempdir', str(temp_root))",
    ),
    (
        "test_running_outer_boundary_blocks_file_and_upload_before_fetch_or_temp",
        "monkeypatch.setattr(gradio_routes, 'secure_url_stream_response', bomb)",
    ),
    (
        "test_running_outer_boundary_blocks_file_and_upload_before_fetch_or_temp",
        "monkeypatch.setattr(gradio_routes, 'file_fetch', bomb)",
    ),
    (
        "test_running_outer_boundary_blocks_file_and_upload_before_fetch_or_temp",
        "monkeypatch.setattr(gradio_routes.tempfile, 'NamedTemporaryFile', bomb)",
    ),
    (
        "test_running_outer_boundary_blocks_file_and_upload_before_fetch_or_temp",
        "monkeypatch.setattr(gradio_routes.tempfile, 'TemporaryDirectory', bomb)",
    ),
    (
        "test_running_outer_boundary_blocks_file_and_upload_before_fetch_or_temp",
        "monkeypatch.setattr(gradio_routes.tempfile, 'tempdir', str(temp_root))",
    ),
    (
        "test_entrypoint_mount_and_uvicorn_contract_are_exact",
        "monkeypatch.setattr(ui_module, 'create_app', lambda bundle_root=None: demo)",
    ),
    (
        "test_entrypoint_mount_and_uvicorn_contract_are_exact",
        "monkeypatch.setattr(ui_module, 'build_package_asset_membership', lambda: membership)",
    ),
    (
        "test_entrypoint_mount_and_uvicorn_contract_are_exact",
        "monkeypatch.setattr(gr, 'mount_gradio_app', fake_mount)",
    ),
    (
        "test_entrypoint_mount_and_uvicorn_contract_are_exact",
        "monkeypatch.setattr(entrypoint.uvicorn, 'run', fake_run)",
    ),
    (
        "make_unit_failure_bundle",
        "monkeypatch.setattr(evidence_module, 'RECEIPT_SHA256', hashlib.sha256(raw).hexdigest())",
    ),
    (
        "make_unit_failure_bundle",
        "monkeypatch.setattr(evidence_module, 'RECEIPT_GIT_BLOB_SHA', "
        "evidence_module.git_blob_sha1(raw))",
    ),
)
_GRADIO_CANONICAL_MONKEYPATCH_SETATTR_DUMPS = tuple(
    (owner, ast.dump(ast.parse(source, mode="eval").body, include_attributes=False))
    for owner, source in _GRADIO_CANONICAL_MONKEYPATCH_SETATTR_SOURCE
)
_GRADIO_MONKEYPATCH_HELPER_CALLS = {
    "make_unit_failure_bundle": (
        ("test_app_owned_root_is_not_a_nested_main_landmark", 2),
        ("test_failure_page_is_one_static_document_with_no_capabilities", 2),
        ("test_schema_failure_controlled_seam_has_exact_copy_and_no_partial_surface", 2),
    ),
    "_fake_asset_roots": (
        ("test_package_asset_file_or_directory_symlink_fails_closed", 0),
        ("test_package_asset_containment_escape_fails_closed", 0),
        ("test_package_asset_special_file_fails_closed", 0),
        ("test_package_asset_duplicate_url_fails_closed", 0),
        ("test_package_asset_case_alias_fails_closed", 0),
    ),
}
_GRADIO_ENTRYPOINT_PATCH_SOURCE = (
    'monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)',
    'monkeypatch.setattr(ui_module, "build_package_asset_membership", lambda: membership)',
    'monkeypatch.setattr(gr, "mount_gradio_app", fake_mount)',
    'monkeypatch.setattr(entrypoint.uvicorn, "run", fake_run)',
)


def _parsed_expression_statement_value(source: str) -> ast.expr:
    statement = ast.parse(source).body[0]
    assert isinstance(statement, ast.Expr)
    return statement.value


_GRADIO_ENTRYPOINT_PATCH_DUMPS = tuple(
    ast.dump(_parsed_expression_statement_value(source), include_attributes=False)
    for source in _GRADIO_ENTRYPOINT_PATCH_SOURCE
)
_GRADIO_ENTRYPOINT_IDENTITY_HELPER_SOURCE = """\
def _assert_entrypoint_positional_identity(
    entrypoint: Any,
    mounted_parent: FastAPI,
    mounted_demo: gr.Blocks,
    served_app: Any,
) -> None:
    assert mounted_parent is entrypoint.parent
    assert mounted_demo is entrypoint.demo
    assert served_app is entrypoint.app
    assert isinstance(served_app, ui_module.PublicSurfaceGuard)
    assert served_app.downstream is mounted_parent
"""
_GRADIO_ENTRYPOINT_IDENTITY_HELPER_DUMP = ast.dump(
    ast.parse(_GRADIO_ENTRYPOINT_IDENTITY_HELPER_SOURCE).body[0],
    include_attributes=False,
)
_GRADIO_ENTRYPOINT_IDENTITY_CALL_SOURCE = (
    "_assert_entrypoint_positional_identity("
    "entrypoint, mount_positional[0][0], mount_positional[0][1], "
    "uvicorn_positional[0])",
    "_assert_entrypoint_positional_identity(entrypoint, wrong_parent, entrypoint.demo, wrong_app)",
)
_GRADIO_ENTRYPOINT_IDENTITY_CALL_DUMPS = tuple(
    ast.dump(ast.parse(source, mode="eval").body, include_attributes=False)
    for source in _GRADIO_ENTRYPOINT_IDENTITY_CALL_SOURCE
)


def _semantic_binding_records(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> list[tuple[str, ast.AST]]:
    records: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            records.append((node.id, node))
        elif isinstance(node, ast.arg):
            records.append((node.arg, node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            records.append((node.name, node))
        elif isinstance(node, ast.alias):
            records.extend(
                (name, node)
                for name in _alias_original_and_effective_names(node, parents.get(node))
            )
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            records.append((node.name, node))
        elif isinstance(node, ast.MatchMapping) and node.rest:
            records.append((node.rest, node))
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            records.extend((name, node) for name in node.names)
    return records


def _nearest_function(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
        current = parents.get(current)
    return None


def _nearest_class(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> ast.ClassDef | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.ClassDef):
            return current
        current = parents.get(current)
    return None


def _expression_dump(source: str) -> str:
    return ast.dump(ast.parse(source, mode="eval").body, include_attributes=False)


def _is_exact_call(node: ast.AST, source: str) -> bool:
    return isinstance(node, ast.Call) and ast.dump(
        node, include_attributes=False
    ) == _expression_dump(source)


def _is_exact_decorator_call(
    call: ast.Call,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    owner = _nearest_function(call, parents)
    return owner is not None and call in owner.decorator_list


def _binding_is_canonical_import(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    canonical_import_nodes: set[ast.stmt],
) -> bool:
    return isinstance(node, ast.alias) and parents.get(node) in canonical_import_nodes


def _is_within_annotation(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    current = node
    while (parent := parents.get(current)) is not None:
        if isinstance(parent, ast.arg) and parent.annotation is current:
            return True
        if isinstance(parent, ast.AnnAssign) and parent.annotation is current:
            return True
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent.returns is current
        if isinstance(parent, ast.stmt):
            return False
        current = parent
    return False


def _annotation_binding_key(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> tuple[str, str, str] | None:
    current = node
    while (parent := parents.get(current)) is not None:
        if isinstance(parent, ast.arg) and parent.annotation is current:
            owner = _nearest_function(parent, parents)
            return None if owner is None else ("arg", owner.name, parent.arg)
        if isinstance(parent, ast.AnnAssign) and parent.annotation is current:
            if not isinstance(parent.target, ast.Name):
                return None
            function_owner = _nearest_function(parent, parents)
            if function_owner is not None:
                return ("annassign", function_owner.name, parent.target.id)
            class_owner = _nearest_class(parent, parents)
            if class_owner is not None:
                return ("annassign", class_owner.name, parent.target.id)
            return None
        if isinstance(parent, ast.stmt):
            return None
        current = parent
    return None


def _has_exact_function_header(
    function: ast.FunctionDef,
    parameters: tuple[tuple[str, str], ...],
    return_annotation: str,
) -> bool:
    arguments = function.args
    return (
        not function.decorator_list
        and not getattr(function, "type_params", [])
        and not arguments.posonlyargs
        and not arguments.kwonlyargs
        and arguments.vararg is None
        and arguments.kwarg is None
        and not arguments.defaults
        and not arguments.kw_defaults
        and len(arguments.args) == len(parameters)
        and all(
            argument.arg == expected_name
            and argument.annotation is not None
            and ast.dump(argument.annotation, include_attributes=False)
            == _expression_dump(expected_annotation)
            for argument, (expected_name, expected_annotation) in zip(
                arguments.args, parameters, strict=True
            )
        )
        and function.returns is not None
        and ast.dump(function.returns, include_attributes=False)
        == _expression_dump(return_annotation)
    )


def _direct_monkeypatch_call_signature(
    call: ast.Call,
    parents: dict[ast.AST, ast.AST],
) -> tuple[str, str, str] | None:
    if not (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "setattr"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "monkeypatch"
        and len(call.args) == 3
        and not call.keywords
        and isinstance(call.args[1], ast.Constant)
        and isinstance(call.args[1].value, str)
    ):
        return None
    owner = _nearest_function(call, parents)
    target_name = _call_name(call.args[0])
    if owner is None or target_name is None:
        return None
    return owner.name, target_name, call.args[1].value


def _gradio_test_source_violations(tree: ast.Module) -> list[str]:
    violations: set[str] = set()
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    violations.update(
        f"semantic_dunder:{name}"
        for name in _semantic_dunder_bindings(tree, parents, permitted_all_target=None)
    )

    module_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    import_dumps = tuple(ast.dump(node, include_attributes=False) for node in module_imports)
    canonical_import_nodes: set[ast.stmt] = set()
    if import_dumps != _GRADIO_CANONICAL_IMPORT_DUMPS:
        violations.add("imports:closed_world")
    else:
        canonical_import_nodes.update(module_imports)
    if len(
        [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    ) != len(module_imports):
        violations.add("imports:nested")
    if (
        len(tree.body) < 36
        or tuple(tree.body[:34]) != tuple(module_imports)
        or ast.dump(tree.body[34], include_attributes=False) != _GRADIO_ALL_FAILURE_CODES_DUMP
        or ast.dump(tree.body[35], include_attributes=False) != _GRADIO_SPACE_ROOT_DUMP
    ):
        violations.add("module:prefix")

    binding_records = _semantic_binding_records(tree, parents)
    for name, node in binding_records:
        if name in _GRADIO_FORBIDDEN_PATCH_NAMES:
            violations.add(f"binding:{name}")
        if name in _GRADIO_FORBIDDEN_DYNAMIC_MEMBERS:
            violations.add(f"binding:{name}")
        if name in {"breakpoint", "help", "dir", "_getframe", "_current_frames"}:
            violations.add(f"binding:{name}")
        if name in _GRADIO_PROTECTED_IDENTITIES and not _binding_is_canonical_import(
            node, parents, canonical_import_nodes
        ):
            if name == "SPACE_ROOT" and node is getattr(tree.body[35], "targets", [None])[0]:
                continue
            if name == "AppEntryMarker" and isinstance(node, ast.ClassDef):
                continue
            violations.add(f"binding:{name}")

    allowed_getattr_names: set[ast.Name] = set()
    getattr_contracts = (
        ("getattr(inner, 'original_router', None)", "collect"),
        ("getattr(socket, 'AF_UNIX', None)", "test_package_asset_special_file_fails_closed"),
    )
    for source, owner_name in getattr_contracts:
        matches = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and _is_exact_call(node, source)
            and (owner := _nearest_function(node, parents)) is not None
            and owner.name == owner_name
        ]
        if len(matches) != 1 or not isinstance(matches[0].func, ast.Name):
            violations.add(f"getattr:{owner_name}")
        else:
            allowed_getattr_names.add(matches[0].func)

    expected_type_compare = _expression_dump("type(exc).__name__ == 'Failed'")
    type_compares = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        and ast.dump(node, include_attributes=False) == expected_type_compare
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "test_linux_symlink_fixture_failure_is_a_failure_not_a_skip"
    ]
    allowed_type_names = {
        node
        for compare in type_compares
        for node in ast.walk(compare)
        if isinstance(node, ast.Name) and node.id == "type"
    }
    if len(type_compares) != 1 or len(allowed_type_names) != 1:
        violations.add("type:exact_context")

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in _GRADIO_FORBIDDEN_BUILTIN_LOADS and node not in allowed_getattr_names:
                violations.add(f"name:{node.id}")
            if node.id in _GRADIO_FORBIDDEN_PATCH_NAMES:
                violations.add(f"name:{node.id}")
            if node.id in _GRADIO_FORBIDDEN_DYNAMIC_MEMBERS:
                violations.add(f"name:{node.id}")
            if node.id == "type" and node not in allowed_type_names:
                violations.add("name:type")
            if node.id == "isinstance":
                parent = parents.get(node)
                if not (
                    isinstance(parent, ast.Call)
                    and parent.func is node
                    and not parent.keywords
                    and len(parent.args) == 2
                ):
                    violations.add("name:isinstance")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if (
                node.value in _FORBIDDEN_DYNAMIC_PROTOCOL_LITERALS
                or node.value == "PublicSurfaceGuard"
            ):
                violations.add(f"literal:{node.value}")

    bounded_log_classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BoundedLogCapture"
    ]
    bounded_log_class = bounded_log_classes[0] if len(bounded_log_classes) == 1 else None
    bounded_log_initializers = (
        []
        if bounded_log_class is None
        else [
            node
            for node in bounded_log_class.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        ]
    )
    bounded_log_initializer = (
        bounded_log_initializers[0] if len(bounded_log_initializers) == 1 else None
    )
    expected_super_statement = ast.dump(
        ast.parse("super().__init__(level=logging.DEBUG)").body[0],
        include_attributes=False,
    )
    super_statements = (
        []
        if bounded_log_initializer is None
        else [
            statement
            for statement in bounded_log_initializer.body
            if ast.dump(statement, include_attributes=False) == expected_super_statement
        ]
    )
    super_calls = [
        node
        for statement in super_statements
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and _is_exact_call(node, "super().__init__(level=logging.DEBUG)")
    ]
    super_parent_valid = (
        len(super_calls) == 1
        and bounded_log_initializer is not None
        and bool(bounded_log_initializer.body)
        and bounded_log_initializer.body[0] in super_statements
    )
    version_compares = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        and ast.dump(node, include_attributes=False)
        == _expression_dump("gr.__version__ == '6.26.0'")
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "test_gradio_version_and_normal_config_are_static_and_event_free"
    ]
    allowed_dunder_attrs: set[ast.Attribute] = set()
    for root in [
        *(super_calls if super_parent_valid else []),
        *version_compares,
        *type_compares,
    ]:
        allowed_dunder_attrs.update(
            node
            for node in ast.walk(root)
            if isinstance(node, ast.Attribute) and _is_dunder(node.attr)
        )
    if not super_parent_valid:
        violations.add("super:exact_context")
        violations.add("exact_parent:super")
    if len(version_compares) != 1:
        violations.add("gr_version:exact_context")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and _is_dunder(node.attr):
            if node not in allowed_dunder_attrs:
                violations.add(f"dunder:{node.attr}")
        elif (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and _is_dunder(node.id)
            and node.id not in {"__file__", "__name__"}
        ):
            violations.add(f"dunder:{node.id}")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if node.attr in _GRADIO_FORBIDDEN_DYNAMIC_MEMBERS:
            violations.add(f"dynamic_member:{node.attr}")
        if node.attr in _GRADIO_FORBIDDEN_FRAME_MEMBERS:
            violations.add(f"frame_member:{node.attr}")
        if node.attr == "modules":
            violations.add("registry:modules")
        if node.attr == "patch":
            violations.add("patch:attribute")
        if isinstance(node.ctx, (ast.Store, ast.Del)) and node.attr in _GRADIO_PROTECTED_MEMBERS:
            violations.add(f"protected_store:{node.attr}")

    top_level_entrypoints = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_entrypoint_mount_and_uvicorn_contract_are_exact"
    ]
    entrypoint_owner = top_level_entrypoints[0] if len(top_level_entrypoints) == 1 else None
    if entrypoint_owner is None:
        violations.add("entrypoint:owner")

    identity_helpers = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_assert_entrypoint_positional_identity"
    ]
    identity_helper = identity_helpers[0] if len(identity_helpers) == 1 else None
    exact_identity_helper_argument: ast.arg | None = None
    if (
        identity_helper is None
        or ast.dump(identity_helper, include_attributes=False)
        != _GRADIO_ENTRYPOINT_IDENTITY_HELPER_DUMP
    ):
        violations.add("entrypoint:identity_helper")
    else:
        exact_identity_helper_argument = identity_helper.args.args[0]

    allowed_identity_helper_loads: set[ast.Name] = set()
    for expected_dump in _GRADIO_ENTRYPOINT_IDENTITY_CALL_DUMPS:
        matches = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and ast.dump(node, include_attributes=False) == expected_dump
            and _nearest_function(node, parents) is entrypoint_owner
        ]
        if len(matches) != 1 or not isinstance(matches[0].func, ast.Name):
            violations.add("entrypoint:identity_callsite")
        else:
            allowed_identity_helper_loads.add(matches[0].func)
    identity_helper_loads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "_assert_entrypoint_positional_identity"
        and isinstance(node.ctx, ast.Load)
    ]
    if len(identity_helper_loads) != 2 or any(
        node not in allowed_identity_helper_loads for node in identity_helper_loads
    ):
        violations.add("entrypoint:identity_load")
    for name, node in binding_records:
        if name == "_assert_entrypoint_positional_identity" and node is not identity_helper:
            violations.add("entrypoint:identity_binding")

    entrypoint_patch_nodes: set[ast.Call] = set()
    for expected_dump in _GRADIO_ENTRYPOINT_PATCH_DUMPS:
        matches = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and ast.dump(node, include_attributes=False) == expected_dump
            and _nearest_function(node, parents) is entrypoint_owner
        ]
        if len(matches) != 1:
            violations.add("entrypoint:patch_exception")
        else:
            entrypoint_patch_nodes.add(matches[0])

    monkeypatch_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "monkeypatch"
    ]
    approved_monkeypatch_calls: set[ast.Call] = set()
    allowed_monkeypatch_loads: set[ast.Name] = set()
    for expected_owner, expected_dump in _GRADIO_CANONICAL_MONKEYPATCH_SETATTR_DUMPS:
        matches = [
            call
            for call in monkeypatch_calls
            if ast.dump(call, include_attributes=False) == expected_dump
            and (owner := _nearest_function(call, parents)) is not None
            and owner.name == expected_owner
        ]
        if len(matches) != 1:
            violations.add("monkeypatch:canonical")
        else:
            approved_monkeypatch_calls.add(matches[0])
            call_attribute = matches[0].func
            assert isinstance(call_attribute, ast.Attribute)
            assert isinstance(call_attribute.value, ast.Name)
            allowed_monkeypatch_loads.add(call_attribute.value)
    canonical_setattr_calls = {
        call
        for call in monkeypatch_calls
        if isinstance(call.func, ast.Attribute) and call.func.attr == "setattr"
    }
    if (
        len(canonical_setattr_calls) != len(_GRADIO_CANONICAL_MONKEYPATCH_SETATTR_DUMPS)
        or canonical_setattr_calls != approved_monkeypatch_calls
    ):
        violations.add("monkeypatch:canonical")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "setattr":
            parent = parents.get(node)
            if not (
                isinstance(node.value, ast.Name)
                and node.value.id == "monkeypatch"
                and isinstance(parent, ast.Call)
                and parent.func is node
                and len(parent.args) == 3
                and not parent.keywords
                and isinstance(parent.args[1], ast.Constant)
                and isinstance(parent.args[1].value, str)
            ):
                violations.add("monkeypatch:setattr_shape")
    for call in monkeypatch_calls:
        call_attribute = call.func
        assert isinstance(call_attribute, ast.Attribute)
        method = call_attribute.attr
        if method == "setattr":
            if not (
                len(call.args) == 3
                and not call.keywords
                and isinstance(call.args[1], ast.Constant)
                and isinstance(call.args[1].value, str)
            ):
                violations.add("monkeypatch:setattr_shape")
                continue
            member = call.args[1].value
            if _is_dunder(member):
                violations.add("monkeypatch:load")
            elif member in _GRADIO_PROTECTED_MEMBERS and call not in entrypoint_patch_nodes:
                violations.add(f"monkeypatch:protected:{member}")
        elif method != "setenv":
            violations.add(f"monkeypatch:method:{method}")

    monkeypatch_args = [
        node for node in ast.walk(tree) if isinstance(node, ast.arg) and node.arg == "monkeypatch"
    ]
    annotation_dump = _expression_dump("pytest.MonkeyPatch")
    for argument in monkeypatch_args:
        if (
            argument.annotation is None
            or ast.dump(argument.annotation, include_attributes=False) != annotation_dump
        ):
            violations.add("monkeypatch:annotation")
    for name, node in binding_records:
        if name == "monkeypatch" and node not in monkeypatch_args:
            violations.add("monkeypatch:binding")

    setenv_calls: list[ast.Call] = []
    for call in monkeypatch_calls:
        call_attribute = call.func
        assert isinstance(call_attribute, ast.Attribute)
        if call_attribute.attr == "setenv":
            setenv_calls.append(call)
    if len(setenv_calls) != 1:
        violations.add("monkeypatch:setenv_count")
    else:
        setenv_call = setenv_calls[0]
        setenv_owner = _nearest_function(setenv_call, parents)
        expression = parents.get(setenv_call)
        loop = parents.get(expression) if expression is not None else None
        target_statement = ast.parse("for name, value in (): pass").body[0]
        assert isinstance(target_statement, ast.For)
        expected_target = ast.dump(target_statement.target, include_attributes=False)
        expected_iter = _expression_dump(
            "{'GRADIO_ANALYTICS_ENABLED': 'true', "
            "'HF_HUB_DISABLE_TELEMETRY': '0', "
            "'GRADIO_WATCH_DIRS': '/CANARY_7419', "
            "'GRADIO_VIBE_MODE': 'true', "
            "'GRADIO_ROOT_PATH': '/CANARY_7419', "
            "'SPACE_ID': 'CANARY_7419/space', "
            "'PORT': '9999'}.items()"
        )
        if not (
            setenv_owner is not None
            and setenv_owner.name
            == "test_exact_instance_state_ignores_poisoned_framework_environment"
            and _is_exact_call(setenv_call, "monkeypatch.setenv(name, value)")
            and isinstance(expression, ast.Expr)
            and isinstance(loop, ast.For)
            and expression in loop.body
            and ast.dump(loop.target, include_attributes=False) == expected_target
            and ast.dump(loop.iter, include_attributes=False) == expected_iter
            and loop.body == [expression]
        ):
            violations.add("monkeypatch:setenv_shape")
        else:
            setenv_attribute = setenv_call.func
            assert isinstance(setenv_attribute, ast.Attribute)
            assert isinstance(setenv_attribute.value, ast.Name)
            allowed_monkeypatch_loads.add(setenv_attribute.value)

    helper_headers = {
        "make_unit_failure_bundle": (
            (
                ("tmp_path", "Path"),
                ("code", "EvidenceFailureCode"),
                ("monkeypatch", "pytest.MonkeyPatch"),
            ),
            "Path",
            2,
            {
                ("evidence_module", "RECEIPT_SHA256"),
                ("evidence_module", "RECEIPT_GIT_BLOB_SHA"),
            },
        ),
        "_fake_asset_roots": (
            (("monkeypatch", "pytest.MonkeyPatch"), ("tmp_path", "Path")),
            "tuple[Path, Path]",
            0,
            {("ui_module", "BUILD_PATH_LIB"), ("ui_module", "STATIC_PATH_LIB")},
        ),
    }
    for helper_name, (
        parameters,
        return_annotation,
        parameter_index,
        internal_targets,
    ) in helper_headers.items():
        helper_contract_valid = True
        helper_matches = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == helper_name
        ]
        helper = helper_matches[0] if len(helper_matches) == 1 else None
        if helper is None or not _has_exact_function_header(helper, parameters, return_annotation):
            helper_contract_valid = False

        allowed_helper_callees: set[ast.Name] = set()
        for owner_name, argument_index in _GRADIO_MONKEYPATCH_HELPER_CALLS[helper_name]:
            matches = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == helper_name
                and (owner := _nearest_function(node, parents)) is not None
                and owner.name == owner_name
                and len(node.args) == (3 if helper_name == "make_unit_failure_bundle" else 2)
                and not node.keywords
                and isinstance(node.args[argument_index], ast.Name)
                and getattr(node.args[argument_index], "id", None) == "monkeypatch"
            ]
            if len(matches) != 1:
                helper_contract_valid = False
                continue
            helper_callee = matches[0].func
            assert isinstance(helper_callee, ast.Name)
            allowed_helper_callees.add(helper_callee)
            monkeypatch_argument = matches[0].args[argument_index]
            assert isinstance(monkeypatch_argument, ast.Name)
            allowed_monkeypatch_loads.add(monkeypatch_argument)

        helper_name_loads = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and node.id == helper_name
            and isinstance(node.ctx, ast.Load)
        ]
        if len(helper_name_loads) != len(allowed_helper_callees) or any(
            node not in allowed_helper_callees for node in helper_name_loads
        ):
            helper_contract_valid = False
        for name, binding in binding_records:
            if name == helper_name and binding is not helper:
                helper_contract_valid = False

        if helper is not None and parameter_index < len(helper.args.args):
            helper_argument = helper.args.args[parameter_index]
            internal_loads = [
                node
                for node in ast.walk(helper)
                if isinstance(node, ast.Name)
                and node.id == "monkeypatch"
                and isinstance(node.ctx, ast.Load)
                and _nearest_function(node, parents) is helper
            ]
            internal_calls: list[ast.AST | None] = []
            for node in internal_loads:
                attribute = parents.get(node)
                if isinstance(attribute, ast.Attribute):
                    internal_calls.append(parents.get(attribute))
            internal_signatures = {
                (_call_name(call.args[0]), call.args[1].value)
                for call in internal_calls
                if isinstance(call, ast.Call)
                and _direct_monkeypatch_call_signature(call, parents) is not None
                and isinstance(call.args[1], ast.Constant)
                and isinstance(call.args[1].value, str)
            }
            if (
                helper_argument.arg != "monkeypatch"
                or len(internal_loads) != 2
                or len(internal_calls) != 2
                or internal_signatures != internal_targets
            ):
                helper_contract_valid = False
        else:
            helper_contract_valid = False
        if not helper_contract_valid:
            violations.add("monkeypatch:load")

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id == "monkeypatch"
            and isinstance(node.ctx, ast.Load)
            and node not in allowed_monkeypatch_loads
        ):
            violations.add("monkeypatch:load")

    allowed_pytest_names: set[ast.Name] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        full_name = _call_name(node)
        if full_name is None or not full_name.startswith("pytest"):
            continue
        parent = parents.get(node)
        if (
            full_name == "pytest.mark"
            and isinstance(parent, ast.Attribute)
            and parent.attr == "parametrize"
        ):
            allowed_pytest_names.update(
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Name) and child.id == "pytest"
            )
            continue
        if full_name == "pytest.fixture":
            if (
                isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node in parent.decorator_list
            ):
                allowed_pytest_names.update(
                    child
                    for child in ast.walk(node)
                    if isinstance(child, ast.Name) and child.id == "pytest"
                )
                continue
            if (
                isinstance(parent, ast.Call)
                and parent.func is node
                and _is_exact_decorator_call(parent, parents)
                and ast.dump(parent, include_attributes=False)
                == _expression_dump("pytest.fixture(scope='module')")
            ):
                allowed_pytest_names.update(
                    child
                    for child in ast.walk(node)
                    if isinstance(child, ast.Name) and child.id == "pytest"
                )
                continue
        if (
            full_name == "pytest.mark.parametrize"
            and isinstance(parent, ast.Call)
            and parent.func is node
            and _is_exact_decorator_call(parent, parents)
        ):
            allowed_pytest_names.update(
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Name) and child.id == "pytest"
            )
            continue
        if (
            full_name in {"pytest.raises", "pytest.skip", "pytest.fail"}
            and isinstance(parent, ast.Call)
            and parent.func is node
        ):
            allowed_pytest_names.update(
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Name) and child.id == "pytest"
            )
            continue
        if (
            full_name in {"pytest.MonkeyPatch", "pytest.TempPathFactory"}
            and isinstance(parent, ast.arg)
            and parent.annotation is node
        ):
            allowed_pytest_names.update(
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Name) and child.id == "pytest"
            )
            continue
        violations.add(f"pytest:{full_name}")
    if any(
        node not in allowed_pytest_names
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "pytest" and isinstance(node.ctx, ast.Load)
    ):
        violations.add("pytest:context")
    for name, node in binding_records:
        if name in {"request", "pytestconfig"} and isinstance(node, ast.arg):
            violations.add(f"pytest:fixture:{name}")

    guard_constructor_owners = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_outer_guard_constructor_is_exact_and_rejects_empty_membership"
    ]
    guard_constructor_owner = (
        guard_constructor_owners[0] if len(guard_constructor_owners) == 1 else None
    )
    expected_signature_assignment = ast.dump(
        ast.parse("parameters = inspect.signature(ui_module.PublicSurfaceGuard).parameters").body[
            0
        ],
        include_attributes=False,
    )
    signature_assignments = (
        []
        if guard_constructor_owner is None
        else [
            statement
            for statement in guard_constructor_owner.body
            if ast.dump(statement, include_attributes=False) == expected_signature_assignment
        ]
    )
    signature_calls = [
        node
        for statement in signature_assignments
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and _is_exact_call(node, "inspect.signature(ui_module.PublicSurfaceGuard)")
    ]
    expected_parameter_assertion = ast.dump(
        ast.parse(
            "assert all(item.default is inspect.Parameter.empty for item in parameters.values())"
        ).body[0],
        include_attributes=False,
    )
    parameter_empty_assertions = (
        []
        if guard_constructor_owner is None
        else [
            statement
            for statement in guard_constructor_owner.body
            if ast.dump(statement, include_attributes=False) == expected_parameter_assertion
        ]
    )
    parameter_empty_attrs = [
        node
        for assertion in parameter_empty_assertions
        for node in ast.walk(assertion)
        if isinstance(node, ast.Attribute) and _call_name(node) == "inspect.Parameter.empty"
    ]
    if len(signature_assignments) != 1 or len(signature_calls) != 1:
        violations.add("inspect:signature")
        violations.add("exact_parent:signature")
    if len(parameter_empty_assertions) != 1 or len(parameter_empty_attrs) != 1:
        violations.add("inspect:Parameter.empty")
        violations.add("exact_parent:Parameter.empty")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        full_name = _call_name(node)
        if full_name is None or not full_name.startswith("inspect."):
            continue
        if full_name == "inspect.signature" and any(
            isinstance(parent, ast.Call) and parent.func is node for parent in [parents.get(node)]
        ):
            continue
        parameter_parent = parents.get(node)
        if (
            full_name == "inspect.Parameter"
            and isinstance(parameter_parent, ast.Attribute)
            and parameter_parent.attr == "empty"
        ):
            continue
        if full_name == "inspect.Parameter.empty" and node in parameter_empty_attrs:
            continue
        violations.add(f"inspect:{full_name}")

    entrypoint_statements = [] if entrypoint_owner is None else entrypoint_owner.body
    expected_entrypoint_statements = tuple(
        ast.dump(ast.parse(source).body[0], include_attributes=False)
        for source in (
            "spec = importlib.util.spec_from_file_location("
            "'carerisk_space_entrypoint', SPACE_ROOT / 'app.py')",
            "assert spec is not None and spec.loader is not None",
            "entrypoint = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(entrypoint)",
        )
    )
    exact_entrypoint_sequences = [
        entrypoint_statements[index : index + len(expected_entrypoint_statements)]
        for index in range(len(entrypoint_statements) - len(expected_entrypoint_statements) + 1)
        if tuple(
            ast.dump(statement, include_attributes=False)
            for statement in entrypoint_statements[
                index : index + len(expected_entrypoint_statements)
            ]
        )
        == expected_entrypoint_statements
    ]
    exact_entrypoint_statements = (
        exact_entrypoint_sequences[0] if len(exact_entrypoint_sequences) == 1 else []
    )
    if len(exact_entrypoint_sequences) != 1:
        violations.add("entrypoint:load_chain")
        violations.add("loader:context")
    allowed_loader_nodes = {
        node for statement in exact_entrypoint_statements for node in ast.walk(statement)
    }
    allowed_spec_bindings: set[ast.AST] = {
        node
        for statement in exact_entrypoint_statements
        for node in ast.walk(statement)
        if isinstance(node, ast.Name)
        and node.id in {"spec", "entrypoint"}
        and isinstance(node.ctx, ast.Store)
    }
    if exact_identity_helper_argument is not None:
        allowed_spec_bindings.add(exact_identity_helper_argument)
    for name, node in binding_records:
        if name in {"spec", "entrypoint"} and node not in allowed_spec_bindings:
            violations.add(f"entrypoint:binding:{name}")
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id == "spec"
            and isinstance(node.ctx, ast.Load)
            and node not in allowed_loader_nodes
        ):
            violations.add("loader:context")
        if isinstance(node, ast.Attribute):
            if (
                node.attr == "loader"
                and isinstance(node.value, ast.Name)
                and node.value.id == "spec"
                and node not in allowed_loader_nodes
            ):
                violations.add("loader:context")
            if node.attr in _GRADIO_LOADER_CAPABILITY_MEMBERS and node not in allowed_loader_nodes:
                violations.add("loader:context")
                if node.attr == "exec_module":
                    violations.add("entrypoint:exec_module")
        if isinstance(node, ast.Attribute):
            full_name = _call_name(node)
            if (
                full_name is not None
                and full_name.startswith("importlib.")
                and full_name
                not in {
                    "importlib.util",
                    "importlib.util.spec_from_file_location",
                    "importlib.util.module_from_spec",
                }
            ):
                violations.add(f"importlib:{full_name}")

    allowed_space_root_names: set[ast.Name] = set()
    if (
        len(tree.body) >= 36
        and ast.dump(tree.body[35], include_attributes=False) == _GRADIO_SPACE_ROOT_DUMP
    ):
        allowed_space_root_names.update(
            node
            for node in ast.walk(tree.body[35])
            if isinstance(node, ast.Name) and node.id == "SPACE_ROOT"
        )
    source_read_dump = _expression_dump(
        "(SPACE_ROOT / 'carerisk_space' / 'ui.py').read_text(encoding='utf-8')"
    )
    for call in [node for node in ast.walk(tree) if isinstance(node, ast.Call)]:
        if ast.dump(call, include_attributes=False) == source_read_dump:
            allowed_space_root_names.update(
                node
                for node in ast.walk(call)
                if isinstance(node, ast.Name) and node.id == "SPACE_ROOT"
            )
    if exact_entrypoint_statements:
        allowed_space_root_names.update(
            node
            for node in ast.walk(exact_entrypoint_statements[0])
            if isinstance(node, ast.Name) and node.id == "SPACE_ROOT"
        )
    all_space_root_names = [
        node for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == "SPACE_ROOT"
    ]
    if len(all_space_root_names) != 3 or any(
        node not in allowed_space_root_names for node in all_space_root_names
    ):
        violations.add("SPACE_ROOT:context")

    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Name) and node.id == "Path" and isinstance(node.ctx, ast.Load)
        ):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.Attribute) and _call_name(parent) == "Path.is_symlink":
            statement = parents.get(parent)
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == "real_is_symlink"
            ):
                continue
        if isinstance(parent, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            violations.add("Path:alias")

    config_dump = _expression_dump(
        "uvicorn.Config(marker, host='127.0.0.1', port=7860, workers=1, http='h11', "
        "proxy_headers=False, forwarded_allow_ips='', access_log=False, server_header=False, "
        "date_header=False, log_config=None, lifespan='on')"
    )
    config_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and ast.dump(node, include_attributes=False) == config_dump
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "running_wire_app"
    ]
    server_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _is_exact_call(node, "uvicorn.Server(config)")
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "running_wire_app"
    ]
    if len(config_calls) != 1:
        violations.add("uvicorn:Config")
    if len(server_calls) != 1:
        violations.add("uvicorn:Server")
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "uvicorn"
        ):
            parent = parents.get(node)
            if not (
                isinstance(parent, ast.Call)
                and parent.func is node
                and (parent in config_calls or parent in server_calls)
            ):
                violations.add(f"uvicorn:{node.attr}")

    marker_classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "AppEntryMarker"
    ]
    marker_class = marker_classes[0] if len(marker_classes) == 1 else None
    if marker_class is None or (
        marker_class.decorator_list
        or marker_class.bases
        or marker_class.keywords
        or getattr(marker_class, "type_params", [])
    ):
        violations.add("AppEntryMarker:header")
    marker_assignment_dump = ast.dump(
        ast.parse("marker = AppEntryMarker(guarded, guarded.package_asset_urls)").body[0],
        include_attributes=False,
    )
    marker_assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and ast.dump(node, include_attributes=False) == marker_assignment_dump
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "running_wire_app"
    ]
    marker_fields: list[ast.AnnAssign] = []
    for node in ast.walk(tree):
        marker_parent = parents.get(node)
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "marker"
            and isinstance(marker_parent, ast.ClassDef)
            and marker_parent.name == "RunningWireApp"
            and isinstance(node.annotation, ast.Name)
            and node.annotation.id == "AppEntryMarker"
            and node.value is None
        ):
            marker_fields.append(node)
    allowed_marker_bindings = {
        node
        for statement in [*marker_assignments, *marker_fields]
        for node in ast.walk(statement)
        if isinstance(node, ast.Name) and node.id == "marker" and isinstance(node.ctx, ast.Store)
    }
    for name, node in binding_records:
        if name == "marker" and node not in allowed_marker_bindings:
            violations.add("marker:binding")
        if name == "AppEntryMarker" and node is not marker_class:
            violations.add("AppEntryMarker:binding")
    if len(marker_assignments) != 1 or len(marker_fields) != 1:
        violations.add("marker:lineage")
    allowed_marker_identity_loads = {
        node
        for statement in [*marker_assignments, *marker_fields]
        for node in ast.walk(statement)
        if isinstance(node, ast.Name)
        and node.id == "AppEntryMarker"
        and isinstance(node.ctx, ast.Load)
    }
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id == "AppEntryMarker"
            and isinstance(node.ctx, ast.Load)
            and node not in allowed_marker_identity_loads
        ):
            violations.add("AppEntryMarker:load")

    allowed_sys_names: set[ast.Name] = set()
    sys_platform_compares = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        and ast.dump(node, include_attributes=False) == _expression_dump("sys.platform == 'win32'")
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "_capability_skip_or_fail"
    ]
    sys_platform_patches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _is_exact_call(node, 'monkeypatch.setattr(sys, "platform", "linux")')
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "test_linux_symlink_fixture_failure_is_a_failure_not_a_skip"
    ]
    if len(sys_platform_compares) != 1 or len(sys_platform_patches) != 1:
        violations.add("sys:context")
    for root in [*sys_platform_compares, *sys_platform_patches]:
        allowed_sys_names.update(
            node
            for node in ast.walk(root)
            if isinstance(node, ast.Name) and node.id == "sys" and isinstance(node.ctx, ast.Load)
        )
    if any(
        isinstance(node, ast.Attribute)
        and node.attr == "platform"
        and isinstance(node.ctx, (ast.Store, ast.Del))
        for node in ast.walk(tree)
    ):
        violations.add("sys:context")
    if any(
        node not in allowed_sys_names
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "sys" and isinstance(node.ctx, ast.Load)
    ):
        violations.add("sys:context")

    allowed_protected_loads: dict[str, set[ast.Name]] = {
        name: set()
        for name in {
            "getattr",
            "type",
            "super",
            "inspect",
            "importlib",
            "uvicorn",
            "gr",
            "socket",
            "sys",
            "pytest",
            "ui_module",
            "isinstance",
            "frozenset",
        }
    }
    allowed_protected_loads["getattr"].update(allowed_getattr_names)
    allowed_protected_loads["type"].update(allowed_type_names)
    if super_parent_valid:
        allowed_protected_loads["super"].update(
            node
            for node in ast.walk(super_calls[0])
            if isinstance(node, ast.Name) and node.id == "super"
        )
    if len(signature_calls) == 1:
        allowed_protected_loads["inspect"].update(
            node
            for node in ast.walk(signature_calls[0])
            if isinstance(node, ast.Name) and node.id == "inspect"
        )
    if len(parameter_empty_attrs) == 1:
        allowed_protected_loads["inspect"].update(
            node
            for node in ast.walk(parameter_empty_attrs[0])
            if isinstance(node, ast.Name) and node.id == "inspect"
        )
    if len(exact_entrypoint_statements) == 4:
        allowed_protected_loads["importlib"].update(
            node
            for statement in (
                exact_entrypoint_statements[0],
                exact_entrypoint_statements[2],
            )
            for node in ast.walk(statement)
            if isinstance(node, ast.Name) and node.id == "importlib"
        )
    if len(config_calls) == 1:
        allowed_protected_loads["uvicorn"].update(
            node
            for node in ast.walk(config_calls[0])
            if isinstance(node, ast.Name) and node.id == "uvicorn"
        )
    if len(server_calls) == 1:
        allowed_protected_loads["uvicorn"].update(
            node
            for node in ast.walk(server_calls[0])
            if isinstance(node, ast.Name) and node.id == "uvicorn"
        )

    gr_blocks_attributes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and _call_name(node) == "gr.Blocks"
        and _is_within_annotation(node, parents)
    ]
    expected_gr_blocks_bindings = {
        ("arg", "_only_document", "app"),
        ("arg", "_compose", "demo"),
        ("arg", "_queue_state_snapshot", "demo"),
        ("annassign", "RunningWireApp", "demo"),
        ("arg", "_assert_entrypoint_positional_identity", "mounted_demo"),
        ("arg", "fake_mount", "mounted_demo"),
        (
            "annassign",
            "test_entrypoint_mount_and_uvicorn_contract_are_exact",
            "mount_positional",
        ),
    }
    gr_mount_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _is_exact_call(
            node,
            "gr.mount_gradio_app(parent, demo, path='/', server_name='0.0.0.0', "
            "server_port=7860, footer_links=[], run_history=False, root_path='', "
            "allowed_paths=['/__carerisk_no_allowed_files__'], blocked_paths=['/'], "
            "favicon_path=None, show_error=False, max_file_size=0, ssr_mode=False, "
            "enable_monitoring=False, pwa=False, mcp_server=False)",
        )
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "_compose"
    ]
    gr_entrypoint_patch_calls = [
        node
        for node in entrypoint_patch_nodes
        if len(node.args) == 3
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "gr"
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "mount_gradio_app"
    ]
    if (
        len(gr_blocks_attributes) != 7
        or {
            key
            for attribute in gr_blocks_attributes
            if (key := _annotation_binding_key(attribute, parents)) is not None
        }
        != expected_gr_blocks_bindings
        or len(gr_mount_calls) != 1
        or len(version_compares) != 1
        or len(gr_entrypoint_patch_calls) != 1
    ):
        violations.add("protected_load:gr")
    for root in [
        *gr_blocks_attributes,
        *gr_mount_calls,
        *version_compares,
        *gr_entrypoint_patch_calls,
    ]:
        allowed_protected_loads["gr"].update(
            node for node in ast.walk(root) if isinstance(node, ast.Name) and node.id == "gr"
        )

    socket_connection_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _is_exact_call(node, "socket.create_connection(('127.0.0.1', 7860), timeout=5)")
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name in {"request", "request_early_response"}
    ]
    socket_constructor_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _is_exact_call(node, "socket.socket(unix_family, socket.SOCK_STREAM)")
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "test_package_asset_special_file_fails_closed"
    ]
    socket_getattr_names = [node for node in allowed_getattr_names if node.id == "getattr"]
    socket_receiver_names = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _is_exact_call(node, "getattr(socket, 'AF_UNIX', None)")
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == "test_package_asset_special_file_fails_closed"
        for node in ast.walk(node)
        if isinstance(node, ast.Name) and node.id == "socket"
    ]
    if (
        len(socket_connection_calls) != 2
        or len(socket_constructor_calls) != 1
        or len(socket_getattr_names) != 2
        or len(socket_receiver_names) != 1
    ):
        violations.add("protected_load:socket")
    for root in [*socket_connection_calls, *socket_constructor_calls]:
        allowed_protected_loads["socket"].update(
            node for node in ast.walk(root) if isinstance(node, ast.Name) and node.id == "socket"
        )
    allowed_protected_loads["socket"].update(socket_receiver_names)
    allowed_protected_loads["sys"].update(allowed_sys_names)
    allowed_protected_loads["pytest"].update(allowed_pytest_names)

    allowed_protected_attributes: set[ast.Attribute] = set()
    entrypoint_uvicorn_patch_nodes = [
        call
        for call in approved_monkeypatch_calls
        if len(call.args) == 3
        and isinstance(call.args[0], ast.Attribute)
        and isinstance(call.args[0].value, ast.Name)
        and call.args[0].value.id == "entrypoint"
        and call.args[0].attr == "uvicorn"
        and isinstance(call.args[1], ast.Constant)
        and call.args[1].value == "run"
        and isinstance(call.args[2], ast.Name)
        and call.args[2].id == "fake_run"
        and _nearest_function(call, parents) is entrypoint_owner
    ]
    if len(entrypoint_uvicorn_patch_nodes) == 1:
        entrypoint_uvicorn_target = entrypoint_uvicorn_patch_nodes[0].args[0]
        assert isinstance(entrypoint_uvicorn_target, ast.Attribute)
        allowed_protected_attributes.add(entrypoint_uvicorn_target)
    if len(socket_constructor_calls) == 1:
        socket_constructor = socket_constructor_calls[0]
        if (
            isinstance(socket_constructor.func, ast.Attribute)
            and isinstance(socket_constructor.func.value, ast.Name)
            and socket_constructor.func.value.id == "socket"
            and socket_constructor.func.attr == "socket"
            and len(socket_constructor.args) == 2
            and not socket_constructor.keywords
        ):
            allowed_protected_attributes.add(socket_constructor.func)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr in _GRADIO_PROTECTED_ATTRIBUTE_NAMES
            and node not in allowed_protected_attributes
        ):
            violations.add(f"protected_attr:{node.attr}")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
            continue
        parent = parents.get(node)
        if node.id == "ui_module" and (
            isinstance(parent, ast.Attribute)
            and parent.value is node
            or isinstance(parent, ast.Call)
            and parent in approved_monkeypatch_calls
            and parent.args[0] is node
        ):
            allowed_protected_loads["ui_module"].add(node)
        elif node.id == "isinstance" and isinstance(parent, ast.Call) and parent.func is node:
            allowed_protected_loads["isinstance"].add(node)
        elif node.id == "frozenset":
            direct_call = isinstance(parent, ast.Call) and parent.func is node
            isinstance_type = (
                isinstance(parent, ast.Call)
                and isinstance(parent.func, ast.Name)
                and parent.func.id == "isinstance"
                and len(parent.args) == 2
                and parent.args[1] is node
                and not parent.keywords
            )
            annotation = (
                isinstance(parent, ast.Subscript)
                and parent.value is node
                and _is_within_annotation(parent, parents)
            )
            if direct_call or isinstance_type or annotation:
                allowed_protected_loads["frozenset"].add(node)

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in allowed_protected_loads
            and node not in allowed_protected_loads[node.id]
        ):
            violations.add(f"protected_load:{node.id}")

    allowed_exact_members: set[ast.Attribute] = set()
    if len(signature_calls) == 1 and isinstance(signature_calls[0].func, ast.Attribute):
        allowed_exact_members.add(signature_calls[0].func)
    if len(parameter_empty_attrs) == 1:
        allowed_exact_members.add(parameter_empty_attrs[0])
        parameter_attribute = parameter_empty_attrs[0].value
        if isinstance(parameter_attribute, ast.Attribute):
            allowed_exact_members.add(parameter_attribute)
    for statement in exact_entrypoint_statements:
        allowed_exact_members.update(
            node
            for node in ast.walk(statement)
            if isinstance(node, ast.Attribute) and node.attr in _GRADIO_EXACT_MEMBER_NAMES
        )
    for call in [*config_calls, *server_calls, *gr_mount_calls]:
        if isinstance(call.func, ast.Attribute):
            allowed_exact_members.add(call.func)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr in _GRADIO_EXACT_MEMBER_NAMES
            and node not in allowed_exact_members
        ):
            violations.add(f"protected_member:{node.attr}")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr not in {
            "PublicSurfaceGuard",
            "build_package_asset_membership",
        }:
            continue
        if not (isinstance(node.value, ast.Name) and node.value.id == "ui_module"):
            violations.add(f"sensitive_receiver:{node.attr}")
            continue
        parent = parents.get(node)
        if node.attr == "build_package_asset_membership":
            if not (
                isinstance(parent, ast.Call)
                and parent.func is node
                and not parent.args
                and not parent.keywords
            ):
                violations.add("sensitive_context:builder")
            continue
        direct_constructor = isinstance(parent, ast.Call) and parent.func is node
        signature_argument = any(
            isinstance(call, ast.Call)
            and call in signature_calls
            and len(call.args) == 1
            and call.args[0] is node
            for call in [parent]
        )
        isinstance_argument = (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Name)
            and parent.func.id == "isinstance"
            and len(parent.args) == 2
            and parent.args[1] is node
            and not parent.keywords
        )
        if not (direct_constructor or signature_argument or isinstance_argument):
            violations.add("sensitive_context:guard")

    return sorted(violations)


def _guard_helper_violations(tree: ast.Module) -> list[str]:
    violations = _gradio_test_source_violations(tree)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    for function in functions:
        all_guard_calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and _call_name(node.func) == "ui_module.PublicSurfaceGuard"
            and _nearest_function(node, parents) is function
        ]
        if not all_guard_calls:
            continue
        rejected_calls = _expected_rejection_guard_calls(function)
        guard_calls = [call for call in all_guard_calls if call not in rejected_calls]
        if not guard_calls:
            violations.append(f"{function.name}:positive_guard_call")
            continue
        builder_calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and _call_name(node.func) == "ui_module.build_package_asset_membership"
            and _nearest_function(node, parents) is function
        ]
        assignments = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and node.value in builder_calls
            and not node.value.args
            and not node.value.keywords
        ]
        if len(builder_calls) != 1 or len(assignments) != 1:
            violations.append(f"{function.name}:builder_assignment")
            continue
        assignment = assignments[0]
        assert isinstance(assignment.targets[0], ast.Name)
        membership_name = assignment.targets[0].id
        stores = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Name)
            and node.id == membership_name
            and isinstance(node.ctx, ast.Store)
        ]
        type_assertions = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assert)
            and isinstance(node.test, ast.Call)
            and _call_name(node.test.func) == "isinstance"
            and len(node.test.args) == 2
            and not node.test.keywords
            and isinstance(node.test.args[0], ast.Name)
            and node.test.args[0].id == membership_name
            and isinstance(node.test.args[1], ast.Name)
            and node.test.args[1].id == "frozenset"
        ]
        truthy_assertions = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assert)
            and isinstance(node.test, ast.Name)
            and node.test.id == membership_name
        ]
        if len(stores) != 1:
            violations.append(f"{function.name}:builder_reassigned")
        if len(type_assertions) != 1:
            violations.append(f"{function.name}:builder_type_assertion")
        if len(truthy_assertions) != 1:
            violations.append(f"{function.name}:builder_nonempty_assertion")
        if not all(
            len(call.args) == 2
            and not call.keywords
            and isinstance(call.args[1], ast.Name)
            and call.args[1].id == membership_name
            for call in guard_calls
        ):
            violations.append(f"{function.name}:guard_membership_identity")
        checkpoints = [*type_assertions, *truthy_assertions]
        if checkpoints and not (
            assignment.lineno < min(node.lineno for node in checkpoints)
            and max(node.lineno for node in checkpoints) < min(call.lineno for call in guard_calls)
        ):
            violations.append(f"{function.name}:builder_assertion_order")
    return sorted(set(violations))


def _current_gradio_contract_source() -> str:
    return (SPACE_ROOT / "tests" / "test_gradio_contract.py").read_text(encoding="utf-8")


def _mutated_gradio_contract_tree(old: str, new: str, *, count: int = 1) -> ast.Module:
    source = _current_gradio_contract_source()
    assert source.count(old) >= count
    return ast.parse(source.replace(old, new, count))


def _gradio_contract_tree_with_appendix(appendix: str) -> ast.Module:
    return ast.parse(f"{_current_gradio_contract_source()}\n{appendix}\n")


def _gradio_contract_tree_for_case(case: str | tuple[str, str, int]) -> ast.Module:
    if isinstance(case, str):
        return _gradio_contract_tree_with_appendix(case)
    old, new, count = case
    return _mutated_gradio_contract_tree(old, new, count=count)


def _assert_gradio_contract_finding(case: str | tuple[str, str, int], expected: str) -> None:
    tree = _gradio_contract_tree_for_case(case)
    assert expected in _gradio_test_source_violations(tree)
    assert expected in _guard_helper_violations(tree)


def _gradio_contract_tree_with_setattr_replacement(index: int) -> ast.Module:
    tree = ast.parse(_current_gradio_contract_source())
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    owner_name, expected_dump = _GRADIO_CANONICAL_MONKEYPATCH_SETATTR_DUMPS[index]
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and ast.dump(node, include_attributes=False) == expected_dump
        and (owner := _nearest_function(node, parents)) is not None
        and owner.name == owner_name
    ]
    assert len(matches) == 1
    replacement = "os.system" if index == 0 else f"replacement_{index}"
    matches[0].args[2] = ast.parse(replacement, mode="eval").body
    return ast.fix_missing_locations(tree)


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("ui_module.gr", "protected_attr:gr"),
        ("entrypoint.gr", "protected_attr:gr"),
        ("captured_runner = entrypoint.uvicorn", "protected_attr:uvicorn"),
        ("ui_module.Path", "protected_attr:Path"),
        ("evidence_module.Path", "protected_attr:Path"),
        ("ui_module.inspect", "protected_attr:inspect"),
        ("evidence_module.importlib", "protected_attr:importlib"),
        ("constructor = socket.socket", "protected_attr:socket"),
        (
            "other.socket(unix_family, socket.SOCK_STREAM)",
            "protected_attr:socket",
        ),
        (
            "socket.socket(unix_family, socket.SOCK_STREAM)",
            "protected_attr:socket",
        ),
    ),
)
def test_gradio_contract_protected_reexports_are_denied(
    case: str | tuple[str, str, int], expected: str
) -> None:
    _assert_gradio_contract_finding(case, expected)


_GRADIO_ENTRYPOINT_LOADER_BLOCK = """\
    spec = importlib.util.spec_from_file_location(
        "carerisk_space_entrypoint", SPACE_ROOT / "app.py"
    )
    assert spec is not None and spec.loader is not None
    entrypoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entrypoint)
"""


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("loader_alias = spec.loader", "loader:context"),
        ("spec.loader.get_code('evil')", "loader:context"),
        ("spec.loader.get_data('evil')", "loader:context"),
        ("spec.loader.create_module(spec)", "loader:context"),
        ("spec.loader.exec_module(extra)", "loader:context"),
        (
            (
                _GRADIO_ENTRYPOINT_LOADER_BLOCK,
                _GRADIO_ENTRYPOINT_LOADER_BLOCK.replace(
                    "assert spec is not None and spec.loader is not None",
                    "assert spec is not None",
                ),
                1,
            ),
            "loader:context",
        ),
        (
            (
                _GRADIO_ENTRYPOINT_LOADER_BLOCK,
                "    assert spec is not None and spec.loader is not None\n"
                "    spec = importlib.util.spec_from_file_location(\n"
                '        "carerisk_space_entrypoint", SPACE_ROOT / "app.py"\n'
                "    )\n"
                "    entrypoint = importlib.util.module_from_spec(spec)\n"
                "    spec.loader.exec_module(entrypoint)\n",
                1,
            ),
            "loader:context",
        ),
        (
            (
                _GRADIO_ENTRYPOINT_LOADER_BLOCK,
                "    spec = importlib.util.spec_from_file_location(\n"
                '        "carerisk_space_entrypoint", SPACE_ROOT / "app.py"\n'
                "    )\n"
                "    entrypoint = importlib.util.module_from_spec(spec)\n"
                "    assert spec is not None and spec.loader is not None\n"
                "    spec.loader.exec_module(entrypoint)\n",
                1,
            ),
            "loader:context",
        ),
        ("captured_spec = spec", "loader:context"),
        ("another_loader = spec.loader", "loader:context"),
    ),
)
def test_gradio_contract_loader_object_context_is_exact(
    case: str | tuple[str, str, int], expected: str
) -> None:
    _assert_gradio_contract_finding(case, expected)


@pytest.mark.parametrize(
    "index",
    range(len(_GRADIO_CANONICAL_MONKEYPATCH_SETATTR_DUMPS)),
    ids=(
        f"{owner}-{position}"
        for position, (owner, _) in enumerate(_GRADIO_CANONICAL_MONKEYPATCH_SETATTR_DUMPS)
    ),
)
def test_gradio_contract_setattr_calls_are_canonical(index: int) -> None:
    tree = _gradio_contract_tree_with_setattr_replacement(index)
    expected = "monkeypatch:canonical"
    assert expected in _gradio_test_source_violations(tree)
    assert expected in _guard_helper_violations(tree)


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        (
            (
                "    parameters = inspect.signature(ui_module.PublicSurfaceGuard).parameters",
                "    signature_result = inspect.signature(ui_module.PublicSurfaceGuard)\n"
                "    parameters = signature_result.parameters",
                1,
            ),
            "exact_parent:signature",
        ),
        (
            (
                "    parameters = inspect.signature(ui_module.PublicSurfaceGuard).parameters",
                "    parameters = inspect.signature("
                "ui_module.PublicSurfaceGuard).return_annotation",
                1,
            ),
            "exact_parent:signature",
        ),
        (
            (
                "    assert all(item.default is inspect.Parameter.empty "
                "for item in parameters.values())",
                "    assert all(item.annotation is inspect.Parameter.empty "
                "for item in parameters.values())",
                1,
            ),
            "exact_parent:Parameter.empty",
        ),
        (
            (
                "        super().__init__(level=logging.DEBUG)",
                "        if False:\n            super().__init__(level=logging.DEBUG)",
                1,
            ),
            "exact_parent:super",
        ),
        (
            (
                "        super().__init__(level=logging.DEBUG)",
                "        try:\n"
                "            super().__init__(level=logging.DEBUG)\n"
                "        finally:\n"
                "            pass",
                1,
            ),
            "exact_parent:super",
        ),
        (
            (
                "        super().__init__(level=logging.DEBUG)",
                "        marker = None\n        super().__init__(level=logging.DEBUG)",
                1,
            ),
            "exact_parent:super",
        ),
    ),
)
def test_gradio_contract_reflection_parents_are_exact(
    case: str | tuple[str, str, int], expected: str
) -> None:
    _assert_gradio_contract_finding(case, expected)


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        (
            "inspection = inspect\ninspection.signature(ui_module.PublicSurfaceGuard)",
            "protected_load:inspect",
        ),
        (
            "inspect.signature(ui_module.create_app)",
            "protected_load:inspect",
        ),
        (
            "api = importlib\napi.import_module('evil')",
            "protected_load:importlib",
        ),
        (
            "importlib.import_module('evil')",
            "protected_load:importlib",
        ),
        (
            "importlib.util.spec_from_file_location('extra', SPACE_ROOT / 'app.py')",
            "protected_load:importlib",
        ),
        (
            "api = importlib\napi.util.spec_from_file_location('extra', SPACE_ROOT / 'app.py')",
            "protected_load:importlib",
        ),
        (
            "module_factory = importlib.util.module_from_spec",
            "protected_load:importlib",
        ),
        (
            "importlib.util.module_from_spec(spec)",
            "protected_load:importlib",
        ),
        (
            "importlib.util.module_from_spec(spec).loader.exec_module(entrypoint)",
            "protected_load:importlib",
        ),
        (
            "importlib.machinery.SourceFileLoader('extra', 'extra.py').load_module()",
            "protected_load:importlib",
        ),
        (
            "gr.mount_gradio_app(parent, demo, path='/extra')",
            "protected_load:gr",
        ),
        ("gr_alias = gr", "protected_load:gr"),
        (
            "uvicorn.Config(marker, host='127.0.0.1', port=7860)",
            "protected_load:uvicorn",
        ),
        (
            "runner = uvicorn\n"
            "config = runner.Config('carerisk_space.ui:Public' + 'SurfaceGuard')\n"
            "config.load()",
            "protected_load:uvicorn",
        ),
        ("uvicorn.Server(config)", "protected_load:uvicorn"),
        (
            "runner = uvicorn\nserver = runner.Server(config)",
            "protected_load:uvicorn",
        ),
        ("socket_alias = socket", "protected_load:socket"),
        ("super_alias = super", "protected_load:super"),
        ("ui_alias = ui_module", "protected_load:ui_module"),
        ("isinstance_alias = isinstance", "protected_load:isinstance"),
        ("frozenset_alias = frozenset", "protected_load:frozenset"),
        ("extra_socket = socket.socket()", "protected_load:socket"),
    ),
)
def test_gradio_contract_protected_identity_loads_are_exact(
    case: str | tuple[str, str, int], expected: str
) -> None:
    _assert_gradio_contract_finding(case, expected)


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("def __function__():\n    pass", "semantic_dunder:__function__"),
        (
            "async def __async_function__():\n    pass",
            "semantic_dunder:__async_function__",
        ),
        ("class __class_name__:\n    pass", "semantic_dunder:__class_name__"),
        ("def added(__posonly__, /):\n    pass", "semantic_dunder:__posonly__"),
        ("def added(__normal__):\n    pass", "semantic_dunder:__normal__"),
        ("def added(*, __kwonly__):\n    pass", "semantic_dunder:__kwonly__"),
        ("def added(*__vararg__):\n    pass", "semantic_dunder:__vararg__"),
        ("def added(**__kwarg__):\n    pass", "semantic_dunder:__kwarg__"),
        ("__assigned__ = value", "semantic_dunder:__assigned__"),
        ("__annotated__: object = value", "semantic_dunder:__annotated__"),
        ("__augmented__ += value", "semantic_dunder:__augmented__"),
        ("del __deleted__", "semantic_dunder:__deleted__"),
        ("for __loop__ in values:\n    pass", "semantic_dunder:__loop__"),
        (
            "async def added():\n    async for __async_loop__ in values:\n        pass",
            "semantic_dunder:__async_loop__",
        ),
        ("[value for __comprehension__ in values]", "semantic_dunder:__comprehension__"),
        (
            "with open('x') as __with_target__:\n    pass",
            "semantic_dunder:__with_target__",
        ),
        (
            "async def added():\n    async with manager as __async_with__:\n        pass",
            "semantic_dunder:__async_with__",
        ),
        ("(__walrus__ := value)", "semantic_dunder:__walrus__"),
        ("import __import_original__", "semantic_dunder:__import_original__"),
        ("import os as __import_alias__", "semantic_dunder:__import_alias__"),
        (
            "from os import __from_original__",
            "semantic_dunder:__from_original__",
        ),
        (
            "from os import path as __from_alias__",
            "semantic_dunder:__from_alias__",
        ),
        (
            "try:\n    pass\nexcept Exception as __exception__:\n    pass",
            "semantic_dunder:__exception__",
        ),
        (
            "match value:\n    case __match_as__:\n        pass",
            "semantic_dunder:__match_as__",
        ),
        (
            "match value:\n    case [*__match_star__]:\n        pass",
            "semantic_dunder:__match_star__",
        ),
        (
            "match value:\n    case {**__match_rest__}:\n        pass",
            "semantic_dunder:__match_rest__",
        ),
        (
            "def added():\n    global __global__",
            "semantic_dunder:__global__",
        ),
        (
            "def outer():\n    __nonlocal__ = value\n"
            "    def inner():\n        nonlocal __nonlocal__",
            "semantic_dunder:__nonlocal__",
        ),
    ),
)
def test_gradio_contract_semantic_dunder_bindings_are_denied(
    case: str | tuple[str, str, int], expected: str
) -> None:
    _assert_gradio_contract_finding(case, expected)


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        *(
            (
                f'monkeypatch.setattr(ui_module, "{member}", sink)',
                "monkeypatch:load",
            )
            for member in (
                "__getattribute__",
                "__getattr__",
                "__setattr__",
                "__delattr__",
                "__class__",
                "__dict__",
                "__globals__",
                "__getitem__",
                "__call__",
                "__init__",
            )
        ),
        ("setter = monkeypatch.setattr", "monkeypatch:load"),
        ("mp = monkeypatch\nmp.setitem(mapping, 'x', 1)", "monkeypatch:load"),
        (
            "mp = monkeypatch\nsetter = mp.setitem",
            "monkeypatch:load",
        ),
        (
            "method = monkeypatch.helper.setattr",
            "monkeypatch:load",
        ),
        ("monkeypatch.setitem(mapping, 'x', 1)", "monkeypatch:load"),
        ("monkeypatch.delattr(ui_module, 'create_app')", "monkeypatch:load"),
        ("monkeypatch.setenv('EXTRA', '1')", "monkeypatch:load"),
        (
            (
                "def make_unit_failure_bundle(\n",
                "@pytest.fixture\ndef make_unit_failure_bundle(\n",
                1,
            ),
            "monkeypatch:load",
        ),
        ("make_unit_failure_bundle = sink", "monkeypatch:load"),
        (
            (
                "tmp_path: Path, code: EvidenceFailureCode, monkeypatch: pytest.MonkeyPatch",
                "tmp_path: Path, code: EvidenceFailureCode, patcher: pytest.MonkeyPatch",
                1,
            ),
            "monkeypatch:load",
        ),
        (
            (
                'monkeypatch.setattr(evidence_module, "RECEIPT_SHA256",',
                'monkeypatch.setitem(evidence_module, "RECEIPT_SHA256",',
                1,
            ),
            "monkeypatch:load",
        ),
        (
            (
                "def _fake_asset_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path)",
                "@pytest.fixture\ndef _fake_asset_roots("
                "monkeypatch: pytest.MonkeyPatch, tmp_path: Path)",
                1,
            ),
            "monkeypatch:load",
        ),
        ("_fake_asset_roots = sink", "monkeypatch:load"),
        (
            (
                "def _fake_asset_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path)",
                "def _fake_asset_roots(patcher: pytest.MonkeyPatch, tmp_path: Path)",
                1,
            ),
            "monkeypatch:load",
        ),
        (
            (
                'monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", build)',
                'monkeypatch.setitem(ui_module, "BUILD_PATH_LIB", build)',
                1,
            ),
            "monkeypatch:load",
        ),
    ),
)
def test_gradio_contract_monkeypatch_loads_are_exact(
    case: str | tuple[str, str, int], expected: str
) -> None:
    _assert_gradio_contract_finding(case, expected)


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("sys.platform = 'evil'", "sys:context"),
        ("del sys.platform", "sys:context"),
        ("platform_alias = sys.platform", "sys:context"),
        ("sys.platform == 'linux'", "sys:context"),
        ("bool(sys.platform)", "sys:context"),
        ("sys.platform != 'win32'", "sys:context"),
    ),
)
def test_gradio_contract_sys_platform_contexts_are_exact(
    case: str | tuple[str, str, int], expected: str
) -> None:
    _assert_gradio_contract_finding(case, expected)


def test_gradio_contract_source_is_closed_world_reflection_free() -> None:
    tree = _tree(SPACE_ROOT / "tests" / "test_gradio_contract.py")
    assert _gradio_test_source_violations(tree) == []


@pytest.mark.parametrize(
    "appendix",
    (
        "reflect = getattr",
        "reflect = setattr",
        "reflect = delattr",
        "reflect = hasattr",
        "reflect = vars",
        "reflect = globals",
        "reflect = locals",
        "reflect = eval",
        "reflect = exec",
        "reflect = compile",
        "reflect = __import__",
        "mapping = __builtins__",
        "import builtins",
        "from builtins import getattr as reflect",
        "from operator import attrgetter as reflect",
        "from operator import methodcaller as reflect",
        "reflect = inspect.getattr_static",
        "reflect = inspect.getmembers",
        "reflect = importlib.import_module",
        "value = ui_module.__dict__",
        "value = ui_module.__globals__",
        "value = ui_module.__class__",
        "value = ui_module.__getattribute__",
        "value = ui_module.__getattr__",
        "value = ui_module.__setattr__",
        "value = ui_module.__delattr__",
        "value = ui_module.__getitem__",
        "value = ui_module.__call__",
        "def added():\n    return getattr(inner, 'router', None)",
        "def added():\n    return getattr(other, 'original_router', None)",
        "def added():\n    return getattr(inner, 'original_router')",
        "def added():\n    return getattr(inner, 'original_router', False)",
        "def added():\n    return getattr(inner, 'original_router', None, None)",
        "def added():\n    return getattr(inner, name='original_router', default=None)",
        "def added():\n    reflect = getattr\n    return reflect(inner, 'original_router', None)",
        "captured = lambda: getattr",
        "def added(reflect=getattr):\n    return reflect(inner, 'original_router', None)",
        "def getattr(value):\n    return value",
        "class getattr:\n    pass",
        "def added(getattr):\n    return getattr(inner, 'original_router', None)",
        "def added():\n    return getattr(socket, 'SOCK_STREAM', None)",
        "def added():\n    return getattr(other, 'AF_UNIX', None)",
        "def added():\n    return getattr(socket, 'AF_UNIX')",
        "def added():\n    return getattr(socket, 'AF_UNIX', False)",
        "def added():\n    return getattr(socket, name='AF_UNIX', default=None)",
        "type = sink",
        "inspect = sink",
        "importlib = sink",
        "ui_module = sink",
        "gr = sink",
        "uvicorn = sink",
        "isinstance = sink",
        "super = sink",
        "frozenset = sink",
        "socket = sink",
        "pytest = sink",
        "breakpoint()",
        "bp = breakpoint\nbp()",
        "dir(ui_module)",
        "lookup = dir\nlookup(ui_module)",
        "help('evil_module')",
        "help('carerisk_space.ui.' + 'Public' + 'SurfaceGuard')",
        "from unittest.mock import patch",
        "from unittest.mock import patch as replace",
        "import mock",
        "import pytest_mock",
        "def added(mocker):\n    return mocker.patch('x')",
        "@patch('x')\ndef added():\n    pass",
        "def added():\n    with patch.object(ui_module, 'x'):\n        pass",
        "def added():\n    return pytest.importorskip('pkgutil').resolve_name('x')",
        "def added():\n    return uvicorn.importer.import_from_string('x')",
        "def added():\n    return pytest.main([])",
        "def added(request):\n    return request.config.pluginmanager.import_plugin('x')",
        "class TestEscape:\n"
        "    def test_escape(self, request):\n"
        "        return request.module.importlib.reload(ui_module)",
        "fixture_alias = pytest.fixture\n@fixture_alias\ndef alias_fixture():\n    return None",
        "fixture_value = pytest.fixture",
        "_assert_entrypoint_positional_identity = sink",
        "loaded_identity_helper = _assert_entrypoint_positional_identity",
        "def third_identity_callsite():\n"
        "    return _assert_entrypoint_positional_identity(a, b, c, d)",
        "def _assert_entrypoint_positional_identity(entrypoint: Any):\n    return entrypoint",
        "from escape import _assert_entrypoint_positional_identity",
        "del _assert_entrypoint_positional_identity",
        "def rebind_identity_helper():\n"
        "    global _assert_entrypoint_positional_identity\n"
        "    _assert_entrypoint_positional_identity = sink",
        "def outer_identity_binding():\n"
        "    _assert_entrypoint_positional_identity = sink\n"
        "    def inner_identity_binding():\n"
        "        nonlocal _assert_entrypoint_positional_identity\n"
        "        return _assert_entrypoint_positional_identity",
        "resolver = locate\nvalue = resolver('carerisk_space.ui.PublicSurfaceGuard')",
        "value = find_spec('evil')",
        "value = object().gi_frame",
        "value = object().cr_frame",
        "value = object().ag_frame",
        "value = object().tb_frame",
        "value = object().f_builtins",
        "value = object().f_globals",
        "value = object().f_locals",
        "value = object().f_back",
        "value = object()._getframe",
        "value = object()._current_frames",
        "value = os.sys",
        "value = sys.modules",
        "from sys import modules",
        "from sys import modules as registry",
        "registry = sys.modules\nregistry.update({'inspect': sink})",
        "alias = Path",
        "SPACE_ROOT = Path('/tmp')",
        "del SPACE_ROOT",
        "def added():\n    global SPACE_ROOT\n    SPACE_ROOT = Path('/tmp')",
        "(SPACE_ROOT / 'carerisk_space' / 'ui.py').write_text('x')",
        "os.environ['PYTHONBREAKPOINT'] = "
        "'carerisk_space.ui.Public' + 'SurfaceGuard'\nbreakpoint()",
    ),
)
def test_gradio_contract_source_rejects_reflection_near_misses(appendix: str) -> None:
    assert _gradio_test_source_violations(_gradio_contract_tree_with_appendix(appendix))


@pytest.mark.parametrize(
    ("old", "new", "count"),
    (
        (
            "parameters = inspect.signature(ui_module.PublicSurfaceGuard).parameters",
            "guard_type = ui_module.PublicSurfaceGuard\n"
            "    parameters = inspect.signature(guard_type).parameters",
            1,
        ),
        (
            "membership = ui_module.build_package_asset_membership()",
            "builder = ui_module.build_package_asset_membership\n    membership = builder()",
            1,
        ),
        (
            "return ui_module.PublicSurfaceGuard(parent, membership)",
            "ui_alias = ui_module\n    return ui_alias.PublicSurfaceGuard(parent, membership)",
            1,
        ),
        (
            "parameters = inspect.signature(ui_module.PublicSurfaceGuard).parameters",
            "parameters = inspect.signature(ui_module.build_package_asset_membership).parameters",
            1,
        ),
        (
            "assert isinstance(membership, frozenset)",
            "assert isinstance(ui_module.PublicSurfaceGuard, frozenset)",
            1,
        ),
        (
            'monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)',
            'monkeypatch.setattr(ui_alias, "create_app", lambda bundle_root=None: demo)',
            1,
        ),
        (
            'monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)',
            'monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: membership)',
            1,
        ),
        (
            'monkeypatch.setattr(ui_module, "build_package_asset_membership", lambda: membership)',
            'monkeypatch.setattr(ui_alias, "build_package_asset_membership", lambda: membership)',
            1,
        ),
        (
            'monkeypatch.setattr(gr, "mount_gradio_app", fake_mount)',
            'monkeypatch.setattr(gr_alias, "mount_gradio_app", fake_mount)',
            1,
        ),
        (
            'monkeypatch.setattr(entrypoint.uvicorn, "run", fake_run)',
            'monkeypatch.setattr(entrypoint.uvicorn, "run", lambda *args: None)',
            1,
        ),
        (
            'monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)',
            'monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)\n'
            '    monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)',
            1,
        ),
        (
            "def test_entrypoint_mount_and_uvicorn_contract_are_exact(",
            "def test_wrong_owner(",
            1,
        ),
        (
            '@pytest.fixture(scope="module")',
            '@pytest.fixture(scope="session")',
            1,
        ),
        (
            '@pytest.fixture(scope="module")',
            '@pytest.fixture(scope="module", autouse=False)',
            1,
        ),
        (
            '@pytest.fixture(scope="module")',
            '@pytest.fixture("module")',
            1,
        ),
        (
            "@pytest.fixture\n",
            "@pytest.fixture()\n",
            1,
        ),
        (
            "@pytest.fixture\n",
            "fixture_alias = pytest.fixture\n@fixture_alias\n",
            1,
        ),
        (
            "@pytest.fixture\n",
            "pytest.fixture\n@pytest.fixture\n",
            1,
        ),
        (
            "def _assert_entrypoint_positional_identity(",
            "def _wrong_identity_helper_owner(",
            1,
        ),
        (
            "    entrypoint: Any,\n    mounted_parent: FastAPI,",
            "    mounted_parent: FastAPI,\n    entrypoint: Any,",
            1,
        ),
        (
            "    entrypoint: Any,",
            "    entrypoint: object,",
            1,
        ),
        (
            "def _assert_entrypoint_positional_identity(",
            "@pytest.fixture\ndef _assert_entrypoint_positional_identity(",
            1,
        ),
        (
            "    entrypoint: Any,\n    mounted_parent: FastAPI,",
            "    entrypoint: Any,\n    entrypoint_again: Any,\n    mounted_parent: FastAPI,",
            1,
        ),
        (
            "    assert served_app.downstream is mounted_parent",
            "    assert served_app.downstream is mounted_parent\n    return None",
            1,
        ),
        (
            "    assert mounted_parent is entrypoint.parent",
            "    if False:\n        assert mounted_parent is entrypoint.parent",
            1,
        ),
        (
            "    assert mounted_parent is entrypoint.parent",
            "    try:\n        assert mounted_parent is entrypoint.parent\n"
            "    finally:\n        pass",
            1,
        ),
        (
            "    assert mounted_parent is entrypoint.parent\n"
            "    assert mounted_demo is entrypoint.demo",
            "    assert mounted_demo is entrypoint.demo\n"
            "    assert mounted_parent is entrypoint.parent",
            1,
        ),
        (
            "    assert mounted_parent is entrypoint.parent\n",
            "",
            1,
        ),
        (
            "    assert mounted_parent is entrypoint.parent",
            "    assert mounted_parent == entrypoint.parent",
            1,
        ),
        (
            "    _assert_entrypoint_positional_identity(\n        entrypoint,",
            "    holder._assert_entrypoint_positional_identity(\n        entrypoint,",
            1,
        ),
        (
            'monkeypatch.setattr(sys, "platform", "linux")',
            'monkeypatch.setattr(sys.modules["builtins"], "isinstance", sink)',
            1,
        ),
        (
            'monkeypatch.setattr(sys, "platform", "linux")',
            'target = inspect\n    monkeypatch.setattr(target, "signature", sink)',
            1,
        ),
        (
            'monkeypatch.setattr(sys, "platform", "linux")',
            'monkeypatch.setitem(sys.modules, "inspect", sink)',
            1,
        ),
        (
            "monkeypatch.setenv(name, value)",
            "monkeypatch.setenv(name=name, value=value)",
            1,
        ),
        (
            "monkeypatch.setenv(name, value)",
            "monkeypatch.setenv(name, 'changed')",
            1,
        ),
        (
            "monkeypatch.setenv(name, value)",
            "monkeypatch.setenv(name, value)\n        monkeypatch.setenv(name, value)",
            1,
        ),
        (
            "def test_exact_instance_state_ignores_poisoned_framework_environment(",
            "def test_wrong_setenv_owner(",
            1,
        ),
        (
            '"PORT": "9999",',
            '"PORT": "9998",',
            1,
        ),
        (
            '"PORT": "9999",',
            '"PORT": "9999",\n        "EXTRA": "forbidden",',
            1,
        ),
        (
            "for name, value in {",
            "for key, value in {",
            1,
        ),
        (
            '"carerisk_space_entrypoint", SPACE_ROOT / "app.py"',
            '"evil_entrypoint", SPACE_ROOT / "app.py"',
            1,
        ),
        (
            "entrypoint = importlib.util.module_from_spec(spec)",
            "entrypoint = importlib.util.module_from_spec(spec, extra=True)",
            1,
        ),
        (
            "spec.loader.exec_module(entrypoint)",
            "loader.exec_module(entrypoint)",
            1,
        ),
        (
            "config = uvicorn.Config(\n        marker,",
            "config = uvicorn.Config(\n        'carerisk_space.app:app',",
            1,
        ),
        (
            'http="h11",',
            'http="auto",',
            1,
        ),
        (
            "marker = AppEntryMarker(guarded, guarded.package_asset_urls)",
            "marker = 'carerisk_space.app:app'",
            1,
        ),
        (
            "class AppEntryMarker:",
            "@lambda cls: cls\nclass AppEntryMarker:",
            1,
        ),
        (
            "class AppEntryMarker:",
            "class AppEntryMarker(object):",
            1,
        ),
        (
            "class AppEntryMarker:",
            "class AppEntryMarker(metaclass=type):",
            1,
        ),
        (
            "import inspect\nimport io",
            "import inspect as inspection\nimport io",
            1,
        ),
        (
            "import inspect\nimport io",
            "import io\nimport inspect",
            1,
        ),
        (
            "ALL_FAILURE_CODES = cast(tuple[EvidenceFailureCode, ...], "
            "get_args(EvidenceFailureCode))\nSPACE_ROOT",
            "ALL_FAILURE_CODES = cast(tuple[EvidenceFailureCode, ...], "
            "get_args(EvidenceFailureCode))\nDRIFT = True\nSPACE_ROOT",
            1,
        ),
    ),
)
def test_gradio_contract_sensitive_members_have_exact_contexts(
    old: str, new: str, count: int
) -> None:
    assert _gradio_test_source_violations(_mutated_gradio_contract_tree(old, new, count=count))


def test_existing_guard_helpers_derive_membership_from_the_pinned_builder() -> None:
    tree = _tree(SPACE_ROOT / "tests" / "test_gradio_contract.py")
    assert _guard_helper_violations(tree) == []


def _assert_guard_helper_audit_rejects(
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    synthetic_tree = ast.parse(source)
    with monkeypatch.context() as patch:
        patch.setitem(_tree.__globals__, "_tree", lambda path: synthetic_tree)
        with pytest.raises(AssertionError):
            test_existing_guard_helpers_derive_membership_from_the_pinned_builder()


def test_guard_helper_audit_rejects_deleted_type_or_nonempty_assertions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for deleted_assertion in (
        "assert isinstance(membership, frozenset)",
        "assert membership",
    ):
        source = """
def _compose(parent):
    membership = ui_module.build_package_asset_membership()
    assert isinstance(membership, frozenset)
    assert membership
    return ui_module.PublicSurfaceGuard(parent, membership)
""".replace(f"    {deleted_assertion}\n", "")
        _assert_guard_helper_audit_rejects(monkeypatch, source)


def test_guard_helper_audit_rejects_empty_or_different_second_argument(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for mutation in (
        "membership = frozenset()\n    return ui_module.PublicSurfaceGuard(parent, membership)",
        "return ui_module.PublicSurfaceGuard(parent, frozenset())",
    ):
        source = f"""
def _compose(parent):
    membership = ui_module.build_package_asset_membership()
    assert isinstance(membership, frozenset)
    assert membership
    {mutation}
"""
        _assert_guard_helper_audit_rejects(monkeypatch, source)


def test_guard_helper_audit_rejects_bounded_builder_and_guard_alias_lineage() -> None:
    tree = ast.parse(
        """
def _compose(parent):
    builder = ui_module.build_package_asset_membership
    builder_alias = builder
    guard_type = ui_module.PublicSurfaceGuard
    guard_alias = guard_type
    membership = builder_alias()
    assert isinstance(membership, frozenset)
    assert membership
    return guard_alias(parent, membership)
"""
    )
    assert _guard_helper_violations(tree)


def test_guard_helper_audit_rejects_sensitive_reflection_candidates() -> None:
    sources = (
        """
def _compose(parent):
    builder = ui_module.__getattribute__("build_package_asset_membership")
    guard = ui_module.__getattribute__("PublicSurfaceGuard")
    membership = builder()
    assert isinstance(membership, frozenset)
    assert membership
    return guard(parent, membership)
""",
        """
def _compose(parent):
    builder = vars(ui_module)["build_package_asset_membership"]
    guard = vars(ui_module)["PublicSurfaceGuard"]
    membership = builder()
    assert isinstance(membership, frozenset)
    assert membership
    return guard(parent, membership)
""",
        """
def _compose(parent):
    builder = ui_module.__dict__["build_package_asset_membership"]
    guard = ui_module.__dict__["PublicSurfaceGuard"]
    membership = builder()
    assert isinstance(membership, frozenset)
    assert membership
    return guard(parent, membership)
""",
        """
def _compose(parent):
    member = runtime_member
    guard = ui_module.__getattribute__(member)
    membership = ui_module.build_package_asset_membership()
    assert isinstance(membership, frozenset)
    assert membership
    return guard(parent, membership)
""",
        """
def _compose(parent):
    reflect = getattr
    member = runtime_member
    guard = reflect(ui_module, member)
    membership = ui_module.build_package_asset_membership()
    assert isinstance(membership, frozenset)
    assert membership
    return guard(parent, membership)
""",
        """
def _compose(parent):
    reflect = __builtins__["getattr"]
    guard = reflect(ui_module, "PublicSurfaceGuard")
    membership = ui_module.build_package_asset_membership()
    assert isinstance(membership, frozenset)
    assert membership
    return guard(parent, membership)
""",
        """
def _compose(parent):
    builtins_map = __builtins__
    return builtins_map["getattr"](ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    builtins_map = __builtins__
    mapping_alias = builtins_map
    reflect = mapping_alias.get("getattr")
    reflect_alias = reflect
    return reflect_alias(ui_module, "PublicSurfaceGuard")
""",
        """
from carerisk_space.ui import __builtins__ as builtin_map

def _compose(parent):
    return builtin_map["getattr"](ui_module, "PublicSurfaceGuard")
""",
        """
builtins_map = __builtins__
reflect = builtins_map["getattr"]

def _compose(parent):
    return reflect(ui_module, "PublicSurfaceGuard")
""",
        """
import builtins as builtin_map

def _compose(parent):
    return builtin_map.getattr(ui_module, "PublicSurfaceGuard")
""",
        """
from builtins import getattr as reflect
sensitive_alias = ui_module

def _compose(parent):
    return reflect(sensitive_alias, "PublicSurfaceGuard")
""",
        """
guard = getattr(ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
guard = __builtins__["getattr"](ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
mapping = b.__dict__
reflect = mapping["getattr"]

def _compose(parent):
    return reflect(ui_module, "PublicSurfaceGuard")
""",
        """
import builtins as b
mapping = vars(b)
reflect = mapping["getattr"]

def _compose(parent):
    return reflect(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as builtin_map
    return builtin_map.getattr(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    from builtins import getattr as reflect
    return reflect(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return b.__dict__["getattr"](ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return b.__dict__[runtime_member](ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return b.__dict__.get("getattr")(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return b.__dict__.get(runtime_member)(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return vars(b)["getattr"](ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return vars(b)[runtime_member](ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return vars(b).get("getattr")(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return vars(b).get(runtime_member)(ui_module, "PublicSurfaceGuard")
""",
        """
import builtins as b
guard = b.__dict__["getattr"](ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
guard = b.__dict__[runtime_member](ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
guard = b.__dict__.get("getattr")(ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
guard = b.__dict__.get(runtime_member)(ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
guard = vars(b)["getattr"](ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
guard = vars(b)[runtime_member](ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
guard = vars(b).get("getattr")(ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
import builtins as b
guard = vars(b).get(runtime_member)(ui_module, "PublicSurfaceGuard")

def _compose(parent):
    return guard(parent, membership)
""",
        """
def _compose(parent):
    import builtins as b
    v = vars
    mapping = v(b)
    return mapping[runtime_member](ui_module, "PublicSurfaceGuard")
""",
        """
import builtins as b
v = vars
mapping = v(b)
reflect = mapping[runtime_member]

def _compose(parent):
    return reflect(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    reflect = getattr
    return reflect.__call__(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    reflect = getattr
    call = reflect.__call__
    call_alias = call
    return call_alias(ui_module, "PublicSurfaceGuard")
""",
        """
reflect = getattr
call = reflect.__call__

def _compose(parent):
    return call(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    import builtins as b
    return b.getattr.__call__(ui_module, "PublicSurfaceGuard")
""",
        """
def _compose(parent):
    return inspect.getattr_static.__call__(ui_module, "PublicSurfaceGuard")
""",
    )
    for source in sources:
        assert _guard_helper_violations(ast.parse(source))


def test_guard_helper_audit_allows_unrelated_attributes_and_request_locals() -> None:
    tree = _gradio_contract_tree_with_appendix(
        """
def _other_member(other):
    return other.get

def _request_local(request_bytes):
    request = request_bytes
    for request in (request,):
        pass
    return request
"""
    )
    assert _guard_helper_violations(tree) == []


@pytest.mark.parametrize(
    "body",
    (
        "return guard_alias(parent, membership)",
        "assert isinstance(membership, frozenset)\n    assert membership\n"
        "    return guard_alias(parent, frozenset())",
        "assert isinstance(membership, frozenset)\n    assert membership\n"
        "    membership = frozenset()\n    return guard_alias(parent, membership)",
    ),
)
def test_guard_helper_audit_rejects_alias_bypass_mutations(body: str) -> None:
    tree = ast.parse(
        f"""
def _compose(parent):
    builder = ui_module.build_package_asset_membership
    builder_alias = builder
    guard_type = ui_module.PublicSurfaceGuard
    guard_alias = guard_type
    membership = builder_alias()
    {body}
"""
    )
    assert _guard_helper_violations(tree)


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
