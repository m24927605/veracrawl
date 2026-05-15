"""Deterministic multi-adapter dispatch (s3.2).

The runner asks ``_choose_fetcher`` which ``AdapterType`` to use for a
given ``FrontierItem``; the answer is a pure function of
``(item.canonical_url, priors, fetcher_map, replay_seed_ref,
source_adapters)`` so two runs with identical inputs always produce
identical adapter choices (replay-stable by construction).

Filter order is safety-first:

1. Filter ``priors`` to the intersection of ``spec.source_adapters``
   (the job-spec safety boundary).
2. Filter again to the intersection of ``fetcher_map`` (only adapters
   the runner can actually fetch with).
3. Renormalize remaining weights.
4. ``random.Random(seed=stable_hash(canonical_url + replay_seed_ref))``
   picks via ``choices`` — uniform distribution across equal weights.

See ``docs/plans/general-purpose-crawler-agentification/
s3.2-multi-adapter-dispatch.md``.
"""

from __future__ import annotations

import random
from collections.abc import Mapping

from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.crawl_planner import AdapterPrior
from veracrawl.contracts.enums import AdapterType
from veracrawl.external_crawl.frontier import FrontierItem


def _seed_int(*, canonical_url: str, replay_seed_ref: str) -> int:
    digest_hex = stable_hash(canonical_url + replay_seed_ref)
    # 64 bits is plenty for ``random.Random`` and keeps the cast cheap.
    return int(digest_hex[:16], 16)


def _choose_fetcher(
    *,
    item: FrontierItem,
    priors: list[AdapterPrior],
    fetcher_map: Mapping[AdapterType, object],
    replay_seed_ref: str,
    source_adapters: list[AdapterType] | tuple[AdapterType, ...],
) -> AdapterType:
    """Pure deterministic adapter choice.

    Raises ``ValueError`` when the inputs would force a non-decision
    (empty priors, empty fetcher map, blank seed, or zero effective
    weight after filtering).
    """

    if not priors:
        raise ValueError("priors must be non-empty")
    if not fetcher_map:
        raise ValueError("fetcher_map must be non-empty")
    if not replay_seed_ref.strip():
        raise ValueError("replay_seed_ref must be non-blank")

    allowed_types = set(source_adapters)
    fetcher_types = set(fetcher_map.keys())
    eligible = [
        p for p in priors
        if p.adapter_type in allowed_types and p.adapter_type in fetcher_types
    ]
    total_weight = sum(p.weight for p in eligible)
    if not eligible or total_weight <= 0.0:
        raise ValueError(
            "no eligible adapter prior after source_adapters / "
            "fetcher_map filtering with non-zero weight",
        )

    rng = random.Random(_seed_int(
        canonical_url=item.canonical_url,
        replay_seed_ref=replay_seed_ref,
    ))
    weights = [p.weight / total_weight for p in eligible]
    picked = rng.choices(eligible, weights=weights, k=1)[0]
    return picked.adapter_type


__all__ = ["_choose_fetcher"]
