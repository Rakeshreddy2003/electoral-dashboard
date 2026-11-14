"""
One-off backfill: populates SurveyResponse.ac_no for rows synced before that
column existed (the sync job only sets it going forward, see app/sync/
odk_sync.py). Safe to re-run -- it's a pure recompute from assembly_constituency,
not additive.

Run from backend/ with:
    python -m etl.backfill_survey_ac_no
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.constituencies_config import ac_to_no  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import SurveyResponse  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        rows = db.query(SurveyResponse).all()
        updated = 0
        unmatched = set()
        for r in rows:
            ac_no = ac_to_no(r.assembly_constituency)
            if ac_no != r.ac_no:
                r.ac_no = ac_no
                updated += 1
            if r.assembly_constituency and ac_no is None:
                unmatched.add(r.assembly_constituency)
        db.commit()
        print(f"Backfilled ac_no on {updated}/{len(rows)} rows.")
        if unmatched:
            print(f"WARNING: {len(unmatched)} assembly_constituency value(s) had no ac_no match: {sorted(unmatched)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
