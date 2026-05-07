"""Back-compat re-export of the model-provider exception surface.

The canonical home for ``ModelProviderError`` and its subclasses moved
to :mod:`veracrawl.contracts.errors` per codex iter-4 important: core
/ domain components such as the Phase 4 ``OutboxBackedBudget`` raise
``TokenBudgetExceeded``, and core code must depend only on contracts
/ ports — not on adapter modules. This module remains as a thin
re-export so existing imports
(``from veracrawl.adapters.model_providers.errors import …``) and
the OpenAI adapter's compatibility imports keep working unchanged.

New callers should import from :mod:`veracrawl.contracts.errors`
directly.
"""

from __future__ import annotations

from veracrawl.contracts.errors import (
    ModelProviderError,
    ProviderAdapterFailure,
    ProviderAuthFailed,
    ProviderBadRequest,
    ProviderNotFound,
    ProviderRateLimited,
    ProviderServerError,
    StructuredOutputViolation,
    TokenBudgetExceeded,
    classify_provider_error,
)
from veracrawl.contracts.errors import (
    classify_provider_status as classify_status,
)

__all__ = [
    "ModelProviderError",
    "ProviderAdapterFailure",
    "ProviderAuthFailed",
    "ProviderBadRequest",
    "ProviderNotFound",
    "ProviderRateLimited",
    "ProviderServerError",
    "StructuredOutputViolation",
    "TokenBudgetExceeded",
    "classify_provider_error",
    "classify_status",
]
