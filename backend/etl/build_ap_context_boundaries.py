"""
One-off: writes the OTHER ~140 Andhra Pradesh assembly constituencies (every
AC in data/retro/ac_geom.csv that isn't one of the 35 this survey covers) as
a separate, lightweight GeoJSON file -- purely for geographic context on the
Retrospective page's map (a grey, non-interactive backdrop showing the rest
of the state around the interactive North Andhra region), not for any
interactive drill-down. Keeps ac_boundaries.geojson (the 35 in-scope ACs,
built by build_ac_boundaries.py) untouched and unambiguous -- that file is
still the only one any interactive map logic reads.

Run from backend/ with:
    python -m etl.build_ap_context_boundaries

Writes to ../frontend/public/ap_context_boundaries.geojson. Re-run whenever
ac_geom.csv is refreshed from eci/andhra_pradesh_retro.
"""

import ast
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shapely import wkb  # noqa: E402
from shapely.geometry import mapping  # noqa: E402

from app.constituencies_config import ac_to_pc  # noqa: E402

RETRO_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "retro"
OUT_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "ap_context_boundaries.geojson"

AC_SUFFIX_RE = re.compile(r"\s*\([A-Z]+\)\s*$")


def main() -> None:
    features = []

    acmap_id_to_name = {}
    with open(RETRO_DIR / "acs.csv", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            name = AC_SUFFIX_RE.sub("", row["ac_name"]).strip()
            if row.get("acmap_acId"):
                acmap_id_to_name[row["acmap_acId"]] = name

    with open(RETRO_DIR / "ac_geom.csv", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            ac_name = acmap_id_to_name.get(row["acId"])
            if ac_name is None or ac_to_pc(ac_name) is not None:
                continue  # one of our 35 -- already covered by ac_boundaries.geojson

            raw = ast.literal_eval(row["geom"])
            geom = wkb.loads(raw[4:])  # strip the 4-byte little-endian SRID prefix

            features.append({"type": "Feature", "properties": {"ac_name": ac_name}, "geometry": mapping(geom)})

    geojson = {"type": "FeatureCollection", "features": features}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(geojson), encoding="utf-8")
    print(f"Wrote {len(features)} context AC boundaries to {OUT_PATH}")


if __name__ == "__main__":
    main()
