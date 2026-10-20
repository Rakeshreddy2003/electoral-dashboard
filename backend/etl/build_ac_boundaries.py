"""
One-off: converts dashboard/data/retro/ac_geom.csv (MySQL-exported WKB, with
each cell holding the Python repr of the raw bytes -- `b'\\xe6\\x10...'` as
literal text, not actual binary) into a GeoJSON FeatureCollection of the 35
AC boundaries this survey covers, for the Responses page map.

Run from backend/ with:
    python -m etl.build_ac_boundaries

Writes to ../frontend/public/ac_boundaries.geojson (a static asset Vite
copies as-is; the frontend fetches it at runtime, see MapView.tsx). Re-run
whenever ac_geom.csv is refreshed from eci/andhra_pradesh_retro.

Each cell's first 4 bytes are a little-endian SRID (4326 here), and the rest
is standard WKB -- strip the SRID prefix before handing it to shapely.
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
OUT_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "ac_boundaries.geojson"

AC_SUFFIX_RE = re.compile(r"\s*\([A-Z]+\)\s*$")


def main() -> None:
    features = []

    # ac_geom.csv keys off acId (acmap's own id), not acs.csv's id -- join via
    # acs.csv's acmap_acId column instead.
    acmap_id_to_name = {}
    with open(RETRO_DIR / "acs.csv", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            name = AC_SUFFIX_RE.sub("", row["ac_name"]).strip()
            pc_name = ac_to_pc(name)
            if pc_name is not None and row.get("acmap_acId"):
                acmap_id_to_name[row["acmap_acId"]] = (name, pc_name)

    with open(RETRO_DIR / "ac_geom.csv", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            match = acmap_id_to_name.get(row["acId"])
            if match is None:
                continue
            ac_name, pc_name = match

            raw = ast.literal_eval(row["geom"])  # text "b'\\x..'" -> real bytes
            geom = wkb.loads(raw[4:])  # strip the 4-byte little-endian SRID prefix

            features.append(
                {
                    "type": "Feature",
                    "properties": {"ac_name": ac_name, "pc_name": pc_name},
                    "geometry": mapping(geom),
                }
            )

    geojson = {"type": "FeatureCollection", "features": features}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(geojson), encoding="utf-8")
    print(f"Wrote {len(features)} AC boundaries to {OUT_PATH}")


if __name__ == "__main__":
    main()
