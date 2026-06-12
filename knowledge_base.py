"""
FocusFlow Knowledge Base
=========================
Loads plain-text reference files from the ``knowledge_base/`` directory and
provides simple keyword-based retrieval to inject relevant context into LLM
prompts.

Each ``.txt`` file in the directory represents one *topic*.  The topic name
is derived from the filename (without extension, underscores replaced by
spaces, title-cased).
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional


logger = logging.getLogger("focusflow.knowledge")

# Maximum characters returned per matching topic.
_MAX_CHARS_PER_TOPIC: int = 500
# Number of top matches to include in context.
_TOP_N: int = 3

# Standard English stop words to exclude from keyword scoring
_STOP_WORDS: set[str] = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "of", "at", "by", 
    "for", "with", "about", "against", "between", "into", "through", "during", 
    "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", 
    "on", "off", "over", "under", "again", "further", "then", "once", "here", 
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", 
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", 
    "same", "so", "than", "too", "very", "can", "will", "just", "should", "now", 
    "is", "was", "were", "are", "be", "been", "being", "have", "has", "had", 
    "having", "do", "does", "did", "doing", "what", "which", "who", "whom", 
    "this", "that", "these", "those", "am", "your", "our", "its", "their", 
    "them", "they", "he", "she", "it", "we", "you", "me", "him", "her", "his", 
    "hers", "us"
}


class KnowledgeBase:
    """In-memory collection of topic files with keyword search.

    Attributes:
        base_dir: Resolved root directory of the application.
        kb_dir:   ``knowledge_base/`` subdirectory that is scanned.
    """

    def __init__(self, base_dir: str | Path) -> None:
        """Load all ``.txt`` files from the knowledge-base directory.

        Args:
            base_dir: Application root directory.
        """
        self.base_dir: Path = Path(base_dir).resolve()
        self.kb_dir: Path = self.base_dir / "knowledge_base"

        # {topic_name: full_text}
        self._topics: dict[str, str] = {}

        self.reload()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_all_topics(self) -> list[str]:
        """Return a sorted list of loaded topic names."""
        return sorted(self._topics.keys())

    def get_context(self, question_text: str) -> str:
        """Find relevant topics for *question_text* via keyword matching.

        The question is tokenised into lowercase words.  Each topic is
        scored by the number of question-words that appear in its text.
        The top *_TOP_N* topics are returned, each truncated to
        *_MAX_CHARS_PER_TOPIC* characters.

        Args:
            question_text: Free-form question or OCR output.

        Returns:
            Combined context string (may be empty when nothing matches).
        """
        if not question_text or not self._topics:
            return ""

        # Tokenise the question into unique lowercase words (≥2 chars).
        words = set(re.findall(r"[a-zA-Z0-9]{2,}", question_text.lower()))
        words = {w for w in words if w not in _STOP_WORDS}
        if not words:
            return ""

        normalized_words = {self._normalize_word(w) for w in words}

        scored: list[tuple[str, int]] = []
        for topic, text in self._topics.items():
            topic_raw = set(re.findall(r"[a-zA-Z0-9]{2,}", text.lower()))
            topic_words = {self._normalize_word(w) for w in topic_raw}
            score = len(normalized_words.intersection(topic_words))
            if score > 0:
                scored.append((topic, score))

        if not scored:
            logger.debug("No knowledge-base matches for query")
            return ""

        # Sort descending by score, then alphabetically for stability.
        scored.sort(key=lambda t: (-t[1], t[0]))
        top = scored[:_TOP_N]

        parts: list[str] = []
        for topic, score in top:
            snippet = self._topics[topic][:_MAX_CHARS_PER_TOPIC]
            parts.append(f"[{topic}]\n{snippet}")
            logger.debug("KB match  topic=%s  score=%d", topic, score)

        return "\n\n".join(parts)

    @staticmethod
    def _normalize_word(w: str) -> str:
        w = w.lower()
        if len(w) > 4:
            if w.endswith("ies"):
                return w[:-3] + "y"
            if w.endswith("ves"):
                return w[:-3] + "f"
            if w.endswith("es") and not w.endswith("ss"):
                return w[:-2]
            if w.endswith("s") and not w.endswith("ss"):
                return w[:-1]
            if w.endswith("ing") and len(w) > 6:
                return w[:-3]
            if w.endswith("ed"):
                return w[:-2]
        return w

    def reload(self) -> None:
        """Re-scan ``knowledge_base/`` and reload all topic files."""
        self._topics.clear()

        if not self.kb_dir.is_dir():
            logger.info(
                "Knowledge-base directory does not exist: %s", self.kb_dir
            )
            return

        count = 0
        for entry in sorted(self.kb_dir.iterdir()):
            if entry.suffix.lower() != ".txt" or not entry.is_file():
                continue
            topic = self._filename_to_topic(entry.stem)
            try:
                text = entry.read_text(encoding="utf-8", errors="replace").strip()
                if text:
                    self._topics[topic] = text
                    count += 1
                    logger.debug("Loaded topic  %s  (%d chars)", topic, len(text))
                else:
                    logger.debug("Skipped empty file  %s", entry.name)
            except OSError as exc:
                logger.error("Failed to read %s: %s", entry, exc)

        logger.info(
            "Knowledge base loaded  %d topic(s) from %s", count, self.kb_dir
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _filename_to_topic(stem: str) -> str:
        """Convert a filename stem into a human-readable topic name.

        ``"organic_chemistry"`` → ``"Organic Chemistry"``
        """
        cleaned = stem.replace("_", " ").replace("-", " ").strip().title()
        return re.sub(r"\s+", " ", cleaned)
