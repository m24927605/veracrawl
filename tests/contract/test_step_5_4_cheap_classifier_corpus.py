"""Phase 5 step 5.4 — cheap-classifier corpus replay test.

Reads the JSON corpus at ``tests/fixtures/cheap_classifier/``
and asserts every sample's ``expected_verdict`` matches
``HeuristicCheapClassifier.classify``. This is the
fixture-mode equivalent of the Phase 6 step 6.5 ≥80%
hit-rate acceptance test (the Phase 6 corpus is real
production failures; here we drive the deterministic
classifier through curated synthetic shapes).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from veracrawl.agents.recovery.cheap_classifier import HeuristicCheapClassifier
from veracrawl.ports.recovery import CheapClassifierVerdict

_FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "cheap_classifier"


class _FakeStatusFailure(RuntimeError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"fake failure status={status_code}")


class _FakeRobotsBlockedError(RuntimeError):
    pass


_FakeRobotsBlockedError.__name__ = "RobotsBlockedError"


class _FakeAccessControlBlocked(RuntimeError):
    def __init__(self, classifier_provider: str) -> None:
        self.classifier_provider = classifier_provider
        super().__init__("blocked")


def _build_failure(sample: dict[str, Any]) -> BaseException:
    cls = sample["failure_class"]
    if cls == "_FakeStatusFailure":
        return _FakeStatusFailure(sample["status_code"])
    if cls == "RobotsBlockedError":
        return _FakeRobotsBlockedError("blocked")
    if cls == "AccessControlBlocked":
        return _FakeAccessControlBlocked(sample["classifier_provider"])
    if cls == "RuntimeError":
        return RuntimeError("unknown")
    raise ValueError(f"unsupported fixture failure_class: {cls}")


def _load_corpus() -> list[tuple[str, str, dict[str, Any]]]:
    """Returns ``[(path_stem, expected_verdict, sample), ...]``."""

    items: list[tuple[str, str, dict[str, Any]]] = []
    if not _FIXTURE_DIR.is_dir():
        pytest.skip(f"cheap-classifier fixture dir missing: {_FIXTURE_DIR}")
    for path in sorted(_FIXTURE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected = payload["expected_verdict"]
        for sample in payload["samples"]:
            items.append((path.stem, expected, sample))
    return items


@pytest.mark.parametrize(
    ("fixture_stem", "expected_verdict_str", "sample"),
    _load_corpus(),
)
def test_cheap_classifier_matches_corpus_expected_verdict(
    fixture_stem: str,
    expected_verdict_str: str,
    sample: dict[str, Any],
) -> None:
    """Every corpus sample classifies to its declared
    expected verdict. Phase 6 step 6.5 swaps this synthetic
    corpus for production failures + asserts ≥80% hit rate."""

    classifier = HeuristicCheapClassifier()
    failure = _build_failure(sample)
    verdict = classifier.classify(
        failure=failure,
        attempt_evidence_ref=f"attempt:corpus:{fixture_stem}",
    )
    expected = CheapClassifierVerdict(expected_verdict_str)
    assert verdict is expected, (
        f"corpus '{fixture_stem}' sample {sample!r} expected "
        f"{expected_verdict_str!r}, got {verdict.value!r}"
    )


def test_corpus_has_samples_for_all_terminal_verdicts() -> None:
    """Smoke test: the corpus covers all four
    ``CheapClassifierVerdict`` values so the Phase 6
    swap-in of production data has a complete shape to
    extend."""

    items = _load_corpus()
    seen_verdicts = {item[1] for item in items}
    expected_verdicts = {v.value for v in CheapClassifierVerdict}
    missing = expected_verdicts - seen_verdicts
    assert not missing, f"corpus missing samples for: {sorted(missing)}"
