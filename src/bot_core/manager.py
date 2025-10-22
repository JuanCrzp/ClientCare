from typing import Dict, Any
from pathlib import Path
from ..app.config import settings
from ..storage.state_repository import StateRepository
from ..storage.conversation_repository import ConversationRepository
from ..config.rules_loader import get_rules_for
from ..handlers.faq import answer_faq
from ..handlers.ticket import open_ticket
from ..handlers.escalation import escalation_message
from ..handlers.greeting import build_greeting
from ..nlu.classifier import SimpleNLU, MLNLU

_state = StateRepository(Path(settings.data_dir))
_conv = ConversationRepository(Path(settings.data_dir))


class BotManager:
    def process_message(self, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        # 1) Entrada y configuración
        text_raw = str(payload.get("text") or "")
        text = text_raw.lower()
        user_id = str(payload.get("platform_user_id") or "")
        chat_id = payload.get("group_id") or None

        rules = get_rules_for(chat_id)
        nlu_cfg = dict(rules.get("nlu") or {})
        synonyms = dict(rules.get("synonyms") or {})
        menus_cfg = dict(rules.get("menus") or {})

        memory_cfg = dict(rules.get("memory") or {})
        history_max = int(memory_cfg.get("history_max") or 100)
        # Funcionalidad de memoria básica
        resume_after = int(memory_cfg.get("resume_after_minutes") or 60)
        offer_resume_msg = memory_cfg.get("offer_resume_message") or "Veo que tenías pendiente: {topic}. ¿Quieres continuar?"
        
        # Comando /historial - prioritario
        if text.strip() == "/historial":
            hist = _conv.get_history(user_id, chat_id, limit=10)
            if hist:
                lines = []
                for h in hist[-10:]:  # Últimos 10 mensajes
                    role = h.get("role", "")
                    txt = h.get("text", "")[:50]
                    lines.append(f"[{role}] {txt}")
                return {"text": "Historial reciente:\n" + "\n".join(lines)}
            return {"text": "No tienes historial aún."}

        # Registrar mensaje del usuario en historial (best-effort)
        _conv.append_event(user_id, chat_id, role="user", text=text_raw, meta={}, max_items=history_max)
        
        # Ofrecer retomar tema abierto si aplica - ANTES de otros checks
        topic = _conv.get_topic(user_id, chat_id)
        last_hist = _conv.get_history(user_id, chat_id, limit=2)  # Necesitamos al menos 2: el que acabamos de agregar y el anterior
        if topic and len(last_hist) >= 2:
            # Si el usuario vuelve tras X minutos y hay tema abierto, ofrecer continuar
            prev_ts = last_hist[-2]["ts"]  # El mensaje anterior al actual
            import time
            if time.time() - prev_ts > resume_after * 60:
                return {"text": offer_resume_msg.replace("{topic}", topic.get("name") or "tema pendiente")}

        # Helpers de features y menús
        def enabled(feature: str) -> bool:
            features = dict(rules.get("features") or {})
            return bool((features.get(feature) or {}).get("enabled", True))

        def matches_any(words: list[str] | None) -> bool:
            words = words or []
            return any(isinstance(w, str) and w.lower() in text for w in words)

        def has_dynamic_menus() -> bool:
            return bool((menus_cfg.get("items") or {}))

        def menu_root_id() -> str:
            return str(menus_cfg.get("root") or "main")

        def menu_item(mid: str) -> dict | None:
            items = dict(menus_cfg.get("items") or {})
            item = items.get(mid)
            if not item:
                return None
            if item.get("enabled") is False:
                return None
            return item

        def menu_options(mid: str) -> list[dict]:
            it = menu_item(mid) or {}
            opts = list(it.get("options") or [])
            return [o for o in opts if o.get("enabled", True) is not False]

        def menu_text(mid: str) -> str:
            it = menu_item(mid) or {}
            return str(it.get("text") or rules.get("menu_text") or "Escribe tu consulta.")

        # 2) Estado actual
        st = _state.get(user_id, chat_id)
        state_name = st.get("name") or ""
        state_data = st.get("data") or {}

        # 3) Flujo: completar ticket si está pidiendo detalle
        if state_name == "ticket:ask_detail":
            detail = text_raw.strip()
            if detail:
                msg = open_ticket(user_id, detail, chat_id)
                _state.clear(user_id, chat_id)
                _conv.append_event(user_id, chat_id, role="bot", text="[Ticket creado]", meta={"state": "ticket_created"}, max_items=history_max)
                return {"text": msg}
            # Si no hay detalle, re-preguntar
            ask = (rules.get("tickets", {}).get("message_ask_detail") or "Por favor, cuéntame brevemente el problema.")
            return {"text": ask}

        # 4) Comando /start o ir al menú (solo si no hay memoria que mostrar)
        greetings_triggers = list((nlu_cfg.get("greetings") or {}).get("triggers") or [])
        is_greeting_trigger = text in [t.lower() for t in greetings_triggers] or matches_any(synonyms.get("menu")) or text.strip() == "/start"
        
        # Solo procesar como saludo si es /start explícito
        if is_greeting_trigger and text.strip() == "/start":
            if has_dynamic_menus():
                cur = menu_root_id()
                _state.set(user_id, chat_id, "menu:dyn", {"current": cur, "stack": []})
                greet = build_greeting(user_id, chat_id)
                if greet:
                    return {"text": f"{greet}\n\n{menu_text(cur)}"}
                return {"text": menu_text(cur)}
            else:
                _state.set(user_id, chat_id, "menu:main")
                greet = build_greeting(user_id, chat_id)
                if greet:
                    return {"text": f"{greet}\n\n{rules.get('menu_text', 'Escribe tu consulta.') }"}
                return {"text": rules.get('menu_text', 'Escribe tu consulta.')}

        # 5) Menú dinámico: evaluar opción en el menú actual
        if state_name == "menu:dyn" and has_dynamic_menus():
            current = state_data.get("current") or menu_root_id()
            stack = list(state_data.get("stack") or [])
            tnorm = text.strip().lower()

            def triggers_match(trigs: list[str] | None) -> bool:
                trigs = trigs or []
                return any((isinstance(w, str) and (tnorm == w.lower() or w.lower() in tnorm)) for w in trigs)

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
                if action == "back":
                    if stack:
                        prev = stack.pop()
                        _state.set(user_id, chat_id, "menu:dyn", {"current": prev, "stack": stack})
                        return {"text": menu_text(prev)}
                    root = menu_root_id()
                    _state.set(user_id, chat_id, "menu:dyn", {"current": root, "stack": []})
                    return {"text": menu_text(root)}
                if action == "ticket_ask_detail" and enabled("tickets"):
                    _state.set(user_id, chat_id, "ticket:ask_detail")
                    ask = (rules.get("tickets", {}).get("message_ask_detail") or "Por favor, cuéntame brevemente el problema.")
                    return {"text": ask}
                if action == "escalation" and enabled("escalation"):
                    _state.clear(user_id, chat_id)
                    return {"text": escalation_message()}
                if action == "reply":
                    reply = matched.get("reply_text") or rules.get("fallback_text", "No entendí tu mensaje.")
                    _state.set(user_id, chat_id, "menu:dyn", {"current": current, "stack": stack})
                    return {"text": reply}
            # Si no se encontró opción, continuar con NLU/FAQ/fallback global
            pass

        # 6) Menú estático (fallback legacy)
        if state_name == "menu:main":
            if matches_any(synonyms.get("faq")):
                # En configuración dinámica, FAQ es un submenú; aquí devolvemos guía
                return {"text": "Submenú FAQ:\n- Escribe una palabra clave, p.ej. 'precios', 'planes'\n- Escribe 'menu' para volver"}
            if enabled("tickets") and matches_any(synonyms.get("ticket")):
                _state.set(user_id, chat_id, "ticket:ask_detail")
                ask = (rules.get("tickets", {}).get("message_ask_detail") or "Por favor, cuéntame brevemente el problema.")
                return {"text": ask}
            if enabled("escalation") and matches_any(synonyms.get("agent")):
                _state.clear(user_id, chat_id)
                return {"text": escalation_message()}
            return {"text": rules.get("menu_text", "Escribe tu consulta.")}

        # 7) NLU configurable (simple o ML)
        provider = str((nlu_cfg.get("provider") or "simple")).lower()
        if provider == "ml":
            nlu = MLNLU(nlu_cfg, data_dir=settings.data_dir)
        else:
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
                ask = (rules.get("tickets", {}).get("message_ask_detail") or "Por favor, cuéntame brevemente el problema.")
                return {"text": ask}
            if action == "escalation" and enabled("escalation"):
                _state.clear(user_id, chat_id)
                return {"text": escalation_message()}
            if action == "reply":
                reply = intent.get("reply_text") or rules.get("fallback_text", "No entendí tu mensaje.")
                return {"text": reply}
        elif (nlu_cfg.get("intents") or []) and score > 0:
            low_msg = nlu_cfg.get("low_confidence_message") or ("Para ayudarte mejor puedo: mostrar el menú, crear un ticket o derivarte a un agente. ¿Qué prefieres?")
            return {"text": low_msg}

        # 8) FAQ directo por palabra clave
        if enabled("faq"):
            ans = answer_faq(text_raw)
            if ans:
                return {"text": ans}

        # 9) Atajos por sinónimos (tickets / agente)
        if enabled("tickets") and (text == "/ticket" or matches_any(synonyms.get("ticket"))):
            _state.set(user_id, chat_id, "ticket:ask_detail")
            ask = (rules.get("tickets", {}).get("message_ask_detail") or "Por favor, cuéntame brevemente el problema.")
            return {"text": ask}

        if enabled("escalation") and matches_any(synonyms.get("agent")):
            _state.clear(user_id, chat_id)
            return {"text": escalation_message()}

        # 10) Fallback
        return {"text": rules.get("fallback_text", "No entendí tu mensaje.")}
