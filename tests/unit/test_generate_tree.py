import runpy
import os


def test_generate_tree_runs(tmp_path, monkeypatch):
    """Ejecuta el script de generación de estructura y verifica que no falle."""
    # Ejecutar desde la raíz del repo para que las rutas relativas funcionen
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    monkeypatch.chdir(repo_root)

    # Ejecutar el script como si fuera __main__
    runpy.run_path("scripts/generate_tree.py", run_name="__main__")

    # Comprobar que el fichero docs/estructura.md fue creado/actualizado
    docs_file = os.path.join(repo_root, "docs", "estructura.md")
    assert os.path.exists(docs_file)
