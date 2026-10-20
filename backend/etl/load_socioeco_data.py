"""
One-off loader: reads data/socioeco/ (a copy of the pre-survey baseline
socio-economic export -- see data/socioeco/00_README.txt and
app/models.py::SecretariatProfile's docstring for what this is and why it's
not stale data) and loads secretariat-level rows into `secretariat_profiles`.

Run from backend/ with:
    python -m etl.load_socioeco_data

04_secretariat_master.csv carries population/households/BPL-proxy;
06_secretariat_caste_pct.csv and 07_secretariat_religion_pct.csv carry caste/
religion head counts, joined in by secretariat_code. AC names here use the
same "(ST)"/"(St)" reservation suffix as the MATData export (see
constituencies_config.py) -- stripped the same way.
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.constituencies_config import ac_to_pc  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import SecretariatProfile  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "socioeco"
AC_SUFFIX_RE = re.compile(r"\s*\([A-Za-z]+\)\s*$")

# This source spells 4 of our 35 ACs differently from our canonical
# (ECI-matching) names in constituencies_config.py -- found by checking which
# AC names failed ac_to_pc() during a real load (386 secretariats would have
# been silently dropped otherwise).
AC_NAME_ALIASES = {
    "Elamanchili": "Yelamanchili",
    "Payakaraopeta": "Payakaraopet",
    "Bheemili": "Bhimili",
    "Cheepurupalli": "Cheepurupalle",
}

CASTE_COLUMNS = ["Kamma", "Kapu_BC", "Muslim_BC", "OC_Forward", "Other_BC", "Reddy", "SC", "ST", "Unknown"]
RELIGION_COLUMNS = ["Buddhist", "Christian", "Hindu", "Jain", "Muslim", "Other Religious Communities", "Sikh", "Unknown"]


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


def main() -> None:
    if not DATA_DIR.exists():
        raise SystemExit(f"{DATA_DIR} not found")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        caste_by_secretariat = {r["secretariat_code"]: r for r in _load_csv(DATA_DIR / "06_secretariat_caste_pct.csv")}
        religion_by_secretariat = {r["secretariat_code"]: r for r in _load_csv(DATA_DIR / "07_secretariat_religion_pct.csv")}

        db.query(SecretariatProfile).delete()

        loaded = 0
        skipped_ac = 0
        for row in _load_csv(DATA_DIR / "04_secretariat_master.csv"):
            ac_name = AC_SUFFIX_RE.sub("", row["ac_name"]).strip()
            ac_name = AC_NAME_ALIASES.get(ac_name, ac_name)
            if ac_to_pc(ac_name) is None:
                skipped_ac += 1
                continue

            caste_row = caste_by_secretariat.get(row["secretariat_code"])
            caste_counts = None
            caste_total = None
            if caste_row:
                caste_counts = {c: _to_int(caste_row.get(c)) or 0 for c in CASTE_COLUMNS}
                caste_total = _to_int(caste_row.get("persons_total"))

            religion_row = religion_by_secretariat.get(row["secretariat_code"])
            religion_counts = None
            religion_total = None
            if religion_row:
                religion_counts = {c: _to_int(religion_row.get(c)) or 0 for c in RELIGION_COLUMNS}
                religion_total = _to_int(religion_row.get("persons_total"))

            db.add(
                SecretariatProfile(
                    pc_name=row["pc_name"],
                    ac_no=_to_int(row.get("ac_no")),
                    ac_name=ac_name,
                    mandal_name=row.get("mandal_name") or None,
                    secretariat_code=row.get("secretariat_code") or None,
                    secretariat_name=row.get("secretariat_name") or None,
                    rural_urban=row.get("rural_urban") or None,
                    households=_to_int(row.get("households")),
                    population=_to_int(row.get("population")),
                    pct_bpl_proxy_hh=_to_float(row.get("pct_bpl_proxy_hh")),
                    avg_electricity_bill_inr=_to_float(row.get("avg_electricity_bill_inr")),
                    latitude=_to_float(row.get("latitude")),
                    longitude=_to_float(row.get("longitude")),
                    caste_counts_json=json.dumps(caste_counts) if caste_counts else None,
                    caste_persons_total=caste_total,
                    religion_counts_json=json.dumps(religion_counts) if religion_counts else None,
                    religion_persons_total=religion_total,
                )
            )
            loaded += 1

        db.commit()
        print(f"Loaded {loaded} secretariat profiles for the 5 PCs / 35 ACs ({skipped_ac} rows outside our 35 ACs skipped).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
