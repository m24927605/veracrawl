from __future__ import annotations

import pytest

from tests.factories import policy_decision
from veracrawl.contracts.errors import PolicyViolationError
from veracrawl.policy.gates import blocked_action_report, is_allowed, require_allowed


def test_allow_policy_passes() -> None:
    decision = policy_decision(True)
    assert is_allowed(decision)
    require_allowed(decision)


def test_deny_policy_blocks_and_reports() -> None:
    decision = policy_decision(False)
    assert not is_allowed(decision)
    report = blocked_action_report(decision)
    assert report.visible_to_operator
    assert "blocked" in report.blocked_reason
    with pytest.raises(PolicyViolationError):
        require_allowed(decision)
