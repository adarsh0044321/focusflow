"""
FocusFlow Online AI Engine
OpenAI API integration with automatic key rotation on rate-limit errors.
"""

import base64
import io
import logging
from typing import Any, Optional

from openai import OpenAI, APIStatusError, RateLimitError, APIConnectionError

logger = logging.getLogger("focusflow.online")


class OnlineEngine:
    """OpenAI chat-completions wrapper with multi-key rotation and retry."""

    _MAX_RETRIES: int = 3

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logger
        self._key_index: int = 0
        self._clients: dict[str, OpenAI] = {}  # cached per key

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------

    def _get_client(self) -> tuple[OpenAI, str]:
        """Return the current OpenAI client, creating it lazily.

        Raises ``ValueError`` if no API keys are configured.
        """
        keys: list[str] = self.config.get_api_keys()
        if not keys:
            raise ValueError("No API keys configured")
        key = keys[self._key_index % len(keys)]
        if key not in self._clients:
            self._clients[key] = OpenAI(api_key=key)
        return self._clients[key], key

    def _rotate_key(self) -> None:
        """Advance to the next configured API key."""
        keys: list[str] = self.config.get_api_keys()
        if keys:
            self._key_index = (self._key_index + 1) % len(keys)
        self.logger.info(f"[API] Rotated to key index {self._key_index}")

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Return True when at least one API key is available."""
        try:
            keys = self.config.get_api_keys()
            return bool(keys)
        except Exception:
            return False

    def status_message(self) -> str:
        """Return a human-readable status string."""
        try:
            keys = self.config.get_api_keys()
        except Exception:
            return "API keys unavailable"
        if not keys:
            return "No API keys configured"
        return f"{len(keys)} key(s) configured — active key index {self._key_index}"

    def get_active_key_info(self) -> str:
        """Return a masked representation of the active key."""
        try:
            keys = self.config.get_api_keys()
        except Exception:
            return "N/A"
        if not keys:
            return "No keys"
        key = keys[self._key_index % len(keys)]
        masked = f"{key[:3]}...{key[-3:]}" if len(key) > 8 else "***"
        total = len(keys)
        idx = (self._key_index % total) + 1
        return f"{masked} (key {idx}/{total})"

    # ------------------------------------------------------------------
    # Retry wrapper
    # ------------------------------------------------------------------

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Decide whether an exception warrants key rotation."""
        if isinstance(exc, RateLimitError):
            return True
        if isinstance(exc, APIStatusError) and exc.status_code == 429:
            return True
        if isinstance(exc, APIStatusError):
            body = getattr(exc, "body", None)
            if isinstance(body, dict):
                err = body.get("error", {})
                code = err.get("code", "") if isinstance(err, dict) else ""
                if code in ("insufficient_quota", "rate_limit_exceeded"):
                    return True
        return False

    # ------------------------------------------------------------------
    # Text query
    # ------------------------------------------------------------------

    def query_text(self, prompt: str, system_prompt: str = "") -> str:
        """Send a text prompt via OpenAI Responses API and return the answer.

        Automatically rotates keys on rate-limit / quota errors.
        """
        model: str = "gpt-5"

        full_input = prompt.strip()
        if system_prompt.strip():
            full_input = f"{system_prompt.strip()}\n\nQuestion:\n{full_input}"

        last_error: Optional[Exception] = None
        for attempt in range(self._MAX_RETRIES):
            try:
                client, key = self._get_client()
                self.logger.debug(
                    f"[API] Text query attempt {attempt + 1} with key ...{key[-4:] if len(key) > 4 else '***'}"
                )

                response = client.responses.create(
                    model=model,
                    input=full_input,
                )
                if response and getattr(response, "output_text", None):
                    return response.output_text.strip()
                self.logger.warning("[API] Empty response from API")
                return ""

            except (RateLimitError, APIStatusError) as exc:
                last_error = exc
                if self._is_retryable(exc):
                    self.logger.warning(
                        f"[API] Retryable error on attempt {attempt + 1}: {exc}"
                    )
                    self._rotate_key()
                    continue
                self.logger.error(f"[API] Non-retryable API error: {exc}")
                return f"[Error] API error: {exc}"

            except APIConnectionError as exc:
                last_error = exc
                self.logger.error(f"[API] Connection error: {exc}")
                return f"[Error] Cannot reach OpenAI: {exc}"

            except ValueError as exc:
                self.logger.error(f"[API] {exc}")
                return f"[Error] {exc}"

            except Exception as exc:
                self.logger.error(f"[API] Unexpected error: {exc}")
                return f"[Error] {exc}"

        self.logger.error(f"[API] All {self._MAX_RETRIES} retries exhausted. Last: {last_error}")
        return f"[Error] All API keys exhausted after {self._MAX_RETRIES} retries."

    # ------------------------------------------------------------------
    # Vision query (image + text)
    # ------------------------------------------------------------------

    def query_image(
        self,
        image_pil: Any,
        prompt: str,
        system_prompt: str = "",
    ) -> str:
        """Send an image + text prompt via vision-capable Responses API.

        *image_pil* should be a ``PIL.Image.Image`` instance.
        The image is base64-encoded as PNG inline.
        """
        model: str = "gpt-5"

        # Encode image to base64 PNG
        try:
            buf = io.BytesIO()
            image_pil.save(buf, format="PNG")
            b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as exc:
            self.logger.error(f"[API] Failed to encode image: {exc}")
            return f"[Error] Image encoding failed: {exc}"

        full_input = prompt.strip()
        if system_prompt.strip():
            full_input = f"{system_prompt.strip()}\n\nQuestion:\n{full_input}"

        input_payload = [
            {"type": "text", "text": full_input},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_image}"
                }
            }
        ]

        last_error: Optional[Exception] = None
        for attempt in range(self._MAX_RETRIES):
            try:
                client, key = self._get_client()
                self.logger.debug(
                    f"[API] Vision query attempt {attempt + 1} with key ...{key[-4:] if len(key) > 4 else '***'}"
                )
                response = client.responses.create(
                    model=model,
                    input=input_payload,
                )
                if response and getattr(response, "output_text", None):
                    return response.output_text.strip()
                self.logger.warning("[API] Empty vision response from API")
                return ""

            except (RateLimitError, APIStatusError) as exc:
                last_error = exc
                if self._is_retryable(exc):
                    self.logger.warning(
                        f"[API] Retryable error on vision attempt {attempt + 1}: {exc}"
                    )
                    self._rotate_key()
                    continue
                self.logger.error(f"[API] Non-retryable API error: {exc}")
                return f"[Error] API error: {exc}"

            except APIConnectionError as exc:
                last_error = exc
                self.logger.error(f"[API] Connection error: {exc}")
                return f"[Error] Cannot reach OpenAI: {exc}"

            except ValueError as exc:
                self.logger.error(f"[API] {exc}")
                return f"[Error] {exc}"

            except Exception as exc:
                self.logger.error(f"[API] Unexpected error: {exc}")
                return f"[Error] {exc}"

        self.logger.error(f"[API] All {self._MAX_RETRIES} vision retries exhausted. Last: {last_error}")
        return f"[Error] All API keys exhausted after {self._MAX_RETRIES} retries."
