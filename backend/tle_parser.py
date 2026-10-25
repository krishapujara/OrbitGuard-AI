"""TLE parsing, checksum validation, and epoch conversion.

TLE layout follows the historical NORAD two-line format documented by CelesTrak
(Kelso, GP data formats) and used by the sgp4 package. Checksum is the modulo-10
sum of all digits in columns 1-68 plus 1 for each minus sign.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from backend.exceptions import InvalidOrbitalRecordError, TLEChecksumError
from backend.models import OrbitalRecord


class TLEValidationService:
    def parse_text(
        self,
        text: str,
        *,
        source: str,
        retrieved_at: datetime | None = None,
        source_url: str | None = None,
        from_cache: bool = False,
        strict_checksum: bool = True,
    ) -> tuple[list[OrbitalRecord], list[dict[str, str]]]:
        retrieved_at = retrieved_at or datetime.now(timezone.utc)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        records: list[OrbitalRecord] = []
        issues: list[dict[str, str]] = []
        seen: dict[str, int] = {}
        i = 0
        while i < len(lines):
            raw = lines[i].strip()
            if not raw:
                i += 1
                continue
            name = "UNKNOWN"
            line1 = ""
            line2 = ""
            if raw.startswith("1 ") and len(raw) >= 68:
                line1 = raw
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("2 "):
                    line2 = lines[i + 1].strip()
                    i += 2
                else:
                    issues.append({"reason": "incomplete_record", "detail": raw[:40]})
                    i += 1
                    continue
            elif not raw.startswith("1 ") and not raw.startswith("2 "):
                name = raw[:24].strip() or "UNKNOWN"
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("1 "):
                    line1 = lines[i + 1].strip()
                    if i + 2 < len(lines) and lines[i + 2].strip().startswith("2 "):
                        line2 = lines[i + 2].strip()
                        i += 3
                    else:
                        issues.append({"reason": "incomplete_record", "detail": name})
                        i += 2
                        continue
                else:
                    issues.append({"reason": "missing_tle_after_name", "detail": name})
                    i += 1
                    continue
            else:
                issues.append({"reason": "unexpected_line", "detail": raw[:40]})
                i += 1
                continue
            try:
                record = self.parse_pair(
                    line1,
                    line2,
                    name=name,
                    source=source,
                    retrieved_at=retrieved_at,
                    source_url=source_url,
                    from_cache=from_cache,
                    strict_checksum=strict_checksum,
                )
            except InvalidOrbitalRecordError as exc:
                issues.append({"reason": str(exc), "detail": name})
                continue
            key = record.catalog_id
            if key in seen:
                issues.append({"reason": "duplicate_catalog_id", "detail": key})
                records[seen[key]] = record
            else:
                seen[key] = len(records)
                records.append(record)
        return records, issues

    def parse_pair(
        self,
        line1: str,
        line2: str,
        *,
        name: str,
        source: str,
        retrieved_at: datetime,
        source_url: str | None = None,
        from_cache: bool = False,
        strict_checksum: bool = True,
    ) -> OrbitalRecord:
        line1 = line1.strip()
        line2 = line2.strip()
        messages: list[str] = []
        if len(line1) < 68 or len(line2) < 68:
            raise InvalidOrbitalRecordError("TLE lines must be at least 68 characters.")
        if len(line1) > 69:
            line1 = line1[:69]
        if len(line2) > 69:
            line2 = line2[:69]
        if len(line1) == 68:
            line1 = line1 + str(tle_checksum(line1.ljust(68)))
            messages.append("checksum_digit_appended")
        if len(line2) == 68:
            line2 = line2 + str(tle_checksum(line2.ljust(68)))
            messages.append("checksum_digit_appended")
        if not line1.startswith("1 "):
            raise InvalidOrbitalRecordError("Line 1 must start with '1 '.")
        if not line2.startswith("2 "):
            raise InvalidOrbitalRecordError("Line 2 must start with '2 '.")
        id1 = line1[2:7].strip()
        id2 = line2[2:7].strip()
        if not id1 or id1 != id2:
            raise InvalidOrbitalRecordError(
                f"Catalog identifiers do not match between TLE lines ({id1!r} vs {id2!r})."
            )
        try:
            cs1 = tle_checksum(line1[:68])
            cs2 = tle_checksum(line2[:68])
            given1 = int(line1[68])
            given2 = int(line2[68])
        except (ValueError, IndexError) as exc:
            raise InvalidOrbitalRecordError("Unable to read TLE checksum digits.") from exc
        if cs1 != given1 or cs2 != given2:
            msg = f"TLE checksum mismatch for catalog {id1}."
            if strict_checksum:
                raise TLEChecksumError(msg)
            messages.append(msg)
        epoch = parse_tle_epoch(line1)
        try:
            inclination = float(line2[8:16])
            raan = float(line2[17:25])
            ecc = float("0." + line2[26:33].replace(" ", "0"))
            argp = float(line2[34:42])
            ma = float(line2[43:51])
            mm = float(line2[52:63])
        except ValueError as exc:
            raise InvalidOrbitalRecordError("TLE numeric fields are malformed.") from exc
        if not all(map(_finite, (inclination, raan, ecc, argp, ma, mm))):
            raise InvalidOrbitalRecordError("TLE numeric fields contain non-finite values.")
        if ecc < 0 or ecc >= 1:
            messages.append("eccentricity_outside_typical_range")
        classification = line1[7:8].strip() or None
        intl = line1[9:17].strip() or None
        bstar = parse_tle_exp(line1[53:61])
        return OrbitalRecord(
            name=name.strip() or f"OBJECT {id1}",
            catalog_id=id1.lstrip("0") or "0",
            line1=line1,
            line2=line2,
            epoch_utc=epoch,
            retrieved_at=retrieved_at,
            source=source,
            source_url=source_url,
            data_format="TLE",
            validation_status="valid" if not messages else "valid_with_warnings",
            validation_messages=messages,
            classification=classification,
            classification_source="TLE column 8" if classification else None,
            from_cache=from_cache,
            international_designator=intl,
            mean_motion_rev_per_day=mm,
            eccentricity=ecc,
            inclination_deg=inclination,
            raan_deg=raan,
            arg_perigee_deg=argp,
            mean_anomaly_deg=ma,
            bstar=bstar,
        )


def tle_checksum(line: str) -> int:
    total = 0
    for char in line[:68]:
        if char.isdigit():
            total += int(char)
        elif char == "-":
            total += 1
    return total % 10


def parse_tle_epoch(line1: str) -> datetime:
    try:
        year_2 = int(line1[18:20])
        day_frac = float(line1[20:32])
    except ValueError as exc:
        raise InvalidOrbitalRecordError("TLE epoch field is malformed.") from exc
    year = 1900 + year_2 if year_2 >= 57 else 2000 + year_2
    if day_frac < 1 or day_frac >= 367:
        raise InvalidOrbitalRecordError("TLE epoch day-of-year is out of range.")
    return datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_frac - 1.0)


def parse_tle_exp(field: str) -> float | None:
    text = field.strip()
    if not text:
        return None
    try:
        if len(text) >= 2 and (text[-2] in "+-" or text[-1] in "+-"):
            # packed format: ±xxxxx±e
            sign = -1 if text[0] == "-" else 1
            body = text[1:] if text[0] in "+-" else text
            if "-" in body[1:]:
                mantissa, exp = body.rsplit("-", 1)
                exponent = -int(exp)
            elif "+" in body[1:]:
                mantissa, exp = body.rsplit("+", 1)
                exponent = int(exp)
            else:
                return float(text)
            return sign * float("0." + mantissa.replace(" ", "0")) * (10 ** exponent)
        return float(text)
    except ValueError:
        return None


def _finite(value: float) -> bool:
    return value == value and value not in (float("inf"), float("-inf"))


def records_by_query(records: Iterable[OrbitalRecord], query: str) -> list[OrbitalRecord]:
    q = query.strip().lower()
    if not q:
        return list(records)
    out = []
    for rec in records:
        if q in rec.name.lower() or q == rec.catalog_id.lower() or rec.catalog_id.lstrip("0") == q.lstrip("0"):
            out.append(rec)
    return out
