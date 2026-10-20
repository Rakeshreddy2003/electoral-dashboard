import json
import statistics
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.choice_labels import EMPLOYMENT_ARRANGEMENT_LABELS, indicator_label, label_for
from app.database import get_db
from app.deps import require_any
from app.models import SurveyResponse

router = APIRouter(prefix="/api/responses", tags=["responses"])

# A respondent's overall earnings figure, picking whichever of the 3
# wage/salary/self-employed earnings categories is present for their module.
_EARNINGS_CATEGORIES = ("take_home_pay_wage", "take_home_salary_salaried", "earnings_self_employed")

# The 5 PCs' combined extent, generously padded -- one respondent's GPS
# landed in Austin, Texas (a device/testing error), which silently broke the
# map's auto-fit-bounds for every viewer since it had to zoom out to include
# a point on the wrong continent. Anything outside this box is dropped from
# map-points rather than plotted.
_LAT_RANGE = (16.5, 19.5)
_LON_RANGE = (80.5, 84.5)

# Fixed chronological order for the age_group chart -- GROUP BY has no
# notion of this, so the chart otherwise lists bands in whatever order
# Postgres happens to return distinct values.
_AGE_GROUP_ORDER = ["16_18", "19_25", "26_35", "36_50", "51_60", "61_plus"]

# Same reasoning as _AGE_GROUP_ORDER, for the education chart.
_EDUCATION_ORDER = [
    "no_formal_schooling",
    "primary",
    "middle",
    "secondary",
    "intermediate_diploma",
    "graduate",
    "postgraduate",
]

# Columns a chart bar click can filter by (cross-filtering -- click a bar in
# any chart and every chart on the page re-queries scoped to it). Keyed by
# the query param name the frontend sends.
_FILTERABLE_COLUMNS = {
    "pc_name": SurveyResponse.parliamentary_constituency,
    "ac_name": SurveyResponse.assembly_constituency,
    "occupation": SurveyResponse.occupation,
    "gender": SurveyResponse.gender,
    "age_group": SurveyResponse.age_group,
    "education": SurveyResponse.education,
    "employment_arrangement": SurveyResponse.employment_arrangement,
    "has_second_income": SurveyResponse.has_second_income,
    "top_priority_problem": SurveyResponse.top_priority_problem,
    "scheme_awareness": SurveyResponse.scheme_awareness,
    "healthcare_access": SurveyResponse.healthcare_access,
    "schooling_access": SurveyResponse.schooling_access,
    "emergency_line_usage": SurveyResponse.emergency_line_usage,
    "respondent_category": SurveyResponse.respondent_category,
}


class Filters:
    """Parses the cross-filter query params shared by every endpoint below."""

    def __init__(
        self,
        pc_name: str | None = Query(default=None),
        ac_name: str | None = Query(default=None),
        occupation: str | None = Query(default=None),
        gender: str | None = Query(default=None),
        age_group: str | None = Query(default=None),
        education: str | None = Query(default=None),
        employment_arrangement: str | None = Query(default=None),
        has_second_income: str | None = Query(default=None),
        top_priority_problem: str | None = Query(default=None),
        scheme_awareness: str | None = Query(default=None),
        healthcare_access: str | None = Query(default=None),
        schooling_access: str | None = Query(default=None),
        emergency_line_usage: str | None = Query(default=None),
        respondent_category: str | None = Query(default=None),
    ):
        self.values = {
            "pc_name": pc_name,
            "ac_name": ac_name,
            "occupation": occupation,
            "gender": gender,
            "age_group": age_group,
            "education": education,
            "employment_arrangement": employment_arrangement,
            "has_second_income": has_second_income,
            "top_priority_problem": top_priority_problem,
            "scheme_awareness": scheme_awareness,
            "healthcare_access": healthcare_access,
            "schooling_access": schooling_access,
            "emergency_line_usage": emergency_line_usage,
            "respondent_category": respondent_category,
        }

    def apply(self, q, exclude: str | None = None):
        for key, value in self.values.items():
            if value and key != exclude:
                q = q.filter(_FILTERABLE_COLUMNS[key] == value)
        return q


def _named(rows, column: str | None = None) -> list[dict]:
    """[(code, count), ...] -> [{"name": label, "code": code, "count": n}, ...], translated via choice_labels if column is given."""
    out = []
    for code, count in rows:
        label = label_for(column, code) if column else code
        out.append({"name": label or "Unknown", "code": code, "count": count})
    return out


@router.get("/summary")
def summary(
    filters: Filters = Depends(),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    q = filters.apply(db.query(SurveyResponse))
    total = q.count()
    by_pc = filters.apply(db.query(SurveyResponse.parliamentary_constituency, func.count()), "pc_name").group_by(
        SurveyResponse.parliamentary_constituency
    ).all()
    by_occupation = (
        filters.apply(db.query(SurveyResponse.occupation, func.count()), "occupation")
        .group_by(SurveyResponse.occupation)
        .order_by(func.count().desc())
        .all()
    )
    by_gender = filters.apply(db.query(SurveyResponse.gender, func.count()), "gender").group_by(SurveyResponse.gender).all()
    by_age_group = (
        filters.apply(db.query(SurveyResponse.age_group, func.count()), "age_group").group_by(SurveyResponse.age_group).all()
    )
    by_education = (
        filters.apply(db.query(SurveyResponse.education, func.count()), "education")
        .group_by(SurveyResponse.education)
        .all()
    )
    by_employment_arrangement = filters.apply(
        db.query(SurveyResponse.employment_arrangement, func.count()), "employment_arrangement"
    ).group_by(SurveyResponse.employment_arrangement).all()
    by_second_income = filters.apply(db.query(SurveyResponse.has_second_income, func.count()), "has_second_income").group_by(
        SurveyResponse.has_second_income
    ).all()

    age_order = {code: i for i, code in enumerate(_AGE_GROUP_ORDER)}
    by_age_group_sorted = sorted(by_age_group, key=lambda row: age_order.get(row[0], 99))

    education_order = {code: i for i, code in enumerate(_EDUCATION_ORDER)}
    by_education_sorted = sorted(by_education, key=lambda row: education_order.get(row[0], 99))

    return {
        "total_responses": total,
        "by_constituency": _named(by_pc),
        "by_occupation": _named(by_occupation, "occupation"),
        "by_gender": _named(by_gender, "gender"),
        "by_age_group": _named(by_age_group_sorted, "age_group"),
        "by_education": _named(by_education_sorted, "education"),
        "by_employment_arrangement": [
            {"name": EMPLOYMENT_ARRANGEMENT_LABELS.get(n, n) or "Unknown", "code": n, "count": c}
            for n, c in by_employment_arrangement
        ],
        "by_second_income": [{"name": {"yes": "Yes", "no": "No"}.get(n, n) or "Unknown", "code": n, "count": c} for n, c in by_second_income],
    }


@router.get("/political")
def political(
    filters: Filters = Depends(),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    by_priority = (
        filters.apply(db.query(SurveyResponse.top_priority_problem, func.count()), "top_priority_problem")
        .group_by(SurveyResponse.top_priority_problem)
        .order_by(func.count().desc())
        .all()
    )
    by_trust = (
        filters.apply(db.query(SurveyResponse.trust_score, func.count()))
        .group_by(SurveyResponse.trust_score)
        .order_by(SurveyResponse.trust_score)
        .all()
    )
    by_scheme_awareness = filters.apply(db.query(SurveyResponse.scheme_awareness, func.count()), "scheme_awareness").group_by(
        SurveyResponse.scheme_awareness
    ).all()
    by_healthcare = filters.apply(db.query(SurveyResponse.healthcare_access, func.count()), "healthcare_access").group_by(
        SurveyResponse.healthcare_access
    ).all()
    by_schooling = filters.apply(db.query(SurveyResponse.schooling_access, func.count()), "schooling_access").group_by(
        SurveyResponse.schooling_access
    ).all()
    by_emergency_line = filters.apply(
        db.query(SurveyResponse.emergency_line_usage, func.count()), "emergency_line_usage"
    ).group_by(SurveyResponse.emergency_line_usage).all()
    return {
        "by_priority_problem": _named(by_priority, "top_priority_problem"),
        "by_trust_score": [{"score": s, "count": c} for s, c in by_trust],
        "by_scheme_awareness": _named(by_scheme_awareness, "scheme_awareness"),
        "by_healthcare_access": _named(by_healthcare, "healthcare_access"),
        "by_schooling_access": _named(by_schooling, "schooling_access"),
        "by_emergency_line_usage": _named(by_emergency_line, "emergency_line_usage"),
    }


@router.get("/livelihood")
def livelihood(
    filters: Filters = Depends(),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """
    Cross-profession livelihood indicators extracted from the 42 profession
    modules' free-form answers (see app/sync/profession_field_categories.py
    and odk_sync.py::_extract_livelihood_indicators).

    Reports raw indicator distributions only -- no composite "Livelihood
    Security" or "Skill Readiness" index score. The North Andhra Livelihoods
    Blueprint Reporting Plan explicitly defers benchmark thresholds and
    index weighting to after the pilot (Annex A, Annex F item 5), so
    computing a combined score here would mean inventing thresholds the
    report itself hasn't set yet.
    """
    q = filters.apply(db.query(SurveyResponse))
    q = q.filter(SurveyResponse.livelihood_indicators_json.isnot(None))
    rows = q.all()

    earnings: list[float] = []
    earnings_by_occupation: dict[str, list[float]] = {}
    occupation_codes: dict[str, str] = {}
    expenses: list[float] = []
    pay_late_months: list[float] = []
    scheme_aware_n = scheme_applied_n = scheme_received_n = scheme_eligible_n = 0
    risk_counter: Counter = Counter()
    skill_counter: Counter = Counter()
    respondents_with_risk_data = respondents_with_skill_data = 0

    for r in rows:
        ind = json.loads(r.livelihood_indicators_json)
        occ_label = label_for("occupation", r.occupation) or r.occupation or "Unknown"
        occupation_codes[occ_label] = r.occupation

        for cat in _EARNINGS_CATEGORIES:
            v = ind.get(cat)
            if isinstance(v, (int, float)):
                earnings.append(v)
                earnings_by_occupation.setdefault(occ_label, []).append(v)
                break

        exp = ind.get("expenses")
        if isinstance(exp, (int, float)):
            expenses.append(exp)

        pl = ind.get("pay_late")
        if isinstance(pl, (int, float)):
            pay_late_months.append(pl)

        # A module counts toward the scheme funnel if it asked the 3-step
        # aware/applied/received question set at all (fewer modules have
        # this than "scheme_received" alone -- see profession_field_categories.py).
        if "scheme_aware" in ind or "scheme_applied" in ind or "scheme_received" in ind:
            scheme_eligible_n += 1
            if ind.get("scheme_aware"):
                scheme_aware_n += 1
            if ind.get("scheme_applied"):
                scheme_applied_n += 1
            if ind.get("scheme_received"):
                scheme_received_n += 1

        risks = ind.get("risk_incidents")
        if risks:
            respondents_with_risk_data += 1
            risk_counter.update(indicator_label(v) for v in risks if v not in ("nothing_happened", "none"))

        skills = ind.get("skills_held")
        if skills:
            respondents_with_skill_data += 1
            skill_counter.update(indicator_label(v) for v in skills if v != "none")

    def _stats(values: list[float]) -> dict:
        if not values:
            return {"count": 0, "median": None, "mean": None}
        return {"count": len(values), "median": round(statistics.median(values), 1), "mean": round(statistics.mean(values), 1)}

    return {
        "respondents_with_livelihood_data": len(rows),
        "earnings": _stats(earnings),
        "earnings_by_occupation": [
            {"occupation": occ, "occupation_code": occupation_codes.get(occ), **_stats(vals)}
            for occ, vals in sorted(earnings_by_occupation.items(), key=lambda kv: -len(kv[1]))
        ],
        "expenses": _stats(expenses),
        "pay_late_months": _stats(pay_late_months),
        "scheme_funnel": {
            "eligible_modules_n": scheme_eligible_n,
            "aware_n": scheme_aware_n,
            "applied_n": scheme_applied_n,
            "received_n": scheme_received_n,
        },
        "top_risk_incidents": [{"name": name, "count": n} for name, n in risk_counter.most_common(10)],
        "respondents_with_risk_data": respondents_with_risk_data,
        "top_skills_held": [{"name": name, "count": n} for name, n in skill_counter.most_common(10)],
        "respondents_with_skill_data": respondents_with_skill_data,
    }


@router.get("/map-points")
def map_points(
    filters: Filters = Depends(),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    """
    Respondent locations only -- no PII. Restricted to the 5 PCs' bounding
    box: one respondent's GPS landed in Austin, Texas (a device/testing
    error), which otherwise forces the map to zoom out to fit a point on the
    wrong continent. The frontend still auto-fits bounds to whatever comes
    back here, rather than relying on constituency boundary data for this.
    """
    q = filters.apply(db.query(SurveyResponse))
    q = q.filter(
        SurveyResponse.latitude.between(*_LAT_RANGE),
        SurveyResponse.longitude.between(*_LON_RANGE),
    )
    return [
        {
            "lat": r.latitude,
            "lng": r.longitude,
            "pc_name": r.parliamentary_constituency,
            "ac_name": r.assembly_constituency,
            "occupation": label_for("occupation", r.occupation) or r.occupation,
        }
        for r in q.all()
    ]
