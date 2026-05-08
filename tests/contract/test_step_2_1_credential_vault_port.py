"""Contract tests for Phase 2 step 2.1 — ``CredentialVaultPort``.

Surface-level tests for the port + ``CredentialValue`` redaction
contract. The :class:`EnvVarVault` impl is exercised in
``tests/unit/test_step_2_1_env_var_vault.py``.

The acceptance: a ``CredentialValue`` cannot leak its secret via
the default Python string-conversion paths (``__repr__`` /
``__str__`` / ``__format__``) or via pickle. Only :meth:`reveal`
exposes the secret.
"""

from __future__ import annotations

import copy
import logging
import pickle

import pytest

from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
    CredentialValue,
    CredentialVaultPort,
)


def test_credential_value_reveal_returns_secret() -> None:
    cred = CredentialValue(value="bearer-token-xyz", scope_ref="EBAY_PROD")
    assert cred.reveal() == "bearer-token-xyz"


def test_credential_value_repr_emits_redacted_marker() -> None:
    cred = CredentialValue(value="secret-1", scope_ref="EBAY_PROD")
    assert repr(cred) == "<credential:redacted:EBAY_PROD>"
    # Secret never appears in repr.
    assert "secret-1" not in repr(cred)


def test_credential_value_str_emits_redacted_marker() -> None:
    cred = CredentialValue(value="secret-2", scope_ref="AMAZON_SP")
    assert str(cred) == "<credential:redacted:AMAZON_SP>"
    assert "secret-2" not in str(cred)


def test_credential_value_format_redacts() -> None:
    """f-strings call ``__format__`` — the default path that leaks
    most often in production (``logger.info(f"got {cred}")``)."""

    cred = CredentialValue(value="secret-3", scope_ref="EBAY_PROD")
    formatted = f"got token={cred}"
    assert formatted == "got token=<credential:redacted:EBAY_PROD>"
    assert "secret-3" not in formatted


def test_credential_value_format_with_spec_still_redacts() -> None:
    cred = CredentialValue(value="secret-4", scope_ref="X")
    formatted = f"{cred:>40}"  # padding format spec
    assert "secret-4" not in formatted
    assert "<credential:redacted:X>" in formatted


def test_credential_value_pickle_refuses() -> None:
    """Pickling a credential is almost certainly a mis-use; refuse
    rather than silently emit the secret to a stable on-disk form."""

    cred = CredentialValue(value="secret-5", scope_ref="X")
    with pytest.raises(TypeError, match="refuses pickle"):
        pickle.dumps(cred)


def test_credential_value_copy_preserves_value_and_scope() -> None:
    """Shallow copy is allowed for defensive coding (rare but
    useful) — pickle is what we block."""

    cred = CredentialValue(value="secret-6", scope_ref="X")
    cloned = copy.copy(cred)
    assert cloned.reveal() == "secret-6"
    assert cloned.scope_ref == "X"


def test_credential_value_deepcopy_preserves_value_and_scope() -> None:
    cred = CredentialValue(value="secret-7", scope_ref="X")
    cloned = copy.deepcopy(cred)
    assert cloned.reveal() == "secret-7"


def test_credential_value_does_not_leak_via_logger_str_path(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A logger handed the wrapper as ``%s`` should not capture
    the secret in the log record's formatted message."""

    cred = CredentialValue(value="secret-via-log", scope_ref="X")
    logger = logging.getLogger("test_credential_logger")
    with caplog.at_level(logging.INFO, logger="test_credential_logger"):
        logger.info("authorization=%s", cred)
    assert any("secret-via-log" in record.getMessage() for record in caplog.records) is False


def test_credential_value_rejects_empty_value() -> None:
    with pytest.raises(ValueError):
        CredentialValue(value="", scope_ref="X")


def test_credential_value_rejects_empty_scope() -> None:
    with pytest.raises(ValueError):
        CredentialValue(value="x", scope_ref="")


def test_credential_value_eq_uses_identity_default() -> None:
    """Two wrappers around the same secret are NOT equal (identity
    semantics). Prevents leaking via ``cred == known_value``
    timing or output."""

    a = CredentialValue(value="same", scope_ref="X")
    b = CredentialValue(value="same", scope_ref="X")
    assert a != b
    assert a == a


def test_credential_not_found_error_is_keyerror() -> None:
    """``except KeyError`` catches it; typed callers can dispatch
    on the precise type."""

    err = CredentialNotFoundError("no credential")
    assert isinstance(err, KeyError)


def test_credential_vault_port_protocol_satisfied_by_test_double() -> None:
    """Static-style assertion: a minimal in-memory vault satisfies
    the runtime-checkable Protocol."""

    class _MinimalVault:
        def __init__(self) -> None:
            self._store: dict[tuple[str, str], str] = {}

        def get(self, *, scope_ref: str, key: str) -> CredentialValue:
            try:
                value = self._store[(scope_ref, key)]
            except KeyError as exc:
                raise CredentialNotFoundError(scope_ref, key) from exc
            return CredentialValue(value=value, scope_ref=scope_ref)

    vault: CredentialVaultPort = _MinimalVault()
    assert isinstance(vault, CredentialVaultPort)
