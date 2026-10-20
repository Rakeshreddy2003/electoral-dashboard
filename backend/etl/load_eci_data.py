"""
One-off loader: reads the Andhra Pradesh MATData retro export and loads
both assembly (AE/AC) and parliamentary/Lok Sabha (GE/PC) candidate-level
results for the 5 PCs / 35 ACs this survey covers into the `eci_results`
table, for the Retrospective page.

Run from backend/ with:
    python -m etl.load_eci_data

Reads from dashboard/data/retro/ -- a copy of files from the sibling eci/
project's andhra_pradesh_retro export, kept inside this project so the
dashboard repo is self-contained. That copy is a point-in-time snapshot: if
eci/andhra_pradesh_retro is ever regenerated, re-copy the relevant files here
to pick up new elections.

Two data quality notes from inspecting the source:
  - elections.csv's own total_electors/total_votes fields are unreliable for
    some rows (seen: a 2024 AE row where total_electors == total_votes,
    implying impossible 100% turnout). The separately-computed
    matdata_exports/constituency_master_*.csv files have correct electors/
    turnout per constituency/year, so those are used for electors/turnout
    instead of the per-candidate-row fields.
  - The PC-level constituency_master_PC_*.csv files have duplicate rows per
    constituency (the export fans out by district, and a PC spans several
    districts) -- deduplicated here by (constituencyId, year).
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.constituencies_config import PC_TO_ACS, ac_to_pc  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import EciResult  # noqa: E402

RETRO_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "retro"
STATE_ID = "2"  # Andhra Pradesh, per andhra_pradesh_retro/metadata.json
YEARS = [2009, 2014, 2019, 2024]

# pcs.csv spells Araku's PC name in caps; the other 4 already match our
# canonical constituencies_config keys exactly.
PC_NAME_NORMALIZE = {"ARAKU": "Araku"}

AC_SUFFIX_RE = re.compile(r"\s*\([A-Z]+\)\s*$")  # strips " (ST)" / " (SC)" reservation suffixes


def _to_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _load_constituency_master(level: str, election_type: str) -> dict[tuple[str, int], dict]:
    """Returns {(constituencyId, year): row} for the given level/type across YEARS, deduplicated."""
    out: dict[tuple[str, int], dict] = {}
    for year in YEARS:
        path = RETRO_DIR / "matdata_exports" / f"constituency_master_{level}_{year}_{election_type}.csv"
        if not path.exists():
            continue
        for row in _load_csv(path):
            key = (row["constituencyId"], year)
            out.setdefault(key, row)  # first occurrence wins, drops the duplicate fan-out rows
    return out


def main() -> None:
    if not RETRO_DIR.exists():
        raise SystemExit(f"Retro data dir not found at {RETRO_DIR}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        parties = {r["id"]: r["party_code"] for r in _load_csv(RETRO_DIR / "parties_referenced.csv")}
        acs_by_id = {r["id"]: r for r in _load_csv(RETRO_DIR / "acs.csv")}
        pcs_by_id = {r["id"]: r for r in _load_csv(RETRO_DIR / "pcs.csv")}

        ac_master = _load_constituency_master("AC", "AE")
        pc_master = _load_constituency_master("PC", "GE")

        db.query(EciResult).delete()  # full reload each run -- small dataset, avoids dedup-key complexity

        loaded = 0
        for row in _load_csv(RETRO_DIR / "elections.csv"):
            if row["state_id"] != STATE_ID:
                continue
            if row["bypoll"] == "1":
                continue  # a by-election would duplicate the (constituency, year) key the timeline/winners views assume

            year = _to_int(row["election_year"])
            if year not in YEARS:
                continue

            election_type = row["election_type"]
            level = row["ac_or_pc"]

            if level == "AC" and election_type == "AE":
                ac = acs_by_id.get(row["ac_or_pc_id"])
                if not ac:
                    continue
                ac_name = AC_SUFFIX_RE.sub("", ac["ac_name"]).strip()
                pc_name = ac_to_pc(ac_name)
                if pc_name is None:
                    continue  # not one of our 35 ACs
                constituency_name = ac_name
                constituency_no = _to_int(ac["ac_no"])
                master_row = ac_master.get((row["ac_or_pc_id"], year))

            elif level == "PC" and election_type == "GE":
                pc = pcs_by_id.get(row["ac_or_pc_id"])
                if not pc:
                    continue
                pc_name = PC_NAME_NORMALIZE.get(pc["pc_name"].strip(), pc["pc_name"].strip())
                if pc_name not in PC_TO_ACS:
                    continue  # not one of our 5 PCs
                constituency_name = pc_name
                constituency_no = _to_int(pc["pc_no"])
                master_row = pc_master.get((row["ac_or_pc_id"], year))

            else:
                continue  # skip GE/AC segment breakdowns and PC/AE (not meaningful) for this iteration

            total_electors = _to_int(master_row["totalElectors"]) if master_row else None
            total_votes = _to_int(master_row["totalVotes"]) if master_row else None
            turnout_percentage = _to_float(master_row["turnoutPct"]) if master_row else None

            db.add(
                EciResult(
                    election_type=election_type,
                    level=level,
                    year=year,
                    constituency_no=constituency_no,
                    constituency_name=constituency_name,
                    pc_name=pc_name,
                    candidate_name=row["candidate"],
                    party=parties.get(row["party_id"]),
                    position=_to_int(row["rank"]),
                    votes=_to_int(row["votes"]),
                    vote_share_percentage=_to_float(row["voteshare"]),
                    margin=_to_int(row["margin"]),
                    margin_percentage=_to_float(row["margin_percent"]),
                    total_electors=total_electors,
                    total_votes=total_votes,
                    turnout_percentage=turnout_percentage,
                )
            )
            loaded += 1

            if loaded % 500 == 0:
                db.commit()

        db.commit()
        print(f"Loaded {loaded} candidate rows across AC/AE and PC/GE for the 5 PCs / 35 ACs, years {YEARS}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
