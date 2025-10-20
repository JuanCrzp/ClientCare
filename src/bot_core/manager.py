from typing import Dict, Any
from pathlib import Path
from ..app.config import settings
from ..storage.state_repository import StateRepository
from ..config.rules_loader import get_rules_for
from ..handlers.faq import answer_faq
from ..handlers.ticket import open_ticket
from ..handlers.escalation import escalation_message
from ..handlers.greeting import build_greeting
from ..utils.rate_limiter import SimpleRateLimiter
from ..nlu.classifier import SimpleNLU
_limiter = SimpleRateLimiter()
_state = StateRepository(Path(settings.data_dir))

class BotManager:
    def process_message(self, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        text_raw = payload.get("text") or ""
        text = text_raw.lower()
        user_id = payload.get("platform_user_id") or ""
        chat_id = payload.get("group_id") or None
        rules = get_rules_for(chat_id)
        synonyms = rules.get("synonyms", {}) or {}
        menus_cfg = (rules.get("menus") or {})

        def enabled(feature: str) -> bool:
            return bool(((rules.get("features", {}) or {}).get(feature, {}) or {}).get("enabled", True))

        def matches_any(words: list[str] | None) -> bool:
            words = words or []
            return any(w for w in words if isinstance(w, str) and w.lower() in text)

        # Rate limit por usuario (opcional desde rules)
        rl_cfg = (rules.get("rate_limit") or {})
        try:
            per_min = int(rl_cfg.get("per_user_per_minute") or 0)
        except Exception:
            per_min = 0
        if per_min > 0:
            if not _limiter.allow(user_id, per_min):
                msg = rl_cfg.get("message") or "Demasiados mensajes, intenta en un minuto."
                return {"text": msg}

        # Manejo de estado de conversación (menús dinámicos/submenús y pasos)
        state = _state.get(user_id, chat_id)
        state_name = (state.get("name") or "").lower()
        state_data = state.get("data") or {}

        # Estados soportados:
        # - "menu:dyn": menús definidos en rules.menus (dinámicos)
        # - "menu:main": menú estático clásico (retrocompatibilidad)
        # - "menu:faq": submenú de FAQ
        # - "ticket:ask_detail": esperando detalle para crear ticket

        nlu_cfg = rules.get("nlu") or {}

        def has_dynamic_menus() -> bool:
            items = (menus_cfg.get("items") or {})
            return len(items.keys()) > 0

        def menu_root_id() -> str:
            return (menus_cfg.get("root") or "main")

        def menu_item(menu_id: str) -> dict:
            # Obtiene un menú por id. Si el menú tiene enabled: false, se considera oculto.
            mi = (menus_cfg.get("items") or {}).get(menu_id or "", {}) or {}
            if mi and mi.get("enabled", True) is False:
                return {}
            return mi

        def menu_text(menu_id: str) -> str:
            mi = menu_item(menu_id)
            return (mi.get("text") or rules.get("menu_text") or "Escribe tu consulta.")

        def menu_options(menu_id: str) -> list[dict]:
            # Devuelve sólo opciones activas (enabled true o ausente)
            mi = menu_item(menu_id)
            opts = [o for o in (mi.get("options") or []) if o.get("enabled", True) is not False]
            return opts

        # Detecta saludos según rules.nlu.greetings.triggers
        def is_greeting() -> bool:
            t = (text or "").strip().lower()
            if not (nlu_cfg.get("greetings", {}).get("enabled", True)):
                return False
            trig = [str(x).lower() for x in (nlu_cfg.get("greetings", {}).get("triggers") or [])]
            return t in trig

        # Flujo cuando estamos esperando detalle del ticket
        if state_name == "ticket:ask_detail":
            # Si el usuario repite un trigger de ticket ("ticket", "abrir ticket", etc.),
            # pedimos nuevamente el detalle para evitar crear tickets vacíos o pobres.
            def is_ticket_trigger_again() -> bool:
                if matches_any((rules.get("synonyms", {}) or {}).get("ticket")):
                    return True
                # Revisar intents con action ticket_ask_detail
                intents_local = list((nlu_cfg.get("intents") or []))
                t = text.strip().lower()
                for intent in intents_local:
                    if (intent.get("action") or "").lower() == "ticket_ask_detail":
                        patterns = [str(x).lower() for x in (intent.get("patterns") or [])]
                        if any(p and p in t for p in patterns):
                            return True
                return False

            if is_ticket_trigger_again():
                ask = (rules.get("tickets", {}).get("message_ask_detail")
                       or "Por favor, cuéntame brevemente el problema.")
                return {"text": ask}

            # Crea ticket con el texto actual como detalle
            if enabled("tickets"):
                _state.clear(user_id, chat_id)
                return {"text": open_ticket(user_id, text_raw, chat_id)}
            else:
                _state.clear(user_id, chat_id)
                return {"text": rules.get("fallback_text", "No entendí tu mensaje.")}
        if text == "/start" or matches_any(synonyms.get("menu")) or is_greeting():
            if has_dynamic_menus():
                cur = menu_root_id()
                _state.set(user_id, chat_id, "menu:dyn", {"current": cur, "stack": []})
                # Mostrar saludo configurable si está activo, seguido del menú
                greet = build_greeting(user_id, chat_id)
                if greet:
                    return {"text": f"{greet}\n\n{menu_text(cur)}"}
                return {"text": menu_text(cur)}
            else:
                _state.set(user_id, chat_id, "menu:main")
                greet = build_greeting(user_id, chat_id)
                if greet:
                    return {"text": f"{greet}\n\n{rules.get('menu_text', 'Escribe tu consulta.')}"}
                return {"text": rules.get("menu_text", "Escribe tu consulta.")}

        # Atajos globales del menú raíz: si aún no hay estado de menú pero existen menús dinámicos,
        # interpreta la opción contra el root (por ejemplo, "1", "2", "ticket", etc.)
        if has_dynamic_menus() and state_name not in {"menu:dyn", "menu:main", "menu:faq", "ticket:ask_detail"}:
            current = menu_root_id()
            t = (text or "").strip().lower()

            def triggers_match_any(options: list[dict]) -> dict | None:
                for opt in options:
                    for w in (opt.get("triggers") or []):
                        if isinstance(w, str) and (t == w.lower() or w.lower() in t):
                            return opt
                return None

            opt = triggers_match_any(menu_options(current))
            if opt:
                action = (opt.get("action") or "").lower()
                if action == "goto":
                    target = opt.get("target") or ""
                    if target and menu_item(target):
                        _state.set(user_id, chat_id, "menu:dyn", {"current": target, "stack": [current]})
                        return {"text": menu_text(target)}
                if action == "ticket_ask_detail" and enabled("tickets"):
                    _state.set(user_id, chat_id, "ticket:ask_detail")
                    ask = (rules.get("tickets", {}).get("message_ask_detail")
                           or "Por favor, cuéntame brevemente el problema.")
                    return {"text": ask}
                if action == "escalation" and enabled("escalation"):
                    _state.clear(user_id, chat_id)
                    return {"text": escalation_message()}
                if action == "reply":
                    reply = opt.get("reply_text") or rules.get("fallback_text", "No entendí tu mensaje.")
                    _state.set(user_id, chat_id, "menu:dyn", {"current": current, "stack": []})
                    return {"text": reply}

        # Si estamos en el menú dinámico
        if state_name == "menu:dyn" and has_dynamic_menus():
            current = state_data.get("current") or menu_root_id()
            stack = list(state_data.get("stack") or [])

            def triggers_match(trigs: list[str] | None) -> bool:
                trigs = trigs or []
                t = text.strip().lower()
                return any((isinstance(w, str) and (t == w.lower() or w.lower() in t)) for w in trigs)

            matched = None
            for opt in menu_options(current):
                if triggers_match(opt.get("triggers")):
                    matched = opt
                    break

            if matched:
                action = (matched.get("action") or "").lower()
                if action == "goto":
                    target = matched.get("target") or ""
                    if target and menu_item(target):
                        stack.append(current)
                        _state.set(user_id, chat_id, "menu:dyn", {"current": target, "stack": stack})
                        return {"text": menu_text(target)}
                    return {"text": rules.get("fallback_text", "No entendí tu mensaje.")}
                if action == "back":
                    if stack:
                        prev = stack.pop()
                        _state.set(user_id, chat_id, "menu:dyn", {"current": prev, "stack": stack})
                        return {"text": menu_text(prev)}
                    # volver al root si no hay stack
                    root = menu_root_id()
                    _state.set(user_id, chat_id, "menu:dyn", {"current": root, "stack": []})
                    return {"text": menu_text(root)}
                if action == "faq_mode":
                    # Entramos en modo FAQ; guardamos retorno
                    _state.set(user_id, chat_id, "menu:faq", {"return_menu": {"current": current, "stack": stack}})
                    faq_menu = (
                        (rules.get("faq_menu_text") or "Submenú FAQ:\n- Escribe una palabra clave, p.ej. 'precios', 'planes'\n- Escribe 'menu' para volver")
                    )
                    return {"text": faq_menu}
                if action == "ticket_ask_detail":
                    if enabled("tickets"):
                        _state.set(user_id, chat_id, "ticket:ask_detail")
                        ask = (rules.get("tickets", {}).get("message_ask_detail")
                               or "Por favor, cuéntame brevemente el problema.")
                        return {"text": ask}
                if action == "escalation":
                    if enabled("escalation"):
                        _state.clear(user_id, chat_id)
                        return {"text": escalation_message()}
                if action == "reply":
                    reply = matched.get("reply_text") or rules.get("fallback_text", "No entendí tu mensaje.")
                    # permanecemos en el mismo menú
                    _state.set(user_id, chat_id, "menu:dyn", {"current": current, "stack": stack})
                    return {"text": reply}

            # Sin coincidencias: re-mostrar el menú actual
            return {"text": menu_text(current)}

        # Si estamos en el menú principal estático y el usuario elige una opción
        if state_name == "menu:main":
            # Opción FAQ
            if matches_any(synonyms.get("faq")):
                _state.set(user_id, chat_id, "menu:faq")
                faq_menu = (
                    (rules.get("faq_menu_text") or "Submenú FAQ:\n- Escribe una palabra clave, p.ej. 'precios', 'planes'\n- Escribe 'menu' para volver")
                )
                return {"text": faq_menu}
            # Opción Ticket
            if enabled("tickets") and matches_any(synonyms.get("ticket")):
                _state.set(user_id, chat_id, "ticket:ask_detail")
                ask = (rules.get("tickets", {}).get("message_ask_detail")
                       or "Por favor, cuéntame brevemente el problema.")
                return {"text": ask}
            # Opción Agente
            if enabled("escalation") and matches_any(synonyms.get("agent")):
                _state.clear(user_id, chat_id)
                return {"text": escalation_message()}
            # Si escribe otra cosa estando en menú, mostramos el menú para guiar
            menu_txt = rules.get("menu_text", "Escribe tu consulta.")
            return {"text": menu_txt}

        # Si estamos en FAQ y el usuario pide volver al menú
        if state_name == "menu:faq":
            back_triggers = ["menu", "volver", "back", "9"]
            t = text.strip().lower()
            if t in back_triggers or matches_any(synonyms.get("menu")):
                # Si venimos de un menú dinámico, restauramos ese menú
                ret = (state_data.get("return_menu") or {})
                if ret:
                    _state.set(user_id, chat_id, "menu:dyn", {"current": ret.get("current"), "stack": ret.get("stack") or []})
                    return {"text": menu_text(ret.get("current") or menu_root_id())}
                # Si no, volvemos al menú estático
                _state.set(user_id, chat_id, "menu:main")
                return {"text": rules.get("menu_text", "Escribe tu consulta.")}

        # NLU configurable: intenta clasificar intenciones antes del FAQ
        # NLU avanzado: clasificar con fuzzy matching y umbral
        nlu = SimpleNLU(nlu_cfg)
        best, score = nlu.classify(text)
        if best and score >= nlu.threshold:
            action = best.action
            intent = best.intent_cfg
            if action == "goto":
                target = intent.get("target") or ""
                if target and has_dynamic_menus() and menu_item(target):
                    _state.set(user_id, chat_id, "menu:dyn", {"current": target, "stack": [menu_root_id()]})
                    return {"text": menu_text(target)}
            if action == "ticket_ask_detail" and enabled("tickets"):
                _state.set(user_id, chat_id, "ticket:ask_detail")
                ask = (rules.get("tickets", {}).get("message_ask_detail")
                       or "Por favor, cuéntame brevemente el problema.")
                return {"text": ask}
            if action == "escalation" and enabled("escalation"):
                _state.clear(user_id, chat_id)
                return {"text": escalation_message()}
            if action == "reply":
                reply = intent.get("reply_text") or rules.get("fallback_text", "No entendí tu mensaje.")
                return {"text": reply}
        elif (nlu_cfg.get("intents") or []) and score > 0:
            # Hubo una intención cercana, pero por debajo del umbral
            low_msg = nlu_cfg.get("low_confidence_message") or (
                "Puedo ayudarte con: menú, tickets o un agente. ¿Qué prefieres?"
            )
            return {"text": low_msg}

        # FAQ basado en rules
        if enabled("faq"):
            faq_ans = answer_faq(text)
            if faq_ans:
                # Si estábamos en submenú FAQ, mantenemos el estado para permitir más consultas
                if state_name == "menu:faq":
                    return {"text": faq_ans}
                return {"text": faq_ans}

        # Apertura de ticket con palabras clave
        if enabled("tickets") and (text == "/ticket" or matches_any(synonyms.get("ticket"))):
            # Si el usuario está fuera del menú, pedimos detalle primero para ticket guiado
            _state.set(user_id, chat_id, "ticket:ask_detail")
            ask = (rules.get("tickets", {}).get("message_ask_detail")
                   or "Por favor, cuéntame brevemente el problema.")
            return {"text": ask}

        # Escalamiento a agente
        if enabled("escalation") and matches_any(synonyms.get("agent")):
            _state.clear(user_id, chat_id)
            return {"text": escalation_message()}

    # Fallback
        return {"text": rules.get("fallback_text", "No entendí tu mensaje.")}
