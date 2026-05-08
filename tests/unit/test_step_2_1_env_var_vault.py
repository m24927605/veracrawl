"""Unit tests for ``EnvVarVault`` (Phase 2 step 2.1 test impl).

design.md §4 Phase 2: ``EnvVarVault`` reads
``VERACRAWL_CRED_<scope>__<key>`` (double-underscore separator,
codex iter-3) from the process env. Tests
inject an ``environ`` dict so they don't pollute the real env.

Behavioral expectations:

1. Round-trip: ``set env → vault.get → reveal`` returns the
   original value.
2. Missing entry → :class:`CredentialNotFoundError`.
3. Empty / whitespace-only value → treated as missing
   (fail-closed for cooperative crawler).
4. Invalid scope_ref / key (lowercase / dashes / dots / empty)
   rejected with :class:`ValueError`.
5. Returned wrapper is a real :class:`CredentialValue` so the
   redaction contract from step 2.1 applies.
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.credential_vault.env_var_vault import EnvVarVault
from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
    CredentialValue,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    with_runtime_mode,
)


def test_get_returns_credential_value_from_env_var() -> None:
    vault = EnvVarVault(environ={"VERACRAWL_CRED_EBAY__API_KEY": "sk_live_abc123"})
    cred = vault.get(scope_ref="EBAY", key="API_KEY")
    assert isinstance(cred, CredentialValue)
    assert cred.reveal() == "sk_live_abc123"
    assert cred.scope_ref == "EBAY"


def test_missing_env_var_raises_credential_not_found() -> None:
    vault = EnvVarVault(environ={})
    with pytest.raises(CredentialNotFoundError):
        vault.get(scope_ref="EBAY", key="API_KEY")


def test_empty_value_treated_as_missing_fail_closed() -> None:
    """An empty / whitespace-only value is indistinguishable from
    misconfiguration; fail-closed rather than send empty
    Authorization upstream."""

    vault = EnvVarVault(environ={"VERACRAWL_CRED_EBAY__API_KEY": ""})
    with pytest.raises(CredentialNotFoundError):
        vault.get(scope_ref="EBAY", key="API_KEY")
    vault_ws = EnvVarVault(environ={"VERACRAWL_CRED_EBAY__API_KEY": "   \t"})
    with pytest.raises(CredentialNotFoundError):
        vault_ws.get(scope_ref="EBAY", key="API_KEY")


@pytest.mark.parametrize(
    "scope_ref",
    [
        "",  # empty
        "ebay",  # lowercase
        "EBAY-PROD",  # dash
        "EBAY.PROD",  # dot
        "EBAY/PROD",  # slash (path-traversal shape)
        "EBAY PROD",  # space
        "EBAY\nPROD",  # control char
    ],
)
def test_get_rejects_invalid_scope_ref_shape(scope_ref: str) -> None:
    vault = EnvVarVault(environ={})
    with pytest.raises(ValueError):
        vault.get(scope_ref=scope_ref, key="API_KEY")


@pytest.mark.parametrize(
    "key",
    [
        "",
        "api_key",
        "API-KEY",
        "API.KEY",
        "API/KEY",
        "API KEY",
    ],
)
def test_get_rejects_invalid_key_shape(key: str) -> None:
    vault = EnvVarVault(environ={})
    with pytest.raises(ValueError):
        vault.get(scope_ref="EBAY", key=key)


def test_returned_credential_redacts_in_repr_and_str() -> None:
    """End-to-end: the EnvVarVault returns a CredentialValue whose
    default string conversions hide the secret."""

    vault = EnvVarVault(environ={"VERACRAWL_CRED_X__K": "secret-vault-token"})
    cred = vault.get(scope_ref="X", key="K")
    assert "secret-vault-token" not in repr(cred)
    assert "secret-vault-token" not in str(cred)
    assert "secret-vault-token" not in f"{cred}"


def test_env_var_naming_does_not_leak_into_credential_value() -> None:
    """The CredentialValue stores the scope_ref the caller passed,
    not the constructed env var name. Audit / replay records
    showing ``scope_ref=EBAY`` should not betray the env var
    convention to anyone who only sees the wrapper."""

    vault = EnvVarVault(environ={"VERACRAWL_CRED_EBAY__API_KEY": "x"})
    cred = vault.get(scope_ref="EBAY", key="API_KEY")
    assert cred.scope_ref == "EBAY"
    assert "VERACRAWL_CRED_" not in repr(cred)
    assert "VERACRAWL_CRED_" not in str(cred)


def test_default_environ_uses_os_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    """When no ``environ`` arg is passed, ``EnvVarVault`` falls back
    to ``os.environ``. Verify by patching the process env."""

    monkeypatch.setenv("VERACRAWL_CRED_DEFAULT_TEST__KEY", "from-os-environ")
    vault = EnvVarVault()
    cred = vault.get(scope_ref="DEFAULT_TEST", key="KEY")
    assert cred.reveal() == "from-os-environ"


def test_get_refuses_in_production_mode() -> None:
    """Codex iter-1 important: defense in depth — ``EnvVarVault``
    is fixture-only and refuses to serve any credential under
    ``RuntimeMode.PRODUCTION`` even if a wiring regression would
    have routed production through it. The refusal happens
    before the env var lookup so a configured-but-test-only
    secret cannot leak under production wiring."""

    vault = EnvVarVault(environ={"VERACRAWL_CRED_X__K": "should-never-load"})
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as excinfo:
            vault.get(scope_ref="X", key="K")
    assert excinfo.value.backend == "env_var_vault"
    assert excinfo.value.gate == "credential_vault"


def test_unrelated_env_vars_are_not_leaked() -> None:
    """Vault only returns the exact ``VERACRAWL_CRED_<scope>__<key>``
    match — a related env var doesn't accidentally match."""

    vault = EnvVarVault(
        environ={
            "VERACRAWL_CRED_EBAY__API_KEY": "wanted",
            "VERACRAWL_CRED_EBAY__OTHER": "not-wanted",
            "VERACRAWL_CRED_OTHER__API_KEY": "not-wanted-2",
            "PATH": "/usr/bin",
        }
    )
    cred = vault.get(scope_ref="EBAY", key="API_KEY")
    assert cred.reveal() == "wanted"


def test_scope_key_underscore_ambiguity_disambiguated() -> None:
    """Codex iter-3 important: with a single-underscore separator,
    ``(scope='A_B', key='C')`` and ``(scope='A', key='B_C')`` both
    aliased to the same env var. Double-underscore separator now
    keeps them distinct — verify both round-trip independently."""

    vault = EnvVarVault(
        environ={
            "VERACRAWL_CRED_A_B__C": "scope-A_B/key-C",
            "VERACRAWL_CRED_A__B_C": "scope-A/key-B_C",
        }
    )
    assert vault.get(scope_ref="A_B", key="C").reveal() == "scope-A_B/key-C"
    assert vault.get(scope_ref="A", key="B_C").reveal() == "scope-A/key-B_C"


def test_not_found_error_does_not_echo_raw_scope_or_key() -> None:
    """The not-found error path must not echo the caller-supplied
    ``scope_ref`` / ``key`` — uppercase-digit-only tokens can pass
    the env-var-shape regex and still be real secrets, so the
    exception text would otherwise leak them into logs."""

    vault = EnvVarVault(environ={})
    secret_shaped = "AKIAIOSFODNN7EXAMPLE"  # uppercase + digits — passes regex
    with pytest.raises(CredentialNotFoundError) as excinfo:
        vault.get(scope_ref=secret_shaped, key="API_KEY")
    assert secret_shaped not in str(excinfo.value)


def test_empty_value_error_does_not_echo_raw_scope_or_key() -> None:
    """Same redaction rule for the empty-value branch."""

    secret_shaped = "AKIAIOSFODNN7EXAMPLE"
    vault = EnvVarVault(environ={f"VERACRAWL_CRED_{secret_shaped}__API_KEY": "   "})
    with pytest.raises(CredentialNotFoundError) as excinfo:
        vault.get(scope_ref=secret_shaped, key="API_KEY")
    assert secret_shaped not in str(excinfo.value)


def test_invalid_identifier_error_does_not_echo_raw_value() -> None:
    """Codex iter-3 minor: error text is credential-adjacent and
    must not echo the rejected identifier (caller may have handed
    us a secret-looking string)."""

    vault = EnvVarVault(environ={})
    secret_looking = "sk_live_abc.123"  # has a dot → invalid
    with pytest.raises(ValueError) as excinfo:
        vault.get(scope_ref=secret_looking, key="API_KEY")
    assert secret_looking not in str(excinfo.value)
    assert "abc.123" not in str(excinfo.value)
    assert "redacted" in str(excinfo.value)
