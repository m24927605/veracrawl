"""Standard-library HTTP source adapter.

This adapter is concrete and intentionally lives outside VeraCrawl core. It is
used for deterministic local benchmark acquisition and can be replaced by a
production HTTP client adapter later.
"""

from __future__ import annotations

import socket
import urllib.error
import urllib.request
from typing import Any

from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkRequest, NetworkResponse, RedirectHop
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult


class NetworkAdapterTimeoutError(ValueError):
    """Raised when a network acquisition exceeds its runtime budget."""


class _RecordingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, policy_decision_refs: list[str], request_ref: str) -> None:
        super().__init__()
        self.policy_decision_refs = policy_decision_refs
        self.request_ref = request_ref
        self.redirects: list[tuple[str, str, int]] = []

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        self.redirects.append((req.full_url, newurl, code))
        return super().redirect_request(req, fp, code, msg, headers, newurl)

    def redirect_hops(self) -> list[RedirectHop]:
        return [
            RedirectHop(
                id=f"redirect-hop:{self.request_ref}:{index}",
                request_ref=self.request_ref,
                sequence=index,
                from_url=from_url,
                to_url=to_url,
                status_code=status_code,
                policy_decision_refs=self.policy_decision_refs,
            )
            for index, (from_url, to_url, status_code) in enumerate(self.redirects, start=1)
        ]


class StdlibHttpSourceAdapter:
    def __init__(self, request: NetworkRequest) -> None:
        self.request = request
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        redirect_handler = _RecordingRedirectHandler(
            command.policy_snapshot_ref.split(",")
            if "," in command.policy_snapshot_ref
            else self.request.policy_decision_refs,
            self.request.id,
        )
        opener = urllib.request.build_opener(redirect_handler)
        http_request = urllib.request.Request(
            self.request.url,
            method=self.request.method,
            headers={"User-Agent": "VeraCrawl-local-fixture/1"},
        )
        try:
            with opener.open(http_request, timeout=self.request.timeout_ms / 1000) as response:
                body = response.read()
                final_url = response.geturl()
                status_code = int(response.getcode())
                content_type = response.headers.get("Content-Type", "application/octet-stream")
        except TimeoutError as exc:
            raise NetworkAdapterTimeoutError("network request timed out") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError | socket.timeout):
                raise NetworkAdapterTimeoutError("network request timed out") from exc
            raise ValueError(f"network request failed: {exc}") from exc

        body_text = body.decode("utf-8", errors="replace")
        digest = stable_hash({"url": final_url, "body": body_text})
        artifact_ref = f"artifact:{self.request.id}:raw-html:{digest[:12]}"
        redirect_hops = redirect_handler.redirect_hops()
        response_contract = NetworkResponse(
            id=f"network-response:{self.request.id}",
            request_ref=self.request.id,
            status_code=status_code,
            final_url=final_url,
            headers_ref=f"headers:{self.request.id}:response",
            raw_artifact_ref=artifact_ref,
            content_digest=digest,
            content_type=content_type.split(";", 1)[0],
            body_size_bytes=len(body),
            redirect_hop_refs=[hop.id for hop in redirect_hops],
            timing_ref=f"timing:{self.request.id}:response",
        )
        self._last_result = NetworkClientResult(
            response=response_contract,
            redirect_hops=redirect_hops,
            body_text=body_text,
            artifact_refs=[artifact_ref],
        )
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:network-fixture",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=[artifact_ref],
            policy_decision_refs=self.request.policy_decision_refs,
            replay_event_refs=[f"event:{command.command_envelope_id}:network_response_recorded"],
            idempotency_key=f"{command.adapter_spec.id}:{self.request.id}",
            status=AdapterResultStatus.SUCCEEDED,
        )
