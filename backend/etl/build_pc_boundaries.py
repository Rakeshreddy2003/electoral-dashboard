"""
One-off: unions each PC's 7 AC polygons (from ac_boundaries.geojson, already
built by build_ac_boundaries.py) into a single PC boundary, for the
AP-wide/zoomed-out level of the Retrospective page map.

Run from backend/ with:
    python -m etl.build_pc_boundaries

Requires ac_boundaries.geojson to already exist (run build_ac_boundaries.py
first). Writes to ../frontend/public/pc_boundaries.geojson.
"""

import json
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

AC_BOUNDARIES_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "ac_boundaries.geojson"
OUT_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "pc_boundaries.geojson"


def main() -> None:
    if not AC_BOUNDARIES_PATH.exists():
        raise SystemExit(f"{AC_BOUNDARIES_PATH} not found -- run build_ac_boundaries.py first")

    ac_geojson = json.loads(AC_BOUNDARIES_PATH.read_text(encoding="utf-8"))

    by_pc: dict[str, list] = {}
    for feature in ac_geojson["features"]:
        pc_name = feature["properties"]["pc_name"]
        by_pc.setdefault(pc_name, []).append(shape(feature["geometry"]))

    features = []
    for pc_name, polygons in by_pc.items():
        merged = unary_union(polygons)
        features.append({"type": "Feature", "properties": {"pc_name": pc_name, "ac_count": len(polygons)}, "geometry": mapping(merged)})

    geojson = {"type": "FeatureCollection", "features": features}
    OUT_PATH.write_text(json.dumps(geojson), encoding="utf-8")
    print(f"Wrote {len(features)} PC boundaries to {OUT_PATH}")


if __name__ == "__main__":
    main()
