from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CrossScopeTunnelStatus, MemoryType
from veracrawl.contracts.memory import CrossScopeMemoryTunnel


def test_cross_scope_tunnel_rejects_raw_or_unanchored_transfer() -> None:
    with pytest.raises(ValidationError):
        CrossScopeMemoryTunnel(
            id="cross-scope-memory-tunnel:raw",
            source_scope_ref="scope:source",
            target_scope_ref="scope:target",
            allowed_memory_types=[MemoryType.FAILURE_REPAIR],
            authorization_ref="authorization:raw",
            policy_decision_refs=["policy:raw:memory"],
            sanitized_only=False,
            evidence_ref_required=True,
            status=CrossScopeTunnelStatus.APPROVED,
        )
