"""Verify the administrative CTAN-to-GTFS link refresh command's reported outcome."""

import json
from io import StringIO

import pytest
from django.core.management import call_command

from transport.management.commands import link_ctan_gtfs_places
from transport.services.ctan_gtfs_links import CTANGTFSLinkRefresh


def test_command_reports_the_refreshed_active_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose an operator-readable summary without requiring live CTAN requests in tests."""
    expected_result = CTANGTFSLinkRefresh(
        dataset_id=17,
        place_count=25,
        stop_count=152,
        link_count=152,
    )
    monkeypatch.setattr(
        link_ctan_gtfs_places,
        "refresh_active_ctan_gtfs_place_stop_links",
        lambda: expected_result,
    )
    output = StringIO()
    call_command("link_ctan_gtfs_places", stdout=output)
    assert json.loads(output.getvalue()) == expected_result.as_dict()
