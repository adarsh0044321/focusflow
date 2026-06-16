"""
FocusFlow Unified AI Engine
Routes queries to offline (llama.cpp) or online (OpenAI) backends
based on the current configuration mode.
"""

import logging
import time
from typing import Any, Optional

from offline_engine import OfflineEngine
from online_engine import OnlineEngine

logger = logging.getLogger("focusflow.ai_engine")

# ------------------------------------------------------------------
# System prompts
# ------------------------------------------------------------------

_PERSONAS = {
    "solver": (
        "You are an expert exam solver. Given a question (possibly from OCR "
        "with minor errors), solve it step-by-step.\n\n"
        "Rules:\n"
        "1. First, mentally repair any OCR errors in the question text.\n"
        "2. Solve the problem methodically.\n"
        "3. If options are provided, select the correct option.\n"
        "4. Give the final answer clearly as: \"Answer: [option/value]\""
    ),
    "tutor": (
        "You are an encouraging Socratic Tutor. Your goal is to help the user learn and understand "
        "the concepts behind their question rather than just feeding them the answer.\n\n"
        "Rules:\n"
        "1. Identify the core concept behind the question.\n"
        "2. Break it down and explain the methodology step-by-step.\n"
        "3. Ask clarifying questions or lead them to the answer logically.\n"
        "4. DO NOT explicitly state the final answer option. Guide them so they can pick it themselves."
    ),
    "code": (
        "You are a Senior Software Engineer and coding mentor. Answer technical and programming "
        "questions with robust explanations, syntax highlighting structures, and optimized code.\n\n"
        "Rules:\n"
        "1. Repair any typical OCR syntax corruptions in code blocks.\n"
        "2. Provide highly optimized, cleanly formatted code using standard Markdown blocks.\n"
        "3. Explain the time/space complexity and best practices."
    ),
    "lang": (
        "You are a Literature and Language Expert. Focus on providing rich translations, "
        "grammatical corrections, literary context, and linguistic breakdowns.\n\n"
        "Rules:\n"
        "1. Fix OCR spelling and text flow corruptions.\n"
        "2. Provide accurate translations and grammatical explanations.\n"
        "3. Offer stylistic context and word origins if relevant."
    )
}

_DETAIL_SUFFIX = "\n\nShow full working and explanation."

_CONCISE_SUFFIX = "\n\nBe brief. Give only the answer with minimal explanation."


class AIEngine:
    """Unified AI interface that routes to offline or online engines."""

    def __init__(self, config, knowledge_base=None, run_mode: str = "combined") -> None:
        self.config = config
        self.kb = knowledge_base
        self.run_mode = run_mode
        self.offline = OfflineEngine(config)
        self.online = OnlineEngine(config)
        self.logger = logger

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the offline engine if the current mode requires it."""
        if self.run_mode == "online":
            self.logger.info("[AIEngine] Online-only mode active: offline engine start bypassed")
            return
        
        # Resolve settings model setting
        model_setting = self.config.get("online_model")
        if model_setting in ("gpt-4o", "gpt-4o-mini") and self.run_mode != "offline":
            self.logger.info("[AIEngine] Online model selected: offline engine start bypassed")
            return
            
        self.logger.info("[AIEngine] Starting offline engine")
        self.offline.start()

    def stop(self) -> None:
        """Stop the offline engine process."""
        if self.run_mode == "online":
            return
        self.logger.info("[AIEngine] Stopping offline engine")
        self.offline.stop()

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        """Assemble the system prompt with verbosity and knowledge context."""
        persona_key = self.config.get("ai_persona", "solver")
        prompt = _PERSONAS.get(persona_key, _PERSONAS["solver"])

        verbosity = self.config.get("answer_mode") or "concise"
        if verbosity == "concise":
            prompt += _CONCISE_SUFFIX
        else:
            prompt += _DETAIL_SUFFIX

        return prompt

    def _get_knowledge_context(self, query: str) -> str:
        """Pull relevant context from the knowledge base, if available."""
        if self.kb is None or not query.strip():
            return ""
        try:
            context: str = self.kb.get_context(query)  # type: ignore[union-attr]
            if context and context.strip():
                # Limit KB context to 500 chars total to prevent prompt overflow
                kb_text = context.strip()
                if len(kb_text) > 500:
                    kb_text = kb_text[:500] + "..."
                return f"\nRelevant reference material:\n{kb_text}"
        except Exception as exc:
            self.logger.debug(f"[AIEngine] KB context fetch failed: {exc}")
        return ""

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _effective_mode(self) -> str:
        """Determine which engine to use right now.

        Modes:
        - ``offline``  → always offline
        - ``online``   → always online
        - ``hybrid``   → prefer offline if ready, else online fallback
        """
        if self.run_mode in ("online", "offline"):
            return self.run_mode

        model_setting = self.config.get("online_model")
        if model_setting == "offline":
            return "offline"
        elif model_setting == "combined":
            if self.offline.is_ready():
                return "offline"
            if self.online.is_ready():
                return "online"
            return "offline"  # fallback
        else: # e.g. gpt-4o, gpt-4o-mini
            return "online"
        return mode

    # ------------------------------------------------------------------
    # Solve (main entry point)
    # ------------------------------------------------------------------

    def solve(
        self,
        ocr_text: str,
        image: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Solve a question captured via OCR (and optionally its image).

        Returns a dict:
            ``{"answer": str, "duration": float, "mode": str, "engine": str}``
        """
        t0 = time.perf_counter()
        config_mode = self.config.get("mode") or "combined"
        if self.run_mode in ("online", "offline"):
            config_mode = self.run_mode
        system_prompt = self._build_system_prompt()
        knowledge_ctx = self._get_knowledge_context(ocr_text)
        mode = self._effective_mode()

        answer: str
        engine: str

        # Check if we are in combined mode and both engines are not ready
        if config_mode == "combined" and not self.offline.is_ready() and not self.online.is_ready():
            answer = "[No engines available] Combined mode: Offline engine (llama-server) is not ready, and no API keys are configured for Online mode."
            engine = "combined"
        else:
            try:
                if mode == "online":
                    answer, engine = self._solve_online(
                        ocr_text, image, system_prompt, knowledge_ctx,
                    )
                else:
                    answer, engine = self._solve_offline(
                        ocr_text, system_prompt, knowledge_ctx,
                    )
            except Exception as exc:
                self.logger.error(f"[AIEngine] Solve error: {exc}")
                answer = f"[Error] {exc}"
                engine = mode

        duration = round(time.perf_counter() - t0, 2)
        return {
            "answer": answer,
            "duration": duration,
            "mode": mode,
            "engine": engine,
        }

    def _solve_offline(
        self,
        text: str,
        system_prompt: str,
        knowledge_ctx: str,
    ) -> tuple[str, str]:
        """Route to the offline engine."""
        if not self.offline.is_ready():
            status = self.offline.status_message()
            return f"[Offline engine not ready] {status}", "offline"
        answer = self.offline.query(text, system_prompt, knowledge_ctx)
        return answer, "offline/llamacpp"

    def _solve_online(
        self,
        text: str,
        image: Optional[Any],
        system_prompt: str,
        knowledge_ctx: str,
    ) -> tuple[str, str]:
        """Route to the online engine, using vision when an image is available."""
        if not self.online.is_ready():
            return "[Online engine not ready] No API keys configured.", "online"

        full_system = system_prompt
        if knowledge_ctx.strip():
            full_system = f"{system_prompt}\n{knowledge_ctx}"

        if image is not None:
            answer = self.online.query_image(image, text, full_system)
        else:
            answer = self.online.query_text(text, full_system)

        return answer, f"online/{self.config.get('online_model', 'gpt-4o')}"

    # ------------------------------------------------------------------
    # Manual question (no OCR)
    # ------------------------------------------------------------------

    def solve_manual(self, question_text: str) -> dict[str, Any]:
        """Solve a manually typed question (no image, no OCR artefacts).

        The system prompt omits the OCR-repair instruction.
        """
        t0 = time.perf_counter()
        config_mode = self.config.get("mode") or "combined"
        if self.run_mode in ("online", "offline"):
            config_mode = self.run_mode
        knowledge_ctx = self._get_knowledge_context(question_text)
        mode = self._effective_mode()

        persona_key = self.config.get("ai_persona", "solver")
        system_prompt = _PERSONAS.get(persona_key, _PERSONAS["solver"])
        
        # Remove OCR references and re-index rules for manual text solver
        system_prompt = system_prompt.replace("Given a question (possibly from OCR with minor errors), ", "")
        import re
        lines = system_prompt.splitlines()
        cleaned_lines = []
        rule_counter = 1
        in_rules_section = False
        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("rules:"):
                in_rules_section = True
                cleaned_lines.append(line)
                continue
            if in_rules_section and re.match(r"^\d+\.\s", stripped):
                if "ocr" in stripped.lower():
                    continue
                rule_text = re.sub(r"^\d+\.\s*", "", stripped)
                leading_ws = line[:len(line) - len(line.lstrip())]
                cleaned_lines.append(f"{leading_ws}{rule_counter}. {rule_text}")
                rule_counter += 1
            else:
                cleaned_lines.append(line)
        system_prompt = "\n".join(cleaned_lines)

        verbosity = self.config.get("answer_mode") or "concise"
        if verbosity == "concise":
            system_prompt += _CONCISE_SUFFIX
        else:
            system_prompt += _DETAIL_SUFFIX

        answer: str
        engine: str

        # Check if we are in combined mode and both engines are not ready
        if config_mode == "combined" and not self.offline.is_ready() and not self.online.is_ready():
            answer = "[No engines available] Combined mode: Offline engine (llama-server) is not ready, and no API keys are configured for Online mode."
            engine = "combined"
        else:
            try:
                if mode == "online":
                    full_sys = system_prompt
                    if knowledge_ctx.strip():
                        full_sys = f"{system_prompt}\n{knowledge_ctx}"
                    answer = self.online.query_text(question_text, full_sys)
                    engine = f"online/{self.config.get('online_model', 'gpt-4o')}"
                else:
                    if not self.offline.is_ready():
                        status = self.offline.status_message()
                        answer = f"[Offline engine not ready] {status}"
                        engine = "offline"
                    else:
                        answer = self.offline.query(question_text, system_prompt, knowledge_ctx)
                        engine = "offline/llamacpp"
            except Exception as exc:
                self.logger.error(f"[AIEngine] Manual query solve failed on engine '{mode}': {exc}", exc_info=True)
                answer = f"[Error] {exc}"
                engine = mode

        duration = round(time.perf_counter() - t0, 2)
        return {
            "answer": answer,
            "duration": duration,
            "mode": mode,
            "engine": engine,
        }

    def solve_chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Process a multi-turn chat interaction."""
        t0 = time.perf_counter()
        system_prompt = self._build_system_prompt()
        mode = self._effective_mode()

        answer: str
        engine: str

        try:
            if mode == "online":
                answer = self.online.query_chat(messages, system_prompt)
                engine = f"online/{self.config.get('online_model', 'gpt-4o')}"
            else:
                if not self.offline.is_ready():
                    status = self.offline.status_message()
                    answer = f"[Offline engine not ready] {status}"
                    engine = "offline"
                else:
                    answer = self.offline.query_chat(messages, system_prompt)
                    engine = "offline/llamacpp"
        except Exception as exc:
            self.logger.error(f"[AIEngine] Chat solve error: {exc}")
            answer = f"[Error] {exc}"
            engine = mode

        duration = round(time.perf_counter() - t0, 2)
        return {
            "answer": answer,
            "duration": duration,
            "mode": mode,
            "engine": engine,
        }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return a status dict for both engines."""
        return {
            "mode": self.config.get("mode") or "combined",
            "offline": {
                "ready": self.offline.is_ready(),
                "status": self.offline.status_message(),
            },
            "online": {
                "ready": self.online.is_ready(),
                "status": self.online.status_message(),
                "active_key": self.online.get_active_key_info(),
            },
        }
