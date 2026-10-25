from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.exceptions import InvalidOrbitalRecordError, TLEChecksumError
from backend.tle_parser import parse_tle_epoch, records_by_query, tle_checksum
from tests.conftest import ISS_L1, ISS_L2, VANGUARD_L1, VANGUARD_L2


def test_checksum_matches_published_digits() -> None:
    assert tle_checksum(ISS_L1[:68]) == int(ISS_L1[68])
    assert tle_checksum(ISS_L2[:68]) == int(ISS_L2[68])
    assert tle_checksum(VANGUARD_L1[:68]) == int(VANGUARD_L1[68])
    assert tle_checksum(VANGUARD_L2[:68]) == int(VANGUARD_L2[68])


def test_parse_sample_catalog(sample_records) -> None:
    ids = {r.catalog_id for r in sample_records}
    assert ids == {"25544", "20580", "25338", "5"}
    iss = next(r for r in sample_records if r.catalog_id == "25544")
    assert iss.name == "ISS (ZARYA)"
    assert iss.inclination_deg == pytest.approx(51.6439)
    assert iss.eccentricity == pytest.approx(0.0007417)
    assert iss.mean_motion_rev_per_day == pytest.approx(15.50103472)


def test_catalog_identifier_mismatch(validator, retrieved_at) -> None:
    bad_l2 = "2 25545" + ISS_L2[7:]
    with pytest.raises(InvalidOrbitalRecordError, match="do not match"):
        validator.parse_pair(ISS_L1, bad_l2, name="x", source="t", retrieved_at=retrieved_at)


def test_checksum_mismatch_strict(validator, retrieved_at) -> None:
    bad = ISS_L1[:68] + str((int(ISS_L1[68]) + 1) % 10)
    with pytest.raises(TLEChecksumError):
        validator.parse_pair(bad, ISS_L2, name="x", source="t", retrieved_at=retrieved_at)


def test_checksum_mismatch_non_strict_warns(validator, retrieved_at) -> None:
    bad = ISS_L1[:68] + str((int(ISS_L1[68]) + 1) % 10)
    rec = validator.parse_pair(
        bad, ISS_L2, name="x", source="t", retrieved_at=retrieved_at, strict_checksum=False
    )
    assert rec.validation_status == "valid_with_warnings"
    assert any("checksum" in m.lower() for m in rec.validation_messages)


def test_incomplete_and_malformed_text(validator, retrieved_at) -> None:
    text = "ISS\n1 25544U incomplete\nNOT A LINE\n"
    records, issues = validator.parse_text(text, source="t", retrieved_at=retrieved_at)
    assert records == []
    reasons = {i["reason"] for i in issues}
    assert "incomplete_record" in reasons or "missing_tle_after_name" in reasons


def test_duplicate_catalog_keeps_last(validator, retrieved_at) -> None:
    text = "\n".join(["A", ISS_L1, ISS_L2, "B", ISS_L1, ISS_L2])
    records, issues = validator.parse_text(text, source="t", retrieved_at=retrieved_at)
    assert len(records) == 1
    assert any(i["reason"] == "duplicate_catalog_id" for i in issues)
    assert records[0].name == "B"


def test_epoch_conversion_iss() -> None:
    epoch = parse_tle_epoch(ISS_L1)
    assert epoch.year == 2019
    assert epoch.tzinfo is not None
    # Day 343.69339541 of 2019 is 9 December.
    assert epoch.month == 12
    assert epoch.day == 9


def test_epoch_conversion_vanguard() -> None:
    epoch = parse_tle_epoch(VANGUARD_L1)
    assert epoch == datetime(2000, 6, 27, 18, 50, 19, 733568, tzinfo=timezone.utc) or (
        epoch.year == 2000 and epoch.month == 6 and epoch.day == 27
    )


def test_records_by_query(sample_records) -> None:
    hits = records_by_query(sample_records, "25544")
    assert len(hits) == 1
    assert hits[0].name.startswith("ISS")
    by_name = records_by_query(sample_records, "noaa")
    assert len(by_name) == 1
    missing = records_by_query(sample_records, "does-not-exist")
    assert missing == []
