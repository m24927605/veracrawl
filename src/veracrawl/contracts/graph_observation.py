"""Graph-observation event contracts (s4 of general-purpose-crawler-agentification).

See ``docs/plans/general-purpose-crawler-agentification/
s4-graph-observation-port-contract.md``. Five framework-neutral
``VeraModel`` types — no implicit ``utc_now()`` — so replay is
byte-equal given the same caller-supplied timestamps.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlparse

from pydantic import field_validator, model_validator

from veracrawl.contracts.common import Ref, VeraModel
from veracrawl.contracts.enums import CanonicalSource


def _is_http(v: str) -> bool:
    p = urlparse(v)
    return p.scheme in {"http", "https"} and bool(p.netloc)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _utc(name: str, v: datetime) -> datetime:
    if v.tzinfo is None or v.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if v.utcoffset() != UTC.utcoffset(v):
        raise ValueError(f"{name} must be UTC")
    return v


def _check_event_anchors(model: VeraModel) -> None:
    _require(bool(model.id.strip()), "id must be non-blank")  # type: ignore[attr-defined]
    _require(bool(model.run_ref.strip()), "run_ref must be non-blank")  # type: ignore[attr-defined]


class UrlObservedEvent(VeraModel):
    id: str
    run_ref: Ref
    canonical_url: str
    depth: int
    parent_canonical_url: str | None = None
    source_ref: Ref
    observed_at: datetime
    @field_validator("observed_at")
    @classmethod
    def _u(cls, v: datetime) -> datetime: return _utc("observed_at", v)
    @model_validator(mode="after")
    def _validate(self) -> UrlObservedEvent:
        _check_event_anchors(self)
        _require(bool(self.source_ref.strip()), "source_ref must be non-blank")
        _require(_is_http(self.canonical_url), "canonical_url must be absolute http(s)")
        _require(self.depth >= 0, "depth must be non-negative")
        if self.parent_canonical_url is not None:
            _require(_is_http(self.parent_canonical_url),
                     "parent_canonical_url must be absolute http(s) when set")
        return self


class RedirectObservedEvent(VeraModel):
    id: str
    run_ref: Ref
    from_canonical_url: str
    to_canonical_url: str
    status_code: int
    observed_at: datetime
    @field_validator("observed_at")
    @classmethod
    def _u(cls, v: datetime) -> datetime: return _utc("observed_at", v)
    @model_validator(mode="after")
    def _validate(self) -> RedirectObservedEvent:
        _check_event_anchors(self)
        _require(_is_http(self.from_canonical_url),
                 "from_canonical_url must be absolute http(s)")
        _require(_is_http(self.to_canonical_url),
                 "to_canonical_url must be absolute http(s)")
        _require(self.from_canonical_url != self.to_canonical_url,
                 "from_canonical_url must differ from to_canonical_url")
        _require(300 <= self.status_code <= 399, "status_code must be in [300, 399]")
        return self


class CanonicalObservedEvent(VeraModel):
    id: str
    run_ref: Ref
    linked_canonical_url: str
    canonical_target_url: str
    source_kind: CanonicalSource
    observed_at: datetime
    @field_validator("observed_at")
    @classmethod
    def _u(cls, v: datetime) -> datetime: return _utc("observed_at", v)
    @model_validator(mode="after")
    def _validate(self) -> CanonicalObservedEvent:
        _check_event_anchors(self)
        _require(_is_http(self.linked_canonical_url),
                 "linked_canonical_url must be absolute http(s)")
        _require(_is_http(self.canonical_target_url),
                 "canonical_target_url must be absolute http(s)")
        _require(self.linked_canonical_url != self.canonical_target_url,
                 "linked_canonical_url must differ from canonical_target_url")
        return self


class PageStructureObservedEvent(VeraModel):
    id: str
    run_ref: Ref
    page_canonical_url: str
    discovered_link_count: int
    discovered_canonical_urls: list[str]
    observed_at: datetime
    @field_validator("observed_at")
    @classmethod
    def _u(cls, v: datetime) -> datetime: return _utc("observed_at", v)
    @model_validator(mode="after")
    def _validate(self) -> PageStructureObservedEvent:
        _check_event_anchors(self)
        _require(_is_http(self.page_canonical_url),
                 "page_canonical_url must be absolute http(s)")
        _require(self.discovered_link_count >= 0,
                 "discovered_link_count must be non-negative")
        for i, url in enumerate(self.discovered_canonical_urls):
            _require(_is_http(url),
                     f"discovered_canonical_urls[{i}] must be absolute http(s)")
        if len(set(self.discovered_canonical_urls)) != len(self.discovered_canonical_urls):
            raise ValueError("discovered_canonical_urls must not contain duplicate URLs")
        return self


class GraphObservationSnapshot(VeraModel):
    id: str
    run_ref: Ref
    url_observed_events: list[UrlObservedEvent]
    redirect_observed_events: list[RedirectObservedEvent]
    canonical_observed_events: list[CanonicalObservedEvent]
    page_structure_observed_events: list[PageStructureObservedEvent]
    snapshot_at: datetime
    @field_validator("snapshot_at")
    @classmethod
    def _u(cls, v: datetime) -> datetime: return _utc("snapshot_at", v)
    @model_validator(mode="after")
    def _validate(self) -> GraphObservationSnapshot:
        _check_event_anchors(self)
        for lst in ("url_observed_events", "redirect_observed_events",
                    "canonical_observed_events", "page_structure_observed_events"):
            for ev in getattr(self, lst):
                if ev.run_ref != self.run_ref:
                    raise ValueError(f"{lst} entry run_ref must match snapshot run_ref")
        return self
