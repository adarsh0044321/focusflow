"""
FocusFlow Offline LLM Engine
llama.cpp (llama-server) backend only. Runs completely in the background
with no console windows, popups, or user prompts.
"""

import subprocess
import requests
import threading
import time
import logging
import os
import sys
from typing import Optional


logger = logging.getLogger("focusflow.ai")


class OfflineEngine:
    """Offline LLM backend using bundled llama.cpp — zero external installs."""

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logger
        self._server_process: Optional[subprocess.Popen] = None
        self._ready: bool = False
        self._status: str = "Not started"
        self._health_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the llama.cpp server in the background."""
        self._start_llamacpp()

    def stop(self) -> None:
        """Stop the server process and clean up."""
        self._stop_event.set()
        if self._server_process is not None:
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=10)
                self.logger.info("[LLM] Server process terminated")
            except subprocess.TimeoutExpired:
                self._server_process.kill()
                self.logger.warning("[LLM] Server process killed after timeout")
            except Exception as exc:
                self.logger.error(f"[LLM] Error stopping server: {exc}")
            finally:
                self._server_process = None
        self._ready = False
        self._status = "Stopped"

    def is_ready(self) -> bool:
        """Return True when the backend is loaded and responsive."""
        return self._ready

    def status_message(self) -> str:
        """Return a human-readable status string."""
        return self._status

    # ------------------------------------------------------------------
    # llama.cpp
    # ------------------------------------------------------------------

    def _start_llamacpp(self) -> None:
        """Launch llama-server.exe as a silent background subprocess."""
        try:
            binary: str = self.config.resolve_path(self.config.get("llm_binary"))
            model: str = self.config.resolve_path(self.config.get("llm_model_path"))
            port: int = int(self.config.get("llm_port"))
            ctx: int = int(self.config.get("llm_context_length"))
            threads: int = int(self.config.get("llm_threads"))
            gpu: int = int(self.config.get("llm_gpu_layers"))
        except Exception as exc:
            self._status = f"Config error: {exc}"
            self.logger.error(f"[LLM] {self._status}")
            return

        if not os.path.isfile(binary):
            self._status = f"Binary not found: {binary}"
            self.logger.error(f"[LLM] {self._status}")
            return

        if not os.path.isfile(model):
            self._status = f"Model not found: {model}"
            self.logger.error(f"[LLM] {self._status}")
            return

        cmd = [
            str(binary),
            "--model", str(model),
            "--port", str(port),
            "--ctx-size", str(ctx),
            "--threads", str(threads),
            "--n-gpu-layers", str(gpu),
            "--host", "127.0.0.1",
            "--flash-attn",
            "--log-disable",
        ]

        self.logger.info(f"[LLM] Launching: {' '.join(cmd)}")
        self._status = "Loading model... (may take 30-60s on low-RAM PC)"

        # Windows-specific: completely hide the console window
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

        try:
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            self._status = f"Cannot execute: {binary}"
            self.logger.error(f"[LLM] {self._status}")
            return
        except OSError as exc:
            self._status = f"OS error launching server: {exc}"
            self.logger.error(f"[LLM] {self._status}")
            return

        # Start health-polling in a daemon thread
        self._stop_event.clear()
        self._health_thread = threading.Thread(
            target=self._poll_health,
            args=(port,),
            daemon=True,
            name="llm-health-poll",
        )
        self._health_thread.start()

    def _poll_health(self, port: int) -> None:
        """Poll the llama.cpp /health endpoint every 2s until ready."""
        url = f"http://127.0.0.1:{port}/health"
        elapsed = 0
        while not self._stop_event.is_set():
            # If the process died, give up
            if self._server_process is not None and self._server_process.poll() is not None:
                self._status = "Server process exited unexpectedly"
                self.logger.error(f"[LLM] {self._status}")
                return
            try:
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    self._ready = True
                    self._status = "LLM: Model loaded and ready!"
                    self.logger.info("[LLM] Server is healthy — model ready")
                    return
            except requests.ConnectionError:
                pass
            except requests.RequestException as exc:
                self.logger.debug(f"[LLM] Health poll error: {exc}")
            elapsed += 2
            self._status = f"Loading model... ({elapsed}s elapsed)"
            self._stop_event.wait(2.0)

    # ------------------------------------------------------------------
    # Prompt formatting (Phi-3 chat template)
    # ------------------------------------------------------------------

    @staticmethod
    def _format_phi3_prompt(
        user_prompt: str,
        system_prompt: str = "",
        knowledge_context: str = "",
    ) -> str:
        """Build a Phi-3 instruct chat-template string."""
        parts: list[str] = []

        sys_text = system_prompt.strip()
        if knowledge_context.strip():
            sys_text = f"{sys_text}\n\n{knowledge_context}".strip()

        if sys_text:
            parts.append(f"<|system|>\n{sys_text}\n<|end|>")

        parts.append(f"<|user|>\n{user_prompt.strip()}\n<|end|>")
        parts.append("<|assistant|>\n")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        prompt: str,
        system_prompt: str = "",
        knowledge_context: str = "",
    ) -> str:
        """Send a prompt to llama.cpp and return the answer text."""
        if not self._ready:
            raise RuntimeError("Offline engine is not ready")

        return self._query_llamacpp(prompt, system_prompt, knowledge_context)

    def _query_llamacpp(
        self,
        prompt: str,
        system_prompt: str,
        knowledge_context: str,
    ) -> str:
        """Query the llama.cpp /completion endpoint."""
        port = int(self.config.get("llm_port"))
        url = f"http://127.0.0.1:{port}/completion"

        formatted = self._format_phi3_prompt(prompt, system_prompt, knowledge_context)

        payload = {
            "prompt": formatted,
            "n_predict": int(self.config.get("llm_max_tokens", 600)),
            "temperature": float(self.config.get("llm_temperature", 0.1)),
            "top_p": float(self.config.get("llm_top_p", 0.9)),
        }

        timeout = int(self.config.get("llm_timeout", 300))

        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            content: str = data.get("content", "").strip()
            if not content:
                self.logger.warning("[LLM] Empty response from llama.cpp")
            return content
        except requests.Timeout:
            self.logger.error("[LLM] llama.cpp query timed out")
            return "[Error] The model took too long to respond."
        except requests.RequestException as exc:
            self.logger.error(f"[LLM] llama.cpp query failed: {exc}")
            return f"[Error] Query failed: {exc}"
        except (KeyError, ValueError) as exc:
            self.logger.error(f"[LLM] Bad response format: {exc}")
            return "[Error] Invalid response from model."
