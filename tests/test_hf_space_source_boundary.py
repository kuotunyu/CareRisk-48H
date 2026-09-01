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


def _expected_rejection_guard_calls(
    function: ast.FunctionDef,
    aliases: dict[str, str],
) -> set[ast.Call]:
    calls: set[ast.Call] = set()
    for node in ast.walk(function):
        if not isinstance(node, (ast.With, ast.AsyncWith)) or not any(
            isinstance(item.context_expr, ast.Call)
            and _resolved_name(item.context_expr.func, aliases) == "pytest.raises"
            for item in node.items
        ):
            continue
        calls.update(
            call
            for statement in node.body
            for call in ast.walk(statement)
            if isinstance(call, ast.Call)
            and _resolved_name(call.func, aliases) == "ui_module.PublicSurfaceGuard"
        )
    return calls


_ReflectionAliasState = tuple[set[str], set[str], set[str], set[str], set[str]]
_SENSITIVE_ALIAS = "sensitive"
_BUILTIN_MODULE_ALIAS = "builtin_module"
_BUILTIN_MAPPING_ALIAS = "builtin_mapping"
_REFLECTION_CALLABLE_ALIAS = "reflection_callable"
_VARS_CALLABLE_ALIAS = "vars_callable"


def _owned_nodes(statements: Iterable[ast.stmt]) -> list[ast.AST]:
    owned: list[ast.AST] = []
    pending: list[ast.AST] = list(statements)
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        owned.append(node)
        pending.extend(ast.iter_child_nodes(node))
    return owned


def _assignment_names(node: ast.AST) -> set[str]:
    return {target.id for target in _assignment_targets(node) if isinstance(target, ast.Name)}


def _effective_import_name(node: ast.alias, parent: ast.AST) -> str:
    if isinstance(parent, ast.Import):
        return node.asname or node.name.split(".", 1)[0]
    return node.asname or node.name


def _state_has_name(node: ast.expr, names: set[str]) -> bool:
    return isinstance(node, ast.Name) and node.id in names


def _mapping_source(node: ast.expr, state: _ReflectionAliasState) -> bool:
    _, builtin_modules, builtin_mappings, _, vars_callables = state
    if _state_has_name(node, builtin_mappings):
        return True
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "__dict__"
        and _state_has_name(node.value, builtin_modules)
    ):
        return True
    if not (
        isinstance(node, ast.Call)
        and len(node.args) == 1
        and not node.keywords
        and _state_has_name(node.args[0], builtin_modules)
    ):
        return False
    return _state_has_name(node.func, vars_callables) or _reflection_callable_source(
        node.func,
        state,
    )


def _reflection_callable_source(
    node: ast.expr,
    state: _ReflectionAliasState,
) -> bool:
    _, builtin_modules, _, reflection_callables, _ = state
    if isinstance(node, ast.Name):
        return node.id in reflection_callables
    if isinstance(node, ast.Attribute):
        if _call_name(node) in reflection_callables:
            return True
        if node.attr == "__call__":
            return _reflection_callable_source(node.value, state)
        return node.attr != "__dict__" and _state_has_name(node.value, builtin_modules)
    if isinstance(node, ast.Subscript):
        return _mapping_source(node.value, state)
    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and _mapping_source(node.func.value, state)
        ):
            return True
        return (
            bool(node.args)
            and _state_has_name(node.args[0], builtin_modules)
            and _reflection_callable_source(node.func, state)
        )
    return False


def _bounded_reflection_state(
    statements: Iterable[ast.stmt],
    inherited: _ReflectionAliasState | None = None,
    *,
    include_parent: bool = False,
) -> _ReflectionAliasState:
    if inherited is None:
        sensitive_aliases = {"ui_module", "gr", "uvicorn"}
        builtin_module_aliases: set[str] = set()
        builtin_mapping_aliases = {"__builtins__"}
        reflection_callable_aliases = set(
            (_FORBIDDEN_REFLECTION_NAMES - {"__builtins__"}) | _FORBIDDEN_REFLECTION_HELPERS
        )
        vars_callable_aliases = {"vars"}
    else:
        (
            sensitive_aliases,
            builtin_module_aliases,
            builtin_mapping_aliases,
            reflection_callable_aliases,
            vars_callable_aliases,
        ) = (set(items) for items in inherited)
    if include_parent:
        sensitive_aliases.add("parent")
    state = (
        sensitive_aliases,
        builtin_module_aliases,
        builtin_mapping_aliases,
        reflection_callable_aliases,
        vars_callable_aliases,
    )
    owned = _owned_nodes(statements)
    for node in owned:
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name == "builtins":
                    builtin_module_aliases.add(_effective_import_name(imported, node))
        elif isinstance(node, ast.ImportFrom):
            for imported in node.names:
                effective_name = _effective_import_name(imported, node)
                if imported.name == "__builtins__":
                    builtin_mapping_aliases.add(effective_name)
                if (
                    node.module == "builtins"
                    and imported.name in _FORBIDDEN_REFLECTION_NAMES
                    and imported.name != "__builtins__"
                ):
                    reflection_callable_aliases.add(effective_name)
                    if imported.name == "vars":
                        vars_callable_aliases.add(effective_name)

    assignments = [
        node
        for node in owned
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None
    ]
    for _ in range(len(assignments) + 1):
        changed = False
        for assignment in assignments:
            value = assignment.value
            if value is None:
                continue
            targets = _assignment_names(assignment)
            transitions = (
                (sensitive_aliases, _state_has_name(value, sensitive_aliases)),
                (builtin_module_aliases, _state_has_name(value, builtin_module_aliases)),
                (builtin_mapping_aliases, _mapping_source(value, state)),
                (reflection_callable_aliases, _reflection_callable_source(value, state)),
                (vars_callable_aliases, _state_has_name(value, vars_callable_aliases)),
            )
            for aliases, applies in transitions:
                if applies and not targets <= aliases:
                    aliases.update(targets)
                    changed = True
        if not changed:
            break
    return state


def _reflection_state_aliases(state: _ReflectionAliasState) -> dict[str, str]:
    categories: dict[str, set[str]] = {}
    for marker, names in zip(
        (
            _SENSITIVE_ALIAS,
            _BUILTIN_MODULE_ALIAS,
            _BUILTIN_MAPPING_ALIAS,
            _REFLECTION_CALLABLE_ALIAS,
            _VARS_CALLABLE_ALIAS,
        ),
        state,
        strict=True,
    ):
        for name in names:
            categories.setdefault(name, set()).add(marker)
    return {name: "|".join(sorted(markers)) for name, markers in categories.items()}


def _aliases_in_category(aliases: dict[str, str], marker: str) -> set[str]:
    return {name for name, categories in aliases.items() if marker in categories.split("|")}


def _sensitive_reflection_in_nodes(
    nodes: Iterable[ast.AST],
    aliases: dict[str, str],
) -> bool:
    state = (
        _aliases_in_category(aliases, _SENSITIVE_ALIAS),
        _aliases_in_category(aliases, _BUILTIN_MODULE_ALIAS),
        _aliases_in_category(aliases, _BUILTIN_MAPPING_ALIAS),
        _aliases_in_category(aliases, _REFLECTION_CALLABLE_ALIAS),
        _aliases_in_category(aliases, _VARS_CALLABLE_ALIAS),
    )
    sensitive_aliases = state[0]

    def is_sensitive_receiver(node: ast.expr) -> bool:
        while isinstance(node, ast.Attribute):
            node = node.value
        return _state_has_name(node, sensitive_aliases)

    for node in nodes:
        if (
            isinstance(node, ast.Attribute)
            and node.attr
            in (_FORBIDDEN_DYNAMIC_PROTOCOL_LITERALS | {"__dict__", "__globals__", "__class__"})
            and is_sensitive_receiver(node.value)
        ):
            return True
        if (
            isinstance(node, ast.Call)
            and node.args
            and is_sensitive_receiver(node.args[0])
            and (
                _reflection_callable_source(node.func, state)
                or isinstance(node.func, ast.Call)
                and _call_name(node.func.func) in _FORBIDDEN_REFLECTION_HELPERS
            )
        ):
            return True
    return False


def _sensitive_reflection_in_helper(
    function: ast.FunctionDef,
    aliases: dict[str, str],
) -> bool:
    return _sensitive_reflection_in_nodes(_owned_nodes(function.body), aliases)


def _guard_helper_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    module_state = _bounded_reflection_state(tree.body)
    if _sensitive_reflection_in_nodes(
        _owned_nodes(tree.body),
        _reflection_state_aliases(module_state),
    ):
        violations.append("module:sensitive_reflection")
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    for function in functions:
        function_state = _bounded_reflection_state(
            function.body,
            module_state,
            include_parent=True,
        )
        reflection_aliases = _reflection_state_aliases(function_state)
        if _sensitive_reflection_in_helper(function, reflection_aliases):
            violations.append(f"{function.name}:sensitive_reflection")
        aliases, _ = _bounded_aliases(
            function,
            frozenset({"ui_module", "gr", "parent", "uvicorn"})
            | _FORBIDDEN_REFLECTION_NAMES
            | _FORBIDDEN_REFLECTION_HELPERS,
        )
        all_guard_calls = _resolved_calls(function, aliases, "ui_module.PublicSurfaceGuard")
        if not all_guard_calls:
            continue
        rejected_calls = _expected_rejection_guard_calls(function, aliases)
        guard_calls = [call for call in all_guard_calls if call not in rejected_calls]
        if not guard_calls:
            violations.append(f"{function.name}:positive_guard_call")
            continue
        builder_calls = _resolved_calls(
            function,
            aliases,
            "ui_module.build_package_asset_membership",
        )
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
    return violations


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


def test_guard_helper_audit_accepts_bounded_builder_and_guard_alias_lineage() -> None:
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
    assert _guard_helper_violations(tree) == []


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


def test_guard_helper_audit_allows_unrelated_test_introspection() -> None:
    tree = ast.parse(
        """
def _other_member(other):
    return getattr(other, "get")

def _original_router(inner):
    return getattr(inner, "original_router", None)

def _unix_family(socket):
    return getattr(socket, "AF_UNIX", None)
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
