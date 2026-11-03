"""Read-only comparison against the actual source checkouts used for the Faro demo."""
import ast
import subprocess
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1]
SCOUT = DEMO / "scout/machine-learning-scout-api/infer/scout"
SIGNAL = DEMO / "signal/machine-learning-signal-api/infer/signal/signal"
LUNA = Path.home() / "machine-learning-luna"
NEMO = Path.home() / "machine-learning-nemo"
SEMANTICA = Path.home() / "Projects/Semantica/confluence/confluence"


def source(repo, ref, name):
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{ref}:{name}"], text=True)


def method(code, name):
    node = next(n for n in ast.walk(ast.parse(code)) if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(code, node)


def check():
    for name in ("embedder", "embedding", "faiss_index", "index_name", "retrieval"):
        path = f"retrieval_utils/{name}.py"
        assert (SCOUT / path).read_text() == source(LUNA / "utils", "945fde3b", path), path
    path = "catalyst/text_embedders/e5/embedder.py"
    assert (SCOUT / "scout/catalyst" / path).read_text() == source(LUNA / "luna/catalyst", "97ccb129", path)
    for p in (SCOUT / "nemo").rglob("*.py"):
        if p.name == "__init__.py":
            continue
        original = source(NEMO, "825f5d64", p.relative_to(SCOUT))
        if p.name == "predictor.py":
            for name in ("__init__", "search"):
                assert method(p.read_text(), name) == method(original, name), name
        else:
            assert p.read_text() == original, p
    path = "quality/classifier.py"
    assert method((SIGNAL / path).read_text(), "classify") == method((SEMANTICA / path).read_text(), "classify")
    for name in ("custom_exceptions", "error_code", "log_messages", "predictor_logger", "logger_metadata"):
        path = f"common_tools/{name}.py"
        assert (SIGNAL / path).read_text() == (SEMANTICA / path).read_text().replace("confluence.", "faro_signal."), path
    print("Matched Luna retrieval and E5, Nemo search, Semantica classifier and common tools.")


if __name__ == "__main__":
    check()
