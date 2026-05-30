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

_SYSTEM_PROMPT_BASE = (
    "You are an expert exam solver. Given a question (possibly from OCR "
    "with minor errors), solve it step-by-step.\n\n"
    "Rules:\n"
    "1. First, mentally repair any OCR errors in the question text.\n"
    "2. Solve the problem methodically.\n"
    "3. If options are provided, select the correct option.\n"
    "4. Give the final answer clearly as: \"Answer: [option/value]\""
)

_DETAIL_SUFFIX = "\n\nShow full working and explanation."

_CONCISE_SUFFIX = "\n\nBe brief. Give only the answer with minimal explanation."


class AIEngine:
    """Unified AI interface that routes to offline or online engines."""

    def __init__(self, config, knowledge_base=None) -> None:
        self.config = config
        self.kb = knowledge_base
        self.offline = OfflineEngine(config)
        self.online = OnlineEngine(config)
        self.logger = logger

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the offline engine if the current mode requires it."""
        mode = self.config.get("mode") or "combined"
        if mode in ("offline", "combined"):
            self.logger.info("[AIEngine] Starting offline engine")
            self.offline.start()

    def stop(self) -> None:
        """Stop the offline engine process."""
        self.logger.info("[AIEngine] Stopping offline engine")
        self.offline.stop()

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        """Assemble the system prompt with verbosity and knowledge context."""
        prompt = _SYSTEM_PROMPT_BASE

        verbosity = self.config.get("answer_mode") or "concise"
        if verbosity == "concise":
            prompt += _CONCISE_SUFFIX
        else:
            prompt += _DETAIL_SUFFIX

        return prompt

    def _get_knowledge_context(self) -> str:
        """Pull relevant context from the knowledge base, if available."""
        if self.kb is None:
            return ""
        try:
            context: str = self.kb.get_context("")  # type: ignore[union-attr]
            if context and context.strip():
                return f"\nRelevant reference material:\n{context.strip()}"
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
        mode = self.config.get("mode") or "combined"
        if mode == "combined":
            # In combined mode, check which sub-mode is active
            combined_active = self.config.get("combined_active") or "offline"
            if combined_active == "online" and self.online.is_ready():
                return "online"
            if self.offline.is_ready():
                return "offline"
            if self.online.is_ready():
                self.logger.info("[AIEngine] Combined: offline not ready, using online")
                return "online"
            return "offline"  # will fail gracefully with a status message
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
        system_prompt = self._build_system_prompt()
        knowledge_ctx = self._get_knowledge_context()
        mode = self._effective_mode()

        answer: str
        engine: str

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

        return answer, "online/gpt-5"

    # ------------------------------------------------------------------
    # Manual question (no OCR)
    # ------------------------------------------------------------------

    def solve_manual(self, question_text: str) -> dict[str, Any]:
        """Solve a manually typed question (no image, no OCR artefacts).

        The system prompt omits the OCR-repair instruction.
        """
        t0 = time.perf_counter()
        knowledge_ctx = self._get_knowledge_context()
        mode = self._effective_mode()

        system_prompt = (
            "You are an expert exam solver. Solve the following question step-by-step.\n\n"
            "Rules:\n"
            "1. Solve the problem methodically.\n"
            "2. If options are provided, select the correct option.\n"
            "3. Give the final answer clearly as: \"Answer: [option/value]\""
        )

        verbosity = self.config.get("answer_mode") or "concise"
        if verbosity == "concise":
            system_prompt += _CONCISE_SUFFIX
        else:
            system_prompt += _DETAIL_SUFFIX

        answer: str
        engine: str

        try:
            if mode == "online":
                full_sys = system_prompt
                if knowledge_ctx.strip():
                    full_sys = f"{system_prompt}\n{knowledge_ctx}"
                answer = self.online.query_text(question_text, full_sys)
                engine = "online/gpt-5"
            else:
                if not self.offline.is_ready():
                    status = self.offline.status_message()
                    answer = f"[Offline engine not ready] {status}"
                    engine = "offline"
                else:
                    answer = self.offline.query(question_text, system_prompt, knowledge_ctx)
                    engine = "offline/llamacpp"
        except Exception as exc:
            self.logger.error(f"[AIEngine] Manual solve error: {exc}")
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
