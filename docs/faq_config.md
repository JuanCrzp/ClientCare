## Configuración y comportamiento del FAQ dinámico ({auto})

Este documento explica en detalle los cambios implementados en el módulo FAQ del bot, cómo funciona la plantilla `{auto}`, qué opciones nuevas hay en `config/rules.yaml`, y cómo probar y ajustar la detección de preguntas.

### Resumen de cambios

- Se implementó una respuesta automática profesional para la pregunta "¿Qué puedes hacer?" usando la plantilla `{auto}` en el bloque `faq`.
- `build_auto_capabilities(rules)` genera una respuesta formal que lista capacidades activas (catálogo, menús, tickets, FAQ, escalación) y añade 2–3 ejemplos de preguntas frecuentes extraídas del bloque `faq` (excluye la entrada con `{auto}` para evitar recursión).
- `answer_faq(text, threshold)` ahora aplica un umbral de similitud configurable para decidir si un mensaje debe ser tratado como FAQ.
- Se mejoró la robustez evitando coincidencias peligrosas (ej. `t in kw`) y se ignoran mensajes muy cortos (<= 2 caracteres) para reducir falsos positivos.

### Archivos modificados / añadidos

- `src/handlers/faq.py` — lógica principal: `build_auto_capabilities` y `answer_faq`.
- `config/rules.yaml` — nueva clave `features.faq.match_threshold` (valor por defecto 0.75).
- `docs/faq_config.md` — este documento.
- `README.md` — referencia añadida a esta guía.

### Comportamiento detallado

1. Detección de FAQ

   - Cuando llega un mensaje, el handler normaliza el texto (minúsculas, remover signos, colapsar espacios) y genera tokens.
   - `answer_faq` busca coincidencias en cada entrada `faq` evaluando tres mecanismos:
     1) Coincidencia exacta o inclusión controlada (ahora `kw == t` o `kw in t`, se evitó `t in kw`).
     2) Similitud difusa (fuzzy) mediante `SequenceMatcher` (ratio).
     3) Solapamiento de tokens (token overlap).
   - La mejor puntuación entre estas estrategias se compara con `threshold` (por defecto 0.75). Solo si `best_score >= threshold` la entrada FAQ se considera válida y se devuelve su respuesta.
   - Si hay coincidencia exacta (caso 1), la respuesta se devuelve inmediatamente.

2. Umbral configurable

   - `config/rules.yaml` contiene ahora:

```yaml
features:
  faq:
    enabled: true
    not_found_message: "No encontré esa pregunta en el FAQ. ¿Quieres crear un ticket?"
    match_threshold: 0.75
```

   - `match_threshold` acepta valores entre 0.0 y 1.0. Recomendaciones:
     - 0.60–0.70: permisivo (más matches, más falsos positivos posibles).
     - 0.72–0.78: equilibrio recomendado (por defecto 0.75).
     - 0.80–0.90: estricto (solo coincidencias claras).

3. Respuestas automáticas `{auto}`

   - Si en una entrada FAQ la respuesta incluye `{auto}`, el bot sustituye esa plantilla por el resultado de `build_auto_capabilities(rules)`.
   - `build_auto_capabilities`:
     - Lista capacidades activas, con tono formal (usted): p.ej. "Puedo mostrarle nuestro catálogo, guiarle mediante un menú interactivo y abrir y gestionar tickets de soporte.".
     - Agrega 2–3 ejemplos de preguntas sacadas del bloque `faq` (usa `q`, no `keywords`) y evita las entradas que contienen `{auto}`.

4. Evitar falsos positivos y mensajes cortos

   - Para reducir matches accidentales se implementaron dos medidas:
     - No se evalúan entradas con longitud normalizada <= 2 caracteres (ej. "No", "OK"). Estas retornan `None` y permiten que el flujo de fallback o NLU tome el control.
     - Se quitó la comprobación `t in kw` porque provocaba que "no" coincidiera con "novedades".

### Cómo probar localmente

1. Ejecutar los tests unitarios relevantes:

```cmd
python -m pytest tests/unit/test_bot_capabilities.py -q
```

2. Probar en runtime (Windows):

```cmd
lanzar_bot.bat
# o si usas uvicorn directamente
uvicorn src.app.server:app --host 0.0.0.0 --port 8082 --reload
```

Enviar mensajes de prueba por WhatsApp/Webchat/Telegram y revisar logs.

3. Ejemplos de mensajes y comportamiento esperado:

- Usuario: "¿Qué puedes hacer?" → Respuesta con `build_auto_capabilities` (lista capacidades + ejemplos).
- Usuario: "No" → Si solo contiene "No" (len<=2), no será tratado como FAQ; pasará a fallback o NLU.
- Usuario: "¿Cuáles son las novedades?" → Si la similitud con la entrada "novedades" supera `match_threshold`, devuelve la respuesta FAQ.

### Recomendaciones de configuración

- Ajuste fino de `match_threshold` según canal: WhatsApp tiende a mensajes cortos; si ves falsos positivos, sube a 0.8.
- Para permitir respuestas cortas válidas (ej. "hora"), puedes:
  - Reducir el filtro de longitud a 3 (`len(t) <= 2` → `<= 1` o cambiar lógica), o
  - Añadir una lista blanca en `rules.yaml` con palabras cortas que deben evaluarse.

Ejemplo de whitelist en `rules.yaml` (opcional):

```yaml
default:
  faq_whitelist_short: ["hora", "precio", "envío"]
```

Y después ampliar la lógica en `answer_faq` para comprobar esa lista antes de ignorar inputs cortos.

### Troubleshooting y notas

- Si ves que mensajes simples siguen siendo respondidos incorrectamente: revisa `config/rules.yaml` y sube `match_threshold` o revisa las `keywords` que puedan ser demasiado genéricas.
- Si necesitas que diferentes chats usen distintos umbrales, usar overrides por `chat_id` en `config/rules.yaml` (estructura ya soportada por el loader).

### Próximos pasos sugeridos

- Documentar la whitelist short-words si el equipo lo necesita.
- Añadir un test unitario que valide que inputs cortos como "No" no son tratados como FAQ.
- Añadir una sección en la UI/Panel admin para ajustar `match_threshold` por canal.

---

Si quieres, puedo: añadir el test unitario mencionado, implementar la whitelist y/o añadir la opción de override por chat en la documentación y en el código.
