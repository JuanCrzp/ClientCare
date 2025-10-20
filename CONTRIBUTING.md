# Guía de Contribución

¡Gracias por tu interés en contribuir! Este proyecto ClientCare es independiente y vive en esta carpeta como un repositorio autónomo.

Autor principal: Juan Camilo Cruz P (github: JuanCrzp)

## Requisitos
- Python 3.10+
- pip y git
- Opcional: pre-commit (para hooks locales)

## Configuración del entorno
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # opcional, si usas pyproject
```

## Ejecutar pruebas
```bash
pytest -q
```

## Hooks pre-commit (opcional, recomendado)
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Flujo de trabajo
1. Crea un fork y una rama: `feature/nombre-corto` o `fix/bug-descriptivo`
2. Asegura que `pytest` pasa y que no hay errores en pre-commit
3. Describe claramente el cambio en el PR (motivo, alcance, pruebas)
4. Los PRs deben mantener compatibilidad y actualizar docs si aplica

## Estilo de código
- PEP 8 y tipado cuando sea posible
- Funciones pequeñas, nombres descriptivos, logs útiles
- No subas secretos ni `.env`

## Reportes y soporte
- Bugs y mejoras: Issues
- Seguridad: ver `SECURITY.md`
