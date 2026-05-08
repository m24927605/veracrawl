"""Unit tests for ``InMemoryVaultBackend`` (Phase 2 step 2.4a fixture).

The fixture is production-mode-gated symmetric with Phase 2
step 2.1's ``EnvVarVault``; under ``RuntimeMode.PRODUCTION`` every
``fetch`` raises ``ProductionRuntimeNotImplemented``.
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.credential_vault.in_memory_vault_backend import (
    InMemoryVaultBackend,
)
from veracrawl.ports.vault_backend import (
    VaultBackendError,
    VaultBackendErrorKind,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    with_runtime_mode,
)


def test_fetch_returns_value_for_present_credential() -> None:
    backend = InMemoryVaultBackend(credentials={("X", "K"): "v"})
    assert backend.fetch(scope_ref="X", key="K") == "v"


def test_fetch_returns_none_for_missing() -> None:
    backend = InMemoryVaultBackend(credentials={})
    assert backend.fetch(scope_ref="X", key="K") is None


@pytest.mark.parametrize("blank", ["", "   ", "\t", "\n", " \t \n "])
def test_fetch_returns_none_for_blank_value(blank: str) -> None:
    backend = InMemoryVaultBackend(credentials={("X", "K"): blank})
    assert backend.fetch(scope_ref="X", key="K") is None


@pytest.mark.parametrize(
    "kind",
    list(VaultBackendErrorKind),
)
def test_fetch_raises_injected_failure_kind(kind: VaultBackendErrorKind) -> None:
    backend = InMemoryVaultBackend(fail_with_kind=kind)
    with pytest.raises(VaultBackendError) as excinfo:
        backend.fetch(scope_ref="X", key="K")
    assert excinfo.value.kind is kind


def test_production_mode_raises_production_runtime_not_implemented() -> None:
    """Defense-in-depth gate: under PRODUCTION, the fixture refuses
    to serve any credential. Symmetric with Phase 2 step 2.1's
    ``EnvVarVault`` gate."""

    backend = InMemoryVaultBackend(credentials={("X", "K"): "v"})
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as excinfo:
            backend.fetch(scope_ref="X", key="K")
    assert excinfo.value.backend == "in_memory_vault_backend"
    assert excinfo.value.gate == "vault_backend"


def test_production_mode_gates_before_failure_injection() -> None:
    """Even when ``fail_with_kind`` is set, the production gate
    fires first. Avoids leaking the injected-failure shape under
    PRODUCTION wiring regression."""

    backend = InMemoryVaultBackend(fail_with_kind=VaultBackendErrorKind.AUTH_FAILED)
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented):
            backend.fetch(scope_ref="X", key="K")
