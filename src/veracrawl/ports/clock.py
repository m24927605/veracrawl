"""Deterministic clock and randomness ports."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Protocol


class ClockPort(Protocol):
    def now(self) -> datetime: ...


class RandomnessPort(Protocol):
    def token(self, prefix: str = "id") -> str: ...


class FixedClock:
    def __init__(self, value: datetime | None = None) -> None:
        self.value = value or datetime(2026, 5, 2, tzinfo=UTC)

    def now(self) -> datetime:
        return self.value


class DeterministicRandomness:
    def __init__(self, seed: int = 1) -> None:
        self._random = random.Random(seed)

    def token(self, prefix: str = "id") -> str:
        return f"{prefix}-{self._random.randrange(1_000_000):06d}"
