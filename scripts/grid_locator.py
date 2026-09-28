#!/usr/bin/env python3
"""Deterministic Maidenhead grid locator encoder/decoder.

This is an educational operator tool. It does not produce legal-to-transmit
verdicts, band permissions, or regulatory conclusions.
"""

from __future__ import annotations

import argparse
import json
import math
import re

LOCATOR_RE = re.compile(r"^[A-Ra-r]{2}(?:[0-9]{2}(?:[A-Xa-x]{2})?)?$")
VALID_PRECISIONS = {2, 4, 6}


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def maidenhead_encode(latitude: float, longitude: float, precision: int = 6) -> str:
    """Encode latitude/longitude as a 2, 4, or 6-character Maidenhead locator.

    Coordinates use half-open global bounds:
    -90 <= latitude < 90 and -180 <= longitude < 180.
    """
    lat = _number(latitude, "latitude")
    lon = _number(longitude, "longitude")
    if precision not in VALID_PRECISIONS:
        raise ValueError("precision must be one of 2, 4, 6")
    if not (-90.0 <= lat < 90.0):
        raise ValueError("latitude must satisfy -90 <= latitude < 90")
    if not (-180.0 <= lon < 180.0):
        raise ValueError("longitude must satisfy -180 <= longitude < 180")

    x = lon + 180.0
    y = lat + 90.0

    field_lon = min(17, int(math.floor(x / 20.0)))
    field_lat = min(17, int(math.floor(y / 10.0)))
    result = chr(ord("A") + field_lon) + chr(ord("A") + field_lat)

    if precision >= 4:
        x -= field_lon * 20.0
        y -= field_lat * 10.0
        square_lon = min(9, int(math.floor(x / 2.0)))
        square_lat = min(9, int(math.floor(y)))
        result += str(square_lon) + str(square_lat)

        if precision == 6:
            x -= square_lon * 2.0
            y -= square_lat
            subsquare_lon = min(23, int(math.floor(x * 12.0)))
            subsquare_lat = min(23, int(math.floor(y * 24.0)))
            result += chr(ord("a") + subsquare_lon) + chr(ord("a") + subsquare_lat)

    return result


def maidenhead_bounds(locator: str) -> dict:
    """Return the geographic cell bounds and center for a 2/4/6-char locator."""
    if not isinstance(locator, str):
        raise ValueError("locator must be a string")
    loc = locator.strip()
    if len(loc) not in VALID_PRECISIONS or not LOCATOR_RE.fullmatch(loc):
        raise ValueError("locator must be 2, 4, or 6 chars in Maidenhead form")

    field_lon = ord(loc[0].upper()) - ord("A")
    field_lat = ord(loc[1].upper()) - ord("A")
    lon_min = -180.0 + field_lon * 20.0
    lat_min = -90.0 + field_lat * 10.0
    lon_size = 20.0
    lat_size = 10.0

    if len(loc) >= 4:
        lon_min += int(loc[2]) * 2.0
        lat_min += int(loc[3])
        lon_size = 2.0
        lat_size = 1.0

    if len(loc) == 6:
        sub_lon = ord(loc[4].lower()) - ord("a")
        sub_lat = ord(loc[5].lower()) - ord("a")
        lon_size = 2.0 / 24.0
        lat_size = 1.0 / 24.0
        lon_min += sub_lon * lon_size
        lat_min += sub_lat * lat_size

    lon_max = lon_min + lon_size
    lat_max = lat_min + lat_size
    return {
        "locator": (
            loc[:2].upper()
            + (loc[2:4] if len(loc) >= 4 else "")
            + (loc[4:6].lower() if len(loc) == 6 else "")
        ),
        "longitude_min": lon_min,
        "longitude_max": lon_max,
        "latitude_min": lat_min,
        "latitude_max": lat_max,
        "center_longitude": (lon_min + lon_max) / 2.0,
        "center_latitude": (lat_min + lat_max) / 2.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Educational Maidenhead grid locator tool; no transmit/legal verdicts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    encode = sub.add_parser("encode", help="Convert coordinates to a locator")
    encode.add_argument("--lat", required=True, type=float)
    encode.add_argument("--lon", required=True, type=float)
    encode.add_argument("--precision", type=int, choices=sorted(VALID_PRECISIONS), default=6)

    bounds = sub.add_parser("bounds", help="Show the geographic cell for a locator")
    bounds.add_argument("locator")

    args = parser.parse_args()
    if args.command == "encode":
        payload = {
            "latitude": args.lat,
            "longitude": args.lon,
            "precision": args.precision,
            "locator": maidenhead_encode(args.lat, args.lon, args.precision),
            "legal_verdict": None,
        }
    else:
        payload = maidenhead_bounds(args.locator)
        payload["legal_verdict"] = None

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
