from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_FILE = ROOT / "docs" / "estructura.md"

EXCLUDES = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def tree(dir_path: Path, prefix: str = "") -> str:
    entries = sorted([e for e in dir_path.iterdir() if e.name not in EXCLUDES], key=lambda p: (p.is_file(), p.name.lower()))
    lines = []
    for idx, entry in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        lines.append(prefix + connector + entry.name)
        if entry.is_dir():
            extension = "    " if idx == len(entries) - 1 else "│   "
            lines.extend(tree(entry, prefix + extension).splitlines())
    return "\n".join(lines)


def generate_markdown() -> str:
    header = "# Estructura de Carpetas de ClientCare\n\nSe actualiza automáticamente vía pre-commit. No editar manualmente.\n\n"
    code_open = "```\n(clientcare)\n"
    code_close = "\n```\n"
    content = tree(ROOT)
    return header + code_open + content + code_close


if __name__ == "__main__":
    DOCS_FILE.parent.mkdir(parents=True, exist_ok=True)
    md = generate_markdown()
    DOCS_FILE.write_text(md, encoding="utf-8")
    print(f"Actualizada {DOCS_FILE}")
