from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

import io
import json
import re

import pandas as pd

from app.constituencies_config import PC_TO_ACS, ac_to_no, ac_to_pc, is_configured
from app.database import get_db
from app.deps import require_any
from app.models import EciResult, SecretariatProfile

router = APIRouter(prefix="/api/retrospective", tags=["retrospective"])


@router.get("/config")
def config(_=Depends(require_any)):
    return {"pc_to_acs_configured": is_configured(), "pc_names": list(PC_TO_ACS.keys())}


@router.get("/acs")
def list_acs(_=Depends(require_any), db: Session = Depends(get_db)):
    rows = db.query(EciResult.constituency_name).filter(EciResult.level == "AC").distinct().order_by(EciResult.constituency_name).all()
    acs = [r[0] for r in rows]
    return [{"ac_name": ac, "ac_no": ac_to_no(ac), "pc_name": ac_to_pc(ac)} for ac in acs]


@router.get("/results")
def results(
    ac_name: str | None = Query(default=None),
    pc_name: str | None = Query(default=None),
    year: int | None = Query(default=None),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """Assembly (AE) election results, per AC -- the state assembly seat, not the Lok Sabha seat."""
    q = db.query(EciResult).filter(EciResult.level == "AC")
    if ac_name:
        q = q.filter(EciResult.constituency_name == ac_name)
    elif pc_name:
        q = q.filter(EciResult.pc_name == pc_name)
    if year:
        q = q.filter(EciResult.year == year)
    q = q.order_by(EciResult.year.desc(), EciResult.constituency_name, EciResult.position)

    return [
        {
            "year": r.year,
            "ac_name": r.constituency_name,
            "candidate_name": r.candidate_name,
            "party": r.party,
            "position": r.position,
            "vote_share_percentage": r.vote_share_percentage,
            "margin_percentage": r.margin_percentage,
            "turnout_percentage": r.turnout_percentage,
            "total_electors": r.total_electors,
        }
        for r in q.all()
    ]


@router.get("/winners-by-year")
def winners_by_year(
    ac_name: str | None = Query(default=None),
    pc_name: str | None = Query(default=None),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """One row per AC per year for the winning candidate (position == 1) of the assembly (AE) seat."""
    q = db.query(EciResult).filter(EciResult.level == "AC", EciResult.position == 1)
    if ac_name:
        q = q.filter(EciResult.constituency_name == ac_name)
    elif pc_name:
        q = q.filter(EciResult.pc_name == pc_name)
    q = q.order_by(EciResult.constituency_name, EciResult.year)
    return [
        {
            "year": r.year,
            "ac_name": r.constituency_name,
            "candidate_name": r.candidate_name,
            "party": r.party,
            "vote_share_percentage": r.vote_share_percentage,
            "turnout_percentage": r.turnout_percentage,
        }
        for r in q.all()
    ]


@router.get("/turnout-trend")
def turnout_trend(pc_name: str | None = Query(default=None), _=Depends(require_any), db: Session = Depends(get_db)):
    """Average AC-level (assembly) turnout by year, optionally scoped to one PC's 7 ACs."""
    q = db.query(EciResult.year, func.avg(EciResult.turnout_percentage)).filter(EciResult.level == "AC")
    if pc_name:
        q = q.filter(EciResult.pc_name == pc_name)
    rows = q.group_by(EciResult.year).order_by(EciResult.year).all()
    return [{"year": y, "avg_turnout_percentage": round(t, 2) if t else None} for y, t in rows]


@router.get("/pc-history")
def pc_history(pc_name: str = Query(...), _=Depends(require_any), db: Session = Depends(get_db)):
    """
    The actual Lok Sabha (GE) results for one parliamentary constituency,
    one row per candidate per election year -- this is the real MP election,
    not an aggregate of the 7 assembly segments.
    """
    q = (
        db.query(EciResult)
        .filter(EciResult.level == "PC", EciResult.pc_name == pc_name)
        .order_by(EciResult.year.desc(), EciResult.position)
    )
    return [
        {
            "year": r.year,
            "candidate_name": r.candidate_name,
            "party": r.party,
            "position": r.position,
            "votes": r.votes,
            "vote_share_percentage": r.vote_share_percentage,
            "turnout_percentage": r.turnout_percentage,
            "total_electors": r.total_electors,
        }
        for r in q.all()
    ]


@router.get("/ac-detail")
def ac_detail(ac_name: str = Query(...), _=Depends(require_any), db: Session = Depends(get_db)):
    """
    Everything for one AC's election timeline: the AE winner per year, the
    vote-share swing between the 2 most recent AE years (by party, across
    all candidates those years -- not just the winner), the owning PC's
    latest Lok Sabha (GE) result, and an AE-vs-GE elector-roll comparison.
    """
    pc_name = ac_to_pc(ac_name)

    ae_rows = (
        db.query(EciResult)
        .filter(EciResult.level == "AC", EciResult.constituency_name == ac_name)
        .order_by(EciResult.year, EciResult.position)
        .all()
    )
    by_year: dict[int, list[EciResult]] = {}
    for r in ae_rows:
        by_year.setdefault(r.year, []).append(r)

    timeline = []
    for year in sorted(by_year):
        winner = next((c for c in by_year[year] if c.position == 1), None)
        if winner is None:
            continue
        timeline.append(
            {
                "year": year,
                "winner_name": winner.candidate_name,
                "party": winner.party,
                "vote_share_percentage": winner.vote_share_percentage,
                "margin": winner.margin,
                "margin_percentage": winner.margin_percentage,
                "turnout_percentage": winner.turnout_percentage,
                "total_electors": winner.total_electors,
                "candidate_count": len(by_year[year]),
            }
        )

    swing = None
    years_sorted = sorted(by_year)
    if len(years_sorted) >= 2:
        y_prev, y_last = years_sorted[-2], years_sorted[-1]
        shares_prev = {c.party: c.vote_share_percentage for c in by_year[y_prev] if c.party}
        shares_last = {c.party: c.vote_share_percentage for c in by_year[y_last] if c.party}
        parties = sorted(set(shares_prev) | set(shares_last), key=lambda p: -(shares_last.get(p) or 0.0))
        swing = {
            "from_year": y_prev,
            "to_year": y_last,
            "by_party": [
                {"party": p, "swing_pp": round((shares_last.get(p) or 0.0) - (shares_prev.get(p) or 0.0), 1)}
                for p in parties
            ],
        }

    pc_latest = None
    if pc_name:
        pc_winner = (
            db.query(EciResult)
            .filter(EciResult.level == "PC", EciResult.pc_name == pc_name, EciResult.position == 1)
            .order_by(EciResult.year.desc())
            .first()
        )
        if pc_winner:
            pc_latest = {
                "year": pc_winner.year,
                "candidate_name": pc_winner.candidate_name,
                "party": pc_winner.party,
                "vote_share_percentage": pc_winner.vote_share_percentage,
                "turnout_percentage": pc_winner.turnout_percentage,
                "total_electors": pc_winner.total_electors,
            }

    electors_comparison = None
    if timeline and pc_latest:
        electors_comparison = {
            "ae_year": timeline[-1]["year"],
            "ae_electors": timeline[-1]["total_electors"],
            "ge_year": pc_latest["year"],
            "ge_electors": pc_latest["total_electors"],
        }

    return {
        "ac_name": ac_name,
        "pc_name": pc_name,
        "timeline": timeline,
        "swing": swing,
        "pc_latest": pc_latest,
        "electors_comparison": electors_comparison,
    }


@router.get("/close-contests")
def close_contests(
    pc_name: str | None = Query(default=None),
    year: int | None = Query(default=None),
    max_margin_pct: float = Query(default=5.0),
    party: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """
    AC-level (assembly) races, closest margin first. Thresholded on
    margin_percentage rather than raw vote margin, since our 35 ACs vary
    widely in elector-roll size and a percentage is comparable across them.
    """
    q = db.query(EciResult).filter(EciResult.level == "AC", EciResult.election_type == "AE")
    if pc_name:
        q = q.filter(EciResult.pc_name == pc_name)
    if year:
        q = q.filter(EciResult.year == year)
    if search:
        q = q.filter(EciResult.constituency_name.ilike(f"%{search}%"))
    rows = q.order_by(EciResult.constituency_name, EciResult.year, EciResult.position).all()

    by_race: dict[tuple[str, int], list[EciResult]] = {}
    for r in rows:
        by_race.setdefault((r.constituency_name, r.year), []).append(r)

    results = []
    for (ac_name, yr), candidates in by_race.items():
        winner = next((c for c in candidates if c.position == 1), None)
        runner_up = next((c for c in candidates if c.position == 2), None)
        if winner is None or winner.margin_percentage is None or winner.margin_percentage > max_margin_pct:
            continue
        if party and winner.party != party:
            continue
        results.append(
            {
                "ac_name": ac_name,
                "pc_name": winner.pc_name,
                "year": yr,
                "winner_name": winner.candidate_name,
                "winner_party": winner.party,
                "runner_up_name": runner_up.candidate_name if runner_up else None,
                "runner_up_party": runner_up.party if runner_up else None,
                "margin": winner.margin,
                "margin_percentage": winner.margin_percentage,
            }
        )

    results.sort(key=lambda r: r["margin_percentage"])
    return results


@router.get("/ap-overview")
def ap_overview(_=Depends(require_any), db: Session = Depends(get_db)):
    """
    One-shot payload for the AP-wide (all 5 PCs) map: the latest AE winner
    per AC and latest GE winner per PC, for instant hover tooltips without a
    per-hover API round trip.
    """
    ac_rows = (
        db.query(EciResult)
        .filter(EciResult.level == "AC", EciResult.position == 1)
        .order_by(EciResult.constituency_name, EciResult.year.desc())
        .all()
    )
    ac_latest: dict[str, EciResult] = {}
    for r in ac_rows:
        ac_latest.setdefault(r.constituency_name, r)

    pc_rows = (
        db.query(EciResult)
        .filter(EciResult.level == "PC", EciResult.position == 1)
        .order_by(EciResult.pc_name, EciResult.year.desc())
        .all()
    )
    pc_latest: dict[str, EciResult] = {}
    for r in pc_rows:
        pc_latest.setdefault(r.pc_name, r)

    return {
        "acs": [
            {
                "ac_name": name,
                "pc_name": r.pc_name,
                "latest_year": r.year,
                "winner_name": r.candidate_name,
                "party": r.party,
                "vote_share_percentage": r.vote_share_percentage,
                "margin_percentage": r.margin_percentage,
                "turnout_percentage": r.turnout_percentage,
            }
            for name, r in ac_latest.items()
        ],
        "pcs": [
            {
                "pc_name": name,
                "latest_year": r.year,
                "winner_name": r.candidate_name,
                "party": r.party,
                "vote_share_percentage": r.vote_share_percentage,
                "turnout_percentage": r.turnout_percentage,
            }
            for name, r in pc_latest.items()
        ],
    }


@router.get("/top-candidates")
def top_candidates(
    ac_name: str | None = Query(default=None),
    pc_name: str | None = Query(default=None),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """Top 3 finishers per election year for one AC (assembly) or PC (Lok Sabha) seat."""
    if ac_name:
        q = db.query(EciResult).filter(EciResult.level == "AC", EciResult.constituency_name == ac_name)
    elif pc_name:
        q = db.query(EciResult).filter(EciResult.level == "PC", EciResult.pc_name == pc_name)
    else:
        return []
    q = q.filter(EciResult.position <= 3).order_by(EciResult.year.desc(), EciResult.position)

    by_year: dict[int, list] = {}
    for r in q.all():
        by_year.setdefault(r.year, []).append(
            {
                "position": r.position,
                "candidate_name": r.candidate_name,
                "party": r.party,
                "votes": r.votes,
                "vote_share_percentage": r.vote_share_percentage,
            }
        )
    return [{"year": year, "candidates": cands} for year, cands in sorted(by_year.items(), reverse=True)]


@router.get("/demographics")
def demographics(
    ac_name: str | None = Query(default=None),
    pc_name: str | None = Query(default=None),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """
    Pre-survey baseline socio-economic profile (population, households, BPL
    proxy, caste/religion composition), aggregated from secretariat-level
    rows by summing raw head counts (not averaging percentages). See
    SecretariatProfile's docstring for provenance and the caveat that the
    BPL proxy predates AP's 2024 change of government.
    """
    # No ac_name/pc_name -- aggregate across every secretariat (all 5 PCs),
    # so the overview page can show a region-wide socio-economic baseline
    # too, not just once a PC or AC is picked.
    q = db.query(SecretariatProfile)
    if ac_name:
        q = q.filter(SecretariatProfile.ac_name == ac_name)
    elif pc_name:
        q = q.filter(SecretariatProfile.pc_name == pc_name)
    rows = q.all()
    if not rows:
        return None

    total_population = sum(r.population or 0 for r in rows)
    total_households = sum(r.households or 0 for r in rows)
    bpl_households = sum(round((r.pct_bpl_proxy_hh or 0) / 100 * (r.households or 0)) for r in rows)

    caste_totals: dict[str, int] = {}
    caste_denominator = 0
    religion_totals: dict[str, int] = {}
    religion_denominator = 0
    for r in rows:
        if r.caste_counts_json:
            for k, v in json.loads(r.caste_counts_json).items():
                caste_totals[k] = caste_totals.get(k, 0) + v
            caste_denominator += r.caste_persons_total or 0
        if r.religion_counts_json:
            for k, v in json.loads(r.religion_counts_json).items():
                religion_totals[k] = religion_totals.get(k, 0) + v
            religion_denominator += r.religion_persons_total or 0

    def _pct_breakdown(totals: dict[str, int], denominator: int) -> list[dict]:
        if not denominator:
            return []
        return sorted(
            ({"name": k, "count": v, "pct": round(v / denominator * 100, 1)} for k, v in totals.items()),
            key=lambda d: -d["count"],
        )

    return {
        "secretariat_count": len(rows),
        "population": total_population,
        "households": total_households,
        "pct_bpl_proxy_hh": round(bpl_households / total_households * 100, 1) if total_households else None,
        "caste_breakdown": _pct_breakdown(caste_totals, caste_denominator),
        "religion_breakdown": _pct_breakdown(religion_totals, religion_denominator),
    }


_RESULT_COLUMNS = (
    "year",
    "constituency_name",
    "pc_name",
    "candidate_name",
    "party",
    "position",
    "votes",
    "vote_share_percentage",
    "margin",
    "margin_percentage",
    "turnout_percentage",
    "total_electors",
    "total_votes",
)


def _results_to_df(rows: list[EciResult]) -> pd.DataFrame:
    return pd.DataFrame([{c: getattr(r, c) for c in _RESULT_COLUMNS} for r in rows])


def _safe_sheet_name(name: str) -> str:
    """Excel sheet names: <=31 chars, no \\/?*[]: characters."""
    return re.sub(r"[\\/?*\[\]:]", " ", name)[:31]


@router.get("/export.xlsx")
def export_xlsx(
    ac_name: str | None = Query(default=None),
    pc_name: str | None = Query(default=None),
    scope: str = Query(default="both", pattern="^(ae|ge|both)$"),
    years: list[int] | None = Query(default=None),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """
    Download retrospective election results as an .xlsx workbook: one sheet
    per constituency rather than one flat table, so a reader isn't stuck
    filtering a single sheet by hand. Scoped the same way the page itself
    is -- to one AC (plus its owning PC's Lok Sabha result), to one PC (plus
    every assembly segment under it), or to all of North Andhra when
    neither is picked -- and to AE (assembly), GE (Lok Sabha), or both
    levels via `scope`.
    """

    def ae_rows(constituency_name: str | None = None, pc: str | None = None) -> list[EciResult]:
        q = db.query(EciResult).filter(EciResult.level == "AC")
        if constituency_name:
            q = q.filter(EciResult.constituency_name == constituency_name)
        elif pc:
            q = q.filter(EciResult.pc_name == pc)
        if years:
            q = q.filter(EciResult.year.in_(years))
        return q.order_by(EciResult.constituency_name, EciResult.year.desc(), EciResult.position).all()

    def ge_rows(pc: str | None = None) -> list[EciResult]:
        q = db.query(EciResult).filter(EciResult.level == "PC")
        if pc:
            q = q.filter(EciResult.pc_name == pc)
        if years:
            q = q.filter(EciResult.year.in_(years))
        return q.order_by(EciResult.pc_name, EciResult.year.desc(), EciResult.position).all()

    buf = io.BytesIO()
    sheet_count = 0
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if ac_name:
            owning_pc = pc_name or ac_to_pc(ac_name)
            if scope in ("ae", "both"):
                _results_to_df(ae_rows(constituency_name=ac_name)).to_excel(writer, sheet_name=_safe_sheet_name(f"{ac_name} (AE)"), index=False)
                sheet_count += 1
            if scope in ("ge", "both") and owning_pc:
                _results_to_df(ge_rows(pc=owning_pc)).to_excel(writer, sheet_name=_safe_sheet_name(f"{owning_pc} (GE)"), index=False)
                sheet_count += 1
        elif pc_name:
            if scope in ("ge", "both"):
                _results_to_df(ge_rows(pc=pc_name)).to_excel(writer, sheet_name=_safe_sheet_name(f"{pc_name} (GE)"), index=False)
                sheet_count += 1
            if scope in ("ae", "both"):
                for ac in PC_TO_ACS.get(pc_name, []):
                    df = _results_to_df(ae_rows(constituency_name=ac))
                    if df.empty:
                        continue
                    df.to_excel(writer, sheet_name=_safe_sheet_name(f"{ac} (AE)"), index=False)
                    sheet_count += 1
        else:
            if scope in ("ae", "both"):
                _results_to_df(ae_rows()).to_excel(writer, sheet_name="Assembly (AE)", index=False)
                sheet_count += 1
            if scope in ("ge", "both"):
                _results_to_df(ge_rows()).to_excel(writer, sheet_name="Lok Sabha (GE)", index=False)
                sheet_count += 1

        if sheet_count == 0:
            pd.DataFrame([{"message": "No data for the selected filters"}]).to_excel(writer, sheet_name="No data", index=False)

    buf.seek(0)
    filename = _safe_sheet_name(ac_name or pc_name or "north_andhra").replace(" ", "_") + "_retrospective.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
