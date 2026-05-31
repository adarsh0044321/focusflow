"""FocusFlow – OCR text cleaner.

Processes raw Tesseract output before it is sent to the AI back-end,
removing noise, fixing common OCR mistakes, and assessing overall text
quality.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import List, Tuple

logger = logging.getLogger("focusflow.ocr_cleaner")

# Characters that are almost always OCR junk
_UNICODE_JUNK_CATEGORIES = {"Cc", "Cf", "Co", "Cs", "Mn"}

# Patterns that indicate a line is a UI / website artifact
_UI_ARTIFACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bNetlify\b",
        r"\bDiscord\b",
        r"\bAsk Gemini\b",
        r"\bSign [Ii]n\b",
        r"\bSign [Uu]p\b",
        r"\bLog [Ii]n\b",
        r"\bLog [Oo]ut\b",
        r"\bCookie\s?[Pp]olicy\b",
        r"\bPrivacy\s?[Pp]olicy\b",
        r"\bTerms\s+of\s+[Ss]ervice\b",
        r"\bAccept\s+[Cc]ookies?\b",
        r"\bSubscribe\b",
        r"\bNewsletter\b",
        r"\bUnsubscribe\b",
        r"\bFollow\s+[Uu]s\b",
        r"\bShare\s+on\b",
        r"\bPowered\s+by\b",
        r"\bAll\s+[Rr]ights\s+[Rr]eserved\b",
        r"\b©\b",
        r"\bAdvertisement\b",
        r"\bSponsored\b",
        r"\bSkip\s+to\s+content\b",
        r"\bSearch\s*\.\.\.\s*$",
    )
]

# Common OCR substitution errors
_PIPE_IN_WORD = re.compile(r"(?<=[A-Za-z])\|(?=[A-Za-z])")
_LEADING_PIPE = re.compile(r"^\|(?=[a-z])", re.MULTILINE)


class OCRCleaner:
    """Clean raw OCR text and assess its quality."""

    def __init__(self) -> None:
        self.logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean(self, raw_text: str) -> Tuple[str, str, List[str]]:
        """Clean *raw_text* returned by the OCR engine.

        Returns
        -------
        tuple[str, str, list[str]]
            ``(cleaned_text, quality, warnings)``

            * *quality* is one of ``"good"``, ``"weak"``, ``"poor"``.
            * *warnings* lists human-readable notes about issues found.
        """

        if not raw_text:
            return "", "poor", ["Empty input text."]

        warnings: list[str] = []
        text = raw_text

        # 1. Remove Unicode junk characters
        text, n_junk = self._strip_unicode_junk(text)
        if n_junk:
            warnings.append(f"Removed {n_junk} junk Unicode character(s).")

        # 2. Strip leading/trailing whitespace from each line
        text = self._strip_line_whitespace(text)

        # 3. Collapse multiple spaces to single
        text = self._collapse_spaces(text)

        # 4. Remove garbage lines (>50 % non-alphanumeric)
        text, n_garbage = self._remove_garbage_lines(text)
        if n_garbage:
            warnings.append(f"Removed {n_garbage} garbage line(s).")

        # 5. Remove UI / website artifact lines
        text, n_artifacts = self._remove_ui_artifacts(text)
        if n_artifacts:
            warnings.append(f"Removed {n_artifacts} UI-artifact line(s).")

        # 6. Fix common OCR character errors
        text, n_fixes = self._fix_ocr_chars(text)
        if n_fixes:
            warnings.append(f"Applied {n_fixes} OCR character fix(es).")

        # 7. Collapse consecutive blank lines (max 2)
        text = self._collapse_blank_lines(text)

        # 8. Final trim
        text = text.strip()

        # 9. Quality assessment
        quality = self._assess_quality(text)

        self.logger.info(
            "OCR cleaning done – %d chars, quality=%s, %d warning(s).",
            len(text),
            quality,
            len(warnings),
        )
        return text, quality, warnings

    # ------------------------------------------------------------------
    # Internal cleaning steps
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_unicode_junk(text: str) -> Tuple[str, int]:
        """Remove control characters and other Unicode junk."""
        cleaned: list[str] = []
        removed = 0
        for ch in text:
            cat = unicodedata.category(ch)
            if cat in _UNICODE_JUNK_CATEGORIES and ch not in ("\n", "\r", "\t"):
                removed += 1
            else:
                cleaned.append(ch)
        return "".join(cleaned), removed

    @staticmethod
    def _strip_line_whitespace(text: str) -> str:
        """Strip leading/trailing whitespace from every line."""
        return "\n".join(line.strip() for line in text.splitlines())

    @staticmethod
    def _collapse_spaces(text: str) -> str:
        """Collapse runs of horizontal whitespace to a single space."""
        return re.sub(r"[^\S\n]+", " ", text)

    @staticmethod
    def _remove_garbage_lines(text: str) -> Tuple[str, int]:
        """Drop lines where more than 50 % of characters are non-
        alphanumeric (and non-whitespace)."""
        kept: list[str] = []
        removed = 0
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                kept.append(line)
                continue
            non_ws = stripped.replace(" ", "")
            if not non_ws:
                kept.append(line)
                continue
            alnum_count = sum(1 for c in non_ws if c.isalnum())
            ratio = alnum_count / len(non_ws)
            if ratio >= 0.50:
                kept.append(line)
            else:
                removed += 1
        return "\n".join(kept), removed

    @staticmethod
    def _remove_ui_artifacts(text: str) -> Tuple[str, int]:
        """Remove lines that match common UI / website chrome patterns."""
        kept: list[str] = []
        removed = 0
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and any(
                pat.search(stripped) for pat in _UI_ARTIFACT_PATTERNS
            ):
                removed += 1
            else:
                kept.append(line)
        return "\n".join(kept), removed

    @staticmethod
    def _fix_ocr_chars(text: str) -> Tuple[str, int]:
        """Fix frequent OCR character-swap errors.

        Rules applied:
        * ``|`` between letters → ``l``  (e.g. ``he|lo`` → ``hello``)
        * ``|`` at the start of a lowercase word → ``l``
        * Standalone ``0`` next to uppercase letters → ``O``
          (e.g. ``C0MPUTER`` → ``COMPUTER``)
        * Standalone ``O`` next to digits → ``0``
          (e.g. ``1O23`` → ``1023``)
        """
        fixes = 0

        # | → l inside words
        new_text, n = _PIPE_IN_WORD.subn("l", text)
        fixes += n
        text = new_text

        # | at start of lowercase word
        new_text, n = _LEADING_PIPE.subn("l", text)
        fixes += n
        text = new_text

        # 0 → O when surrounded by uppercase letters
        def _zero_to_o(m: re.Match[str]) -> str:
            nonlocal fixes
            fixes += 1
            return m.group(1) + "O" + m.group(2)

        text = re.sub(r"([A-Z])0([A-Z])", _zero_to_o, text)

        # O → 0 when surrounded by digits
        def _o_to_zero(m: re.Match[str]) -> str:
            nonlocal fixes
            fixes += 1
            return m.group(1) + "0" + m.group(2)

        text = re.sub(r"(\d)O(\d)", _o_to_zero, text)

        return text, fixes

    @staticmethod
    def _collapse_blank_lines(text: str) -> str:
        """Collapse runs of 3+ consecutive blank lines to exactly 2."""
        return re.sub(r"(\n\s*){3,}", "\n\n\n", text)

    # ------------------------------------------------------------------
    # Quality assessment
    # ------------------------------------------------------------------

    @staticmethod
    def _assess_quality(text: str) -> str:
        """Rate the cleaned text as ``good``, ``weak``, or ``poor``.

        Heuristics
        ----------
        * ``good``:  ≥ 80 % alphanumeric ratio *and* > 20 characters.
        * ``weak``:  50–80 % ratio *or* 10–20 characters.
        * ``poor``:  < 50 % ratio *or* < 10 characters.
        """
        stripped = text.strip()
        length = len(stripped)

        if length == 0:
            return "poor"

        non_ws = stripped.replace(" ", "").replace("\n", "")
        if not non_ws:
            return "poor"

        alnum = sum(1 for c in non_ws if c.isalnum())
        ratio = alnum / len(non_ws)

        if length < 10 or ratio < 0.50:
            return "poor"
        if length <= 20 or ratio < 0.80:
            return "weak"
        return "good"
