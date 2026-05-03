from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.product_acceptance_fixture_assertions import (
    assert_product_acceptance_fixture,
)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "product-acceptance-success",
        "product-acceptance-runtime-unavailable",
        "product-acceptance-missing-workflow",
        "product-acceptance-missing-minimum-gate",
        "product-acceptance-missing-evidence",
        "product-acceptance-missing-replay",
        "product-acceptance-missing-operator-visibility",
        "product-acceptance-missing-policy",
        "product-acceptance-missing-workflow-specific-refs",
        "product-acceptance-scaffold-only",
        "product-acceptance-contract-only",
        "product-acceptance-false-complete-status",
        "product-acceptance-degraded-operational",
        "product-acceptance-missing-export-reconciliation",
    ],
)
def test_product_acceptance_fixture_contracts(
    fixture_name: str,
    tmp_path: Path,
) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_name
    assert_product_acceptance_fixture(fixture_dir, out_dir=tmp_path / fixture_name)
