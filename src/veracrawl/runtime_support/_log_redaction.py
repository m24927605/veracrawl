"""Sensitive-key redaction processor for structured logs.

Designed as a structlog processor (matches the
``(logger, method_name, event_dict) -> event_dict`` callable signature) so it
can sit in any structlog pipeline. Has no third-party dependency so it can be
exercised in isolation.

Redaction is recursive: nested mappings (dict) and sequences (list, tuple)
are walked so values like ``{"headers": {"Authorization": "Bearer ..."}}``
are redacted at the inner key, not just the top level.
"""

from __future__ import annotations

import re
from typing import Any

# Keys whose values must never appear in logs in plaintext. Patterns match at
# "word boundaries" (start of string, underscore, or hyphen) to avoid false
# positives on benign names like ``somebody``, ``monkey``, ``tokenize``.
_SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:^|[_-])body$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])prompt$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])payload$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])tokens?$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])secret$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])key$", re.IGNORECASE),
    re.compile(r"^apikey$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])password$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])passwd$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])credentials?$", re.IGNORECASE),
    re.compile(r"^(?:set[-_]?)?cookie$", re.IGNORECASE),
    re.compile(r"^(?:proxy[-_]?)?authorization$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])csrf$", re.IGNORECASE),
    re.compile(r"(?:^|[_-])session[-_]id$", re.IGNORECASE),
    re.compile(r"^response[-_](?:text|body)$", re.IGNORECASE),
)

REDACTED = "<redacted>"
REDACTED_DEEP = "<redacted-too-deep>"

# Hard cap on recursion depth to bound work on pathologically deep structures
# (e.g. accidental cycles in user payloads). Practical event_dicts are <= 5.
_MAX_DEPTH = 12


def is_sensitive_key(key: str) -> bool:
    """Return True if ``key`` matches one of the sensitive-key patterns."""
    return any(pattern.search(key) for pattern in _SENSITIVE_PATTERNS)


def _redact_value(value: Any, depth: int) -> Any:
    """Recursively walk nested structures, redacting sensitive subkeys.

    - Dict: redact value if its key is sensitive; otherwise recurse into value.
    - List / tuple: recurse into each element.
    - Other types: returned unchanged.

    Depth is capped at ``_MAX_DEPTH``. **Fail closed**: any container reached
    beyond the cap is replaced with ``REDACTED_DEEP`` so a sensitive value
    cannot escape merely because it sat below the recursion limit.
    """
    if depth >= _MAX_DEPTH:
        if isinstance(value, (dict, list, tuple)):
            return REDACTED_DEEP
        return value
    if isinstance(value, dict):
        return {
            k: (
                REDACTED
                if isinstance(k, str) and is_sensitive_key(k)
                else _redact_value(v, depth + 1)
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item, depth + 1) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item, depth + 1) for item in value)
    return value


class RedactSensitiveProcessor:
    """Replace sensitive-key values in a structlog event_dict with ``<redacted>``.

    Mutates and returns the same top-level event_dict (matches structlog
    processor convention). Nested mappings and sequences are redacted into
    fresh structures (no in-place mutation of nested objects).
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
            else:
                event_dict[key] = _redact_value(event_dict[key], depth=1)
        return event_dict
