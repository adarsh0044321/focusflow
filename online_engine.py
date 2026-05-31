"""
FocusFlow Online AI Engine
OpenAI API integration with automatic key rotation on rate-limit errors.
"""

import base64
import io
import logging
import threading
import time
from typing import Any, Optional

from openai import OpenAI, APIStatusError, RateLimitError, APIConnectionError
from PIL import Image

logger = logging.getLogger("focusflow.online")


class OnlineEngine:
    """OpenAI chat-completions wrapper with multi-key rotation and retry."""

    _MAX_RETRIES: int = 3

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logger
        self._key_index: int = 0
        self._clients: dict[str, OpenAI] = {}  # cached per key
        self._key_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------

    def _get_client(self) -> tuple[OpenAI, str]:
        """Return the current OpenAI client, creating it lazily.

        Raises ``ValueError`` if no API keys are configured.
        """
        with self._key_lock:
            keys: list[str] = self.config.get_api_keys()
            if not keys:
                raise ValueError("No API keys configured. Add keys in Settings -> Online.")
            key = keys[self._key_index % len(keys)]
            if key not in self._clients:
                self._clients[key] = OpenAI(api_key=key)
            return self._clients[key], key

    def _rotate_key(self) -> None:
        """Advance to the next configured API key."""
        with self._key_lock:
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
        with self._key_lock:
            idx = self._key_index
        return f"{len(keys)} key(s) configured — active key index {idx}"

    def get_active_key_info(self) -> str:
        """Return a masked representation of the active key."""
        try:
            keys = self.config.get_api_keys()
        except Exception:
            return "N/A"
        if not keys:
            return "No keys"
        with self._key_lock:
            idx_val = self._key_index
        key = keys[idx_val % len(keys)]
        masked = f"{key[:3]}...{key[-3:]}" if len(key) > 8 else "***"
        total = len(keys)
        idx = (idx_val % total) + 1
        return f"{masked} (key {idx}/{total})"

    # ------------------------------------------------------------------
    # Retry wrapper
    # ------------------------------------------------------------------

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Decide whether an exception warrants key rotation."""
        if isinstance(exc, (RateLimitError, APIConnectionError)):
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
    # Core API request with fallback
    # ------------------------------------------------------------------

    def _request_completion(
        self,
        client: OpenAI,
        model: str,
        messages_or_input: Any,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Send query using responses API with fallback to chat completions."""
        try:
            # Try custom/deprecated responses API format
            response = client.responses.create(
                model=model,
                input=messages_or_input,
            )
            if response and getattr(response, "output_text", None):
                return response.output_text.strip()
        except AttributeError:
            # Standard OpenAI chat completions fallback
            if isinstance(messages_or_input, str):
                chat_messages = [{"role": "user", "content": messages_or_input}]
            else:
                # messages_or_input is already structured payload list
                chat_messages = [{"role": "user", "content": messages_or_input}]

            response = client.chat.completions.create(
                model=model,
                messages=chat_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if response and response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
        return ""

    # ------------------------------------------------------------------
    # Text query
    # ------------------------------------------------------------------

    def query_text(self, prompt: str, system_prompt: str = "") -> str:
        """Send a text prompt via OpenAI API and return the answer.

        Automatically rotates keys on rate-limit / quota errors.
        """
        model: str = self.config.get("online_model", "gpt-4o")
        max_tokens: int = int(self.config.get("online_max_tokens", 1000))
        temperature: float = float(self.config.get("online_temperature", 0.2))

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

                answer = self._request_completion(
                    client=client,
                    model=model,
                    messages_or_input=full_input,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if answer:
                    return answer
                self.logger.warning("[API] Empty response from API")
                return ""

            except APIStatusError as exc:
                last_error = exc
                if exc.status_code in (400, 404) and model != "gpt-4o-mini":
                    self.logger.warning(
                        f"[API] Model {model} failed with {exc.status_code}. Falling back to gpt-4o-mini."
                    )
                    model = "gpt-4o-mini"
                    continue

                if self._is_retryable(exc):
                    self.logger.warning(
                        f"[API] Retryable API status error on attempt {attempt + 1}: {exc}"
                    )
                    self._rotate_key()
                    time.sleep(min(2 ** attempt, 8))
                    continue
                self.logger.error(f"[API] Non-retryable API error: {exc}")
                return f"[Error] API error: {exc}"

            except (RateLimitError, APIConnectionError) as exc:
                last_error = exc
                self.logger.warning(
                    f"[API] Retryable connection/rate limit error on attempt {attempt + 1}: {exc}"
                )
                self._rotate_key()
                time.sleep(min(2 ** attempt, 8))
                continue

            except ValueError as exc:
                self.logger.error(f"[API] {exc}")
                return f"[Error] {exc}"

            except Exception as exc:
                self.logger.error(f"[API] Unexpected error: {exc}")
                return f"[Error] {exc}"

        self.logger.error(f"[API] All {self._MAX_RETRIES} retries exhausted. Last: {last_error}")
        return f"[Error] All API keys exhausted after {self._MAX_RETRIES} retries. (Last: {last_error})"

    # ------------------------------------------------------------------
    # Vision query (image + text)
    # ------------------------------------------------------------------

    def query_image(
        self,
        image_pil: Any,
        prompt: str,
        system_prompt: str = "",
    ) -> str:
        """Send an image + text prompt via vision-capable OpenAI API.

        *image_pil* should be a ``PIL.Image.Image`` instance.
        """
        model: str = self.config.get("online_model", "gpt-4o")
        max_tokens: int = int(self.config.get("online_max_tokens", 1000))
        temperature: float = float(self.config.get("online_temperature", 0.2))

        # Encode image to base64 JPEG
        try:
            # Resize image to max 1280px width
            w, h = image_pil.size
            if w > 1280:
                h = int(h * (1280 / w))
                w = 1280
                try:
                    resample_filter = Image.Resampling.LANCZOS
                except AttributeError:
                    try:
                        resample_filter = Image.LANCZOS
                    except AttributeError:
                        resample_filter = Image.ANTIALIAS
                image_pil = image_pil.resize((w, h), resample_filter)

            buf = io.BytesIO()
            if image_pil.mode != "RGB":
                image_pil = image_pil.convert("RGB")
            image_pil.save(buf, format="JPEG", quality=85)
            b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
            buf.close()
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
                    "url": f"data:image/jpeg;base64,{b64_image}"
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

                answer = self._request_completion(
                    client=client,
                    model=model,
                    messages_or_input=input_payload,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if answer:
                    return answer
                self.logger.warning("[API] Empty vision response from API")
                return ""

            except APIStatusError as exc:
                last_error = exc
                if exc.status_code in (400, 404) and model != "gpt-4o-mini":
                    self.logger.warning(
                        f"[API] Model {model} failed with {exc.status_code}. Falling back to gpt-4o-mini."
                    )
                    model = "gpt-4o-mini"
                    continue

                if self._is_retryable(exc):
                    self.logger.warning(
                        f"[API] Retryable API status error on vision attempt {attempt + 1}: {exc}"
                    )
                    self._rotate_key()
                    time.sleep(min(2 ** attempt, 8))
                    continue
                self.logger.error(f"[API] Non-retryable API error: {exc}")
                return f"[Error] API error: {exc}"

            except (RateLimitError, APIConnectionError) as exc:
                last_error = exc
                self.logger.warning(
                    f"[API] Retryable connection/rate limit error on vision attempt {attempt + 1}: {exc}"
                )
                self._rotate_key()
                time.sleep(min(2 ** attempt, 8))
                continue

            except ValueError as exc:
                self.logger.error(f"[API] {exc}")
                return f"[Error] {exc}"

            except Exception as exc:
                self.logger.error(f"[API] Unexpected error: {exc}")
                return f"[Error] {exc}"

        self.logger.error(f"[API] All {self._MAX_RETRIES} vision retries exhausted. Last: {last_error}")
        return f"[Error] All API keys exhausted after {self._MAX_RETRIES} vision retries. (Last: {last_error})"
