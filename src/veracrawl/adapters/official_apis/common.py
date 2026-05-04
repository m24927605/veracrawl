"""Shared helpers for concrete official API adapters."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from urllib.parse import urlparse

from veracrawl.contracts.common import Ref
from veracrawl.contracts.ecommerce_official_api import EcommerceOfficialApiTargetSpec
from veracrawl.ports.ecommerce_official_api import (
    EcommerceOfficialApiFetchOutcome,
    EcommerceOfficialApiResponse,
)

HttpTransport = Callable[
    [urllib.request.Request, float],
    EcommerceOfficialApiResponse,
]


def stdlib_transport(
    request: urllib.request.Request,
    timeout_seconds: float,
) -> EcommerceOfficialApiResponse:
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            headers = {str(key): str(value) for key, value in response.headers.items()}
            return EcommerceOfficialApiResponse(
                status_code=int(response.status),
                request_url=str(request.full_url),
                final_url=str(response.geturl()),
                headers=headers,
                body=body,
            )
    except urllib.error.HTTPError as exc:
        body = exc.read()
        headers = {str(key): str(value) for key, value in exc.headers.items()}
        return EcommerceOfficialApiResponse(
            status_code=int(exc.code),
            request_url=str(request.full_url),
            final_url=str(exc.url),
            headers=headers,
            body=body,
        )
    except urllib.error.URLError as exc:
        raise OSError(str(exc)) from exc


def env_present(name: str) -> bool:
    return bool(os.environ.get(name))


def missing_outcome(
    *,
    fixture_id: str,
    target: EcommerceOfficialApiTargetSpec,
    missing_env_vars: list[str],
) -> EcommerceOfficialApiFetchOutcome:
    base = f"{fixture_id}:{target.id}:official-api"
    return EcommerceOfficialApiFetchOutcome(
        credential_grant_ref=f"credential-grant:{base}:unavailable",
        credential_audit_ref=f"credential-audit:{base}:missing-env",
        failure_type="official_api_credentials_unavailable",
        diagnostics=[
            (
                f"{target.site_name} official API credentials are unavailable; "
                f"missing env vars: {', '.join(missing_env_vars)}"
            )
        ],
    )


def adapter_failure(
    *,
    fixture_id: str,
    target: EcommerceOfficialApiTargetSpec,
    failure_type: str,
    diagnostics: list[str],
) -> EcommerceOfficialApiFetchOutcome:
    base = f"{fixture_id}:{target.id}:official-api"
    return EcommerceOfficialApiFetchOutcome(
        credential_grant_ref=f"credential-grant:{base}:env",
        credential_audit_ref=f"credential-audit:{base}:attempted",
        failure_type=failure_type,
        diagnostics=diagnostics,
    )


def credential_refs(
    *,
    fixture_id: str,
    target: EcommerceOfficialApiTargetSpec,
    env_names: list[str],
) -> tuple[Ref, Ref]:
    base = f"{fixture_id}:{target.id}:official-api"
    env_slug = "-".join(sorted(name.lower() for name in env_names))
    return (
        f"credential-grant:{base}:env:{env_slug}",
        f"credential-audit:{base}:env:{env_slug}:redacted",
    )


def require_origin(url: str, allowed_origin: str) -> bool:
    return _origin(url) == allowed_origin


def headers_dict(headers: Mapping[str, str]) -> dict[str, str]:
    return {str(key): str(value) for key, value in headers.items()}


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

