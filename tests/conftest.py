from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.models import OrbitalRecord
from backend.tle_parser import TLEValidationService

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
SAMPLE_TLE = FIXTURES / 'sample.tle'

ISS_L1 = '1 25544U 98067A   19343.69339541  .00001764  00000-0  38792-4 0  9991'
ISS_L2 = '2 25544  51.6439 211.2001 0007417  17.6667  85.6398 15.50103472202482'
VANGUARD_L1 = '1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753'
VANGUARD_L2 = '2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667'
BENCHMARK_88888_L1 = '1 88888U          80275.98708465  .00073094  13844-3  66816-4 0    87'
BENCHMARK_88888_L2 = '2 88888  72.8435 115.9689 0086731  52.6988 110.5714 16.05824518  1058'


@pytest.fixture
def validator() -> TLEValidationService:
    return TLEValidationService()


@pytest.fixture
def retrieved_at() -> datetime:
    return datetime(2019, 12, 10, tzinfo=timezone.utc)


@pytest.fixture
def sample_records(validator: TLEValidationService, retrieved_at: datetime):
    records, issues = validator.parse_text(
        SAMPLE_TLE.read_text(encoding='utf-8'),
        source='test-fixture',
        retrieved_at=retrieved_at,
    )
    assert not issues
    return records


@pytest.fixture
def iss(validator: TLEValidationService, retrieved_at: datetime):
    return validator.parse_pair(
        ISS_L1,
        ISS_L2,
        name='ISS (ZARYA)',
        source='test-fixture',
        retrieved_at=retrieved_at,
    )


@pytest.fixture
def vanguard(validator: TLEValidationService, retrieved_at: datetime):
    return validator.parse_pair(
        VANGUARD_L1,
        VANGUARD_L2,
        name='VANGUARD 1',
        source='vallado-example',
        retrieved_at=datetime(2000, 6, 28, tzinfo=timezone.utc),
    )


@pytest.fixture
def benchmark_88888(validator: TLEValidationService):
    return validator.parse_pair(
        BENCHMARK_88888_L1,
        BENCHMARK_88888_L2,
        name='BENCHMARK 88888',
        source='spacetrack-report-3',
        retrieved_at=datetime(1980, 10, 2, tzinfo=timezone.utc),
    )
