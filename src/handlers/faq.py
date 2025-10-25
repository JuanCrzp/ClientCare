import re
from difflib import SequenceMatcher
from ..config.rules_loader import get_rules


def build_auto_capabilities(rules: dict, max_examples: int = 3) -> str:
    """Genera una respuesta profesional según features activas en la config.

    - Lista de capacidades en tono formal (usted).
    - Añade 2-3 ejemplos de preguntas frecuentes tomadas de `rules['faq']`,
      excluyendo la propia entrada que usa "{auto}" para evitar recursión.
    """
    frases = []
    # Usar un tono formal y acciones claras
    if rules.get("catalog", {}).get("enabled", False):
        frases.append("mostrarle nuestro catálogo")
    if rules.get("menus", {}).get("enabled", False):
        frases.append("guiarle mediante un menú interactivo")
    if rules.get("features", {}).get("tickets", {}).get("enabled", False):
        frases.append("abrir y gestionar tickets de soporte")
    if rules.get("features", {}).get("faq", {}).get("enabled", False):
        frases.append("responder preguntas frecuentes sobre la empresa y servicios")
    if rules.get("features", {}).get("escalation", {}).get("enabled", False):
        frases.append("derivarlo a un asesor humano cuando sea necesario")

    if not frases:
        base = "Actualmente no tengo funciones activas configuradas."
        return base

    # Construir la primera frase profesional
    if len(frases) == 1:
        primera = f"Puedo {frases[0].strip()}."
    else:
        primera = "Puedo " + ", ".join([f.strip() for f in frases[:-1]]) + " y " + frases[-1] + "."

    # Tomar ejemplos del FAQ (excluir la entrada que contiene '{auto}')
    ejemplos = []
    faq_list = rules.get("faq") or []
    for item in faq_list:
        if not isinstance(item, dict):
            continue
        q = (item.get("q") or "").strip()
        a = item.get("a") or ""
        # evitar la pregunta que se auto-resuelve para no incluirla como ejemplo
        if "{auto}" in str(a):
            continue
        if q:
            ejemplos.append(q)
        if len(ejemplos) >= max_examples:
            break

    segunda = ""
    if ejemplos:
        # Formatear ejemplos: "horario", "catálogo" y "envíos".
        if len(ejemplos) == 1:
            lista_ej = f'"{ejemplos[0]}"'
        elif len(ejemplos) == 2:
            lista_ej = f'"{ejemplos[0]}" y "{ejemplos[1]}"'
        else:
            lista_ej = ", ".join([f'"{e}"' for e in ejemplos[:-1]]) + f" y \"{ejemplos[-1]}\""

        segunda = (
            f"También puedo responder preguntas frecuentes como: {lista_ej}. "
            "Si lo desea, escriba cualquiera de ellas y con gusto le atiendo."
        )

    return (primera + (" " + segunda if segunda else "")).strip()


def _normalize(s: str) -> str:
    # Lowercase, remove punctuation (keep spaces), collapse whitespace, quita signos de interrogación/exclamación
    s = (s or "").lower()
    s = re.sub(r"[¿?¡!.,;:\-]", " ", s)  # quita signos comunes
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def answer_faq(text: str, threshold: float = 0.75) -> str | None:
    """Respuesta flexible para FAQs con keywords y normalización avanzada.
    Solo responde si la similitud supera el umbral (por defecto 0.75).
    """
    all_rules = get_rules() or {}
    rules = (all_rules.get("default") or {})
    faq = rules.get("faq", []) or []
    # synonyms_list = (rules.get("synonyms") or {}).get("faq") or []

    t = _normalize(text)
    if not t:
        return None
    # Ignorar inputs muy cortos (e.g., 'no', 'ok') para evitar coincidencias erróneas
    if len(t) <= 2:
        return None
    t_tokens = set(t.split())

    # Leer umbral desde la configuración si está definido en rules.yaml
    try:
        cfg_threshold = (
            rules.get("features", {})
            .get("faq", {})
            .get("match_threshold")
        )
        if isinstance(cfg_threshold, (int, float)):
            threshold = float(cfg_threshold)
    except Exception:
        # Si algo falla, usamos el valor por parámetro (por defecto 0.75)
        pass

    best_score = 0.0
    best_answer = None

    for item in faq:
        q = (item.get("q") or "")
        qn = _normalize(q)
        keywords = [qn]
        if "keywords" in item and isinstance(item["keywords"], list):
            keywords += [_normalize(k) for k in item["keywords"] if isinstance(k, str)]

        for kw in keywords:
            # 1) Exact match / inclusion (evitar usar 't in kw' que provoca falsos positivos: 'no' in 'novedades')
            if kw == t or kw in t:
                ans = item.get("a") or None
                if ans and "{auto}" in ans:
                    ans = ans.replace("{auto}", build_auto_capabilities(rules))
                return ans
            # 2) Fuzzy similarity
            try:
                ratio = SequenceMatcher(None, kw, t).ratio()
                if ratio > best_score:
                    best_score = ratio
                    best_answer = item.get("a")
            except Exception:
                pass
            # 3) Token overlap
            kw_tokens = set(kw.split())
            overlap = 0
            for ktk in kw_tokens:
                for ttk in t_tokens:
                    if ktk == ttk or ktk in ttk or ttk in ktk:
                        overlap += 1
                        break
            score = overlap / max(1, len(kw_tokens))
            if score > best_score:
                best_score = score
                best_answer = item.get("a")

    # Solo responde si la mejor coincidencia supera el umbral
    if best_score >= threshold and best_answer:
        ans = best_answer
        if ans and "{auto}" in ans:
            ans = ans.replace("{auto}", build_auto_capabilities(rules))
        return ans
    return None
