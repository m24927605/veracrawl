from __future__ import annotations

from veracrawl.memory.kernel import run_memory_kernel


def test_cross_scope_memory_uses_authorized_sanitized_tunnel() -> None:
    result = run_memory_kernel(
        fixture_id="unit-cross-scope",
        scenario="cross-scope-sanitized-memory",
        evidence_refs=["evidence:unit"],
        policy_decision_refs=["policy:unit:memory"],
    )
    assert result.tunnel
    assert result.tunnel.authorization_ref
    assert result.tunnel.sanitized_only
    assert result.tunnel.evidence_ref_required
    assert result.retrieval_trace
    assert result.retrieval_trace.cross_scope_tunnel_ref == result.tunnel.id


def test_unauthorized_cross_scope_memory_fails() -> None:
    result = run_memory_kernel(
        fixture_id="unit-cross-scope-denied",
        scenario="unauthorized-cross-scope-memory",
        policy_decision_refs=["policy:unit:memory"],
    )
    assert result.report.operator_status == "unauthorized_cross_scope_tunnel"
    assert not result.tunnel
