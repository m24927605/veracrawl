"""Sensitive-key redaction processor for structured logs.

Designed as a structlog processor (matches the
``(logger, method_name, event_dict) -> event_dict`` callable signature) so it
can sit in any structlog pipeline. Has no third-party dependency so it can be
exercised in isolation before the wider logging module lands.
"""

from __future__ import annotations

import re
from typing import Any

# Keys whose values should never appear in logs in plaintext. Matches at
# "word boundaries" (start of string or underscore) to avoid accidental hits
# on benign names such as ``somebody`` or ``monkey``.
_SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:^|_)body$", re.IGNORECASE),
    re.compile(r"(?:^|_)prompt$", re.IGNORECASE),
    re.compile(r"(?:^|_)payload$", re.IGNORECASE),
    re.compile(r"(?:^|_)tokens?$", re.IGNORECASE),
    re.compile(r"(?:^|_)secret$", re.IGNORECASE),
    re.compile(r"^(?:api[-_]?)?key$", re.IGNORECASE),
    re.compile(r"^(?:set[-_]?)?cookie$", re.IGNORECASE),
    re.compile(r"^authorization$", re.IGNORECASE),
    re.compile(r"^proxy[-_]?authorization$", re.IGNORECASE),
    re.compile(r"^response_(?:text|body)$", re.IGNORECASE),
)

REDACTED = "<redacted>"


def is_sensitive_key(key: str) -> bool:
    """Return True if ``key`` matches one of the sensitive-key patterns."""
    return any(pattern.search(key) for pattern in _SENSITIVE_PATTERNS)


class RedactSensitiveProcessor:
    """Replace sensitive-key values in a structlog event_dict with ``<redacted>``.

    Mutates and returns the same dict (matches structlog processor convention).
    Non-string keys are ignored.
    """

    def __call__(
        self,
        logger: Any,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        for key in list(event_dict.keys()):
            if isinstance(key, str) and is_sensitive_key(key):
                event_dict[key] = REDACTED
        return event_dict
