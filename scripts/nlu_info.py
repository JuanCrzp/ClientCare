import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))

from src.nlu.classifier import MLNLU
from src.config.rules_loader import get_rules_for
from src.app.config import settings


def main() -> None:
    rules = get_rules_for(None)
    nlu_cfg = rules.get("nlu") or {}
    model = MLNLU(nlu_cfg, data_dir=settings.data_dir)
    if not getattr(model, "_model", None):
        print("No hay modelo ML disponible. Entrena primero con scripts/train_nlu.py.")
        return
    meta = model._model.get("meta", {})
    labels = model._model.get("labels", [])
    vocab = model._model.get("vocab", {})
    print("\n=== NLU ML INFO ===")
    print("Ruta:", Path(model.model_path).resolve())
    print("Labels:", ", ".join(labels))
    print("Vocab size:", len(vocab))
    print("Meta:")
    for k in sorted(meta.keys()):
        print(f"  - {k}: {meta[k]}")

    # Opcional: escribir JSON
    out = Path(settings.data_dir) / "models" / "nlu_report.json"
    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"model_path": str(Path(model.model_path).resolve()), "intents": labels, "meta": meta}, f, ensure_ascii=False, indent=2)
        print("\nReporte escrito en:", out.resolve())
    except Exception as e:
        print("No se pudo escribir reporte:", e)


if __name__ == "__main__":
    main()
