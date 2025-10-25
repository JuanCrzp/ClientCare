from pathlib import Path
import sys
import json

# mypy: ignore-errors

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def main() -> None:
    # Ensure local imports work
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))

    from src.config.rules_loader import get_rules_for  # type: ignore
    from src.nlu.classifier import MLNLU  # type: ignore
    from src.app.config import settings  # type: ignore

    rules = get_rules_for(None)
    nlu_cfg = rules.get("nlu") or {}
    # Forzamos reentrenamiento
    nlu_cfg = {**nlu_cfg, "ml": {**(nlu_cfg.get("ml") or {}), "retrain_on_start": True}}
    model = MLNLU(nlu_cfg, data_dir=settings.data_dir)
    print("Modelo NLU entrenado y guardado en:", Path(model.model_path).resolve())
    intents = [i.get("name") for i in (nlu_cfg.get("intents") or [])]
    print("Intents:", ", ".join(intents))

    # Guardar reporte JSON
    report_path = Path(settings.data_dir) / "models" / "nlu_report.json"
    meta = getattr(model, "_model", {}).get("meta", {}) if getattr(model, "_model", None) else {}
    report = {
        "model_path": str(Path(model.model_path).resolve()),
        "intents": intents,
        "meta": meta,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("Reporte del modelo:", report_path.resolve())


if __name__ == "__main__":
    main()
