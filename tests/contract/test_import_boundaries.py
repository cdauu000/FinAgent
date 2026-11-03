import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def graph() -> dict[str, set[str]]:
    paths = list((ROOT / "finagent").rglob("*.py"))
    modules = {
        ".".join(path.relative_to(ROOT).with_suffix("").parts).removesuffix(".__init__"): path
        for path in paths
    }
    result = {name: set() for name in modules}
    for name, path in modules.items():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imports = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, "Use absolute imports so boundaries remain auditable"
                imports = [node.module or ""]
                imports += [(node.module + "." + item.name) for item in node.names if node.module]
            else:
                continue
            for imported in imports:
                if imported in modules:
                    result[name].add(imported)
                assert not imported.startswith(("eval", "corpus.teacher")), (name, imported)
                if not name.startswith("finagent.llm_gateway.adapters"):
                    assert not imported.startswith(
                        ("openai", "groq", "google.genai", "deepseek")
                    ), name
                if name.startswith("finagent.llm_gateway."):
                    assert not imported.startswith(
                        (
                            "finagent.store",
                            "finagent.evidence_gate",
                            "finagent.agent",
                            "finagent.corpus",
                        )
                    ), (name, imported)
                if name.startswith("finagent.local."):
                    assert not imported.startswith(("finagent.llm_gateway", "httpx", "requests")), (
                        name
                    )
    return result


def test_import_graph_has_no_cycles_or_forbidden_transitive_dependencies() -> None:
    edges = graph()
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(module: str) -> None:
        assert module not in visiting, f"Import cycle at {module}"
        if module in visited:
            return
        visiting.add(module)
        for child in edges[module]:
            visit(child)
        visiting.remove(module)
        visited.add(module)

    for module in edges:
        visit(module)


def test_domain_has_no_dynamic_code_execution() -> None:
    for path in (ROOT / "finagent").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}, path
