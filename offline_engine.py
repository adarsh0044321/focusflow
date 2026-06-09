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
import socket
from typing import Optional

logger = logging.getLogger("focusflow.ai")


class OfflineEngine:
    """Offline LLM backend using bundled llama.cpp — zero external installs."""

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logger
        self._server_process: Optional[subprocess.Popen] = None
        self._ready_event = threading.Event()
        self._status_lock = threading.Lock()
        with self._status_lock:
            self._status = "Not started"
        self._health_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _set_status(self, value: str) -> None:
        with self._status_lock:
            self._status = value

    def _get_status(self) -> str:
        with self._status_lock:
            return self._status

    def _port_in_use(self, port: int) -> bool:
        """Check if a local TCP port is already occupied."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                return s.connect_ex(('127.0.0.1', port)) == 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the llama.cpp server in the background."""
        self._start_llamacpp()

    def stop(self) -> None:
        """Stop the server process and clean up."""
        self._stop_event.set()
        self._ready_event.clear()
        if self._server_process is not None:
            try:
                self.logger.info("[LLM] Terminating server process...")
                self._server_process.terminate()
                try:
                    self._server_process.wait(timeout=3)
                    self.logger.info("[LLM] Server process terminated")
                except subprocess.TimeoutExpired:
                    self._server_process.kill()
                    self._server_process.wait(timeout=2)
                    self.logger.warning("[LLM] Server process killed after timeout")
            except Exception as exc:
                self.logger.error(f"[LLM] Error stopping server: {exc}")
            finally:
                self._server_process = None
        self._set_status("Stopped")

    def is_ready(self) -> bool:
        """Return True when the backend is loaded and responsive."""
        return self._ready_event.is_set()

    def status_message(self) -> str:
        """Return a human-readable status string."""
        return self._get_status()

    # ------------------------------------------------------------------
    # llama.cpp
    # ------------------------------------------------------------------

    def _read_stderr(self, process: subprocess.Popen) -> None:
        """Daemon thread target to consume llama-server stderr and prevent hangs."""
        try:
            if process.stderr is None:
                return
            for line in iter(process.stderr.readline, ""):
                line_str = line.strip()
                if line_str:
                    self.logger.debug(f"[LLM-stderr] {line_str}")
        except Exception as exc:
            self.logger.debug(f"[LLM] Stderr reader exception: {exc}")

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
            self._set_status(f"Config error: {exc}")
            self.logger.error(f"[LLM] {self._get_status()}")
            return

        if self._port_in_use(port):
            # Check if the existing server is responsive and healthy
            url = f"http://127.0.0.1:{port}/health"
            try:
                resp = requests.get(url, timeout=2.0)
                if resp.status_code == 200:
                    self.logger.info(f"[LLM] Port {port} in use by a healthy llama-server. Adopting it.")
                    self._ready_event.set()
                    self._set_status("LLM: Model loaded and ready! (Existing server)")
                    
                    # Start health monitoring for the adopted server
                    self._stop_event.clear()
                    self._health_thread = threading.Thread(
                        target=self._poll_health,
                        args=(port,),
                        daemon=True,
                        name="llm-health-poll",
                    )
                    self._health_thread.start()
                    return
            except Exception:
                pass

            self._set_status(f"Port {port} already in use")
            self.logger.warning(f"[LLM] Port {port} is already in use. Cannot start llama-server.")
            return

        if not os.path.isfile(binary):
            self._set_status(f"Binary not found: {binary}")
            self.logger.error(f"[LLM] {self._get_status()}")
            return

        if not os.path.isfile(model):
            self._set_status(f"Model not found: {model}")
            self.logger.error(f"[LLM] {self._get_status()}")
            return

        cmd = [
            str(binary),
            "--model", str(model),
            "--port", str(port),
            "--ctx-size", str(ctx),
            "--threads", str(threads),
            "--n-gpu-layers", str(gpu),
            "--host", "127.0.0.1",
            "--flash-attn", "auto",
            "--log-disable",
        ]

        self.logger.info(f"[LLM] Launching: {' '.join(cmd)}")
        self._set_status("Loading model... (may take 30-60s on low-RAM PC)")

        # Windows-specific: completely hide the console window
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

        try:
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            # Start stderr reader thread to log output and prevent pipe congestion
            threading.Thread(
                target=self._read_stderr,
                args=(self._server_process,),
                daemon=True,
                name="llm-stderr-reader"
            ).start()
        except FileNotFoundError:
            self._set_status(f"Cannot execute: {binary}")
            self.logger.error(f"[LLM] {self._get_status()}")
            return
        except OSError as exc:
            self._set_status(f"OS error launching server: {exc}")
            self.logger.error(f"[LLM] {self._get_status()}")
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
        """Poll the llama.cpp /health endpoint every 2s until ready, then monitor."""
        url = f"http://127.0.0.1:{port}/health"
        retries = 0
        max_retries = 30

        # Phase 1: Wait/Poll for model loading
        while not self._stop_event.is_set() and not self._ready_event.is_set():
            if self._server_process is not None and self._server_process.poll() is not None:
                self._set_status("Server process exited unexpectedly")
                self.logger.error("[LLM] Server process exited unexpectedly during startup")
                return

            try:
                resp = requests.get(url, timeout=2.0)
                if resp.status_code == 200:
                    self._ready_event.set()
                    self._set_status("LLM: Model loaded and ready!")
                    self.logger.info("[LLM] Server is healthy — model ready")
                    break
            except requests.RequestException:
                pass

            retries += 1
            if retries >= max_retries:
                self._set_status("Timeout: model failed to load")
                self.logger.error("[LLM] Timeout waiting for model to load. Killing server.")
                self.stop()
                return

            self._set_status(f"Loading model... ({retries * 2}s elapsed)")
            self._stop_event.wait(2.0)

        # Phase 2: Continuous post-ready monitoring
        while not self._stop_event.is_set():
            self._stop_event.wait(5.0)
            if self._stop_event.is_set():
                break

            # Check if process is still alive (only for servers we launched)
            if self._server_process is not None and self._server_process.poll() is not None:
                self._ready_event.clear()
                self._set_status("Server crashed")
                self.logger.error("[LLM] Server process died post-readiness")
                break

            # Poll health endpoint again to confirm responsiveness
            try:
                resp = requests.get(url, timeout=3.0)
                if resp.status_code != 200:
                    self._ready_event.clear()
                    self._set_status("Server unresponsive")
                    self.logger.warning("[LLM] Server returned unhealthy status code")
                else:
                    if not self._ready_event.is_set():
                        self._ready_event.set()
                        self._set_status("LLM: Model loaded and ready!")
            except requests.RequestException:
                self._ready_event.clear()
                self._set_status("Server unresponsive")
                self.logger.warning("[LLM] Health check timed out or failed post-readiness")

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
        if not self._ready_event.is_set():
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

    def _format_phi3_chat(self, messages: list[dict[str, str]], system_prompt: str = "") -> str:
        """Format a list of message dicts into the Phi-3 chat template format."""
        parts: list[str] = []
        sys_text = system_prompt.strip()
        if sys_text:
            parts.append(f"<|system|>\n{sys_text}\n<|end|>")
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"<|{role}|>\n{content.strip()}\n<|end|>")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)

    def query_chat(self, messages: list[dict[str, str]], system_prompt: str = "") -> str:
        """Send a multi-turn chat sequence to llama.cpp and return the assistant response."""
        if not self._ready_event.is_set():
            raise RuntimeError("Offline engine is not ready")

        port = int(self.config.get("llm_port"))
        url = f"http://127.0.0.1:{port}/completion"

        formatted = self._format_phi3_chat(messages, system_prompt)

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
                self.logger.warning("[LLM] Empty chat response from llama.cpp")
            return content
        except requests.Timeout:
            self.logger.error("[LLM] llama.cpp chat query timed out")
            return "[Error] The model took too long to respond."
        except requests.RequestException as exc:
            self.logger.error(f"[LLM] llama.cpp chat query failed: {exc}")
            return f"[Error] Query failed: {exc}"
        except (KeyError, ValueError) as exc:
            self.logger.error(f"[LLM] Bad chat response format: {exc}")
            return "[Error] Invalid response from model."
