import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import record as audit_record
from app.auth import strip_pii
from app.choice_labels import label_for
from app.database import get_db
from app.deps import get_current_user, require_admin, require_any
from app.models import Role, SurveyResponse, User

router = APIRouter(prefix="/api/influencers", tags=["influencers"])

CATEGORIES = ("Neutral Influencer", "Volunteer Army", "Not applicable")


def _apply_filters(q, pc_name, ac_name, category):
    if pc_name:
        q = q.filter(SurveyResponse.parliamentary_constituency == pc_name)
    if ac_name:
        q = q.filter(SurveyResponse.assembly_constituency == ac_name)
    if category:
        q = q.filter(SurveyResponse.respondent_category == category)
    return q


@router.get("/summary")
def summary(
    pc_name: str | None = Query(default=None),
    ac_name: str | None = Query(default=None),
    _=Depends(require_any),
    db: Session = Depends(get_db),
):
    q = _apply_filters(db.query(SurveyResponse.respondent_category, func.count()), pc_name, ac_name, None)
    rows = q.group_by(SurveyResponse.respondent_category).all()
    return [{"category": c or "Unknown", "count": n} for c, n in rows]


@router.get("/list")
def list_respondents(
    pc_name: str | None = Query(default=None),
    ac_name: str | None = Query(default=None),
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Respondent-category rows. Contact name/phone numbers are only present
    in the response when the caller is Admin -- stripped server-side via
    strip_pii(), not hidden client-side. Viewing this list as Admin is
    audit-logged because it exposes PII.
    """
    q = _apply_filters(
        db.query(SurveyResponse).filter(SurveyResponse.respondent_category.in_(("Neutral Influencer", "Volunteer Army"))),
        pc_name,
        ac_name,
        category,
    )
    rows = q.all()

    if user.role == Role.admin:
        audit_record(db, user.email, "view_pii", "influencers", detail=f"pc={pc_name} ac={ac_name} category={category} rows={len(rows)}")

    results = []
    for r in rows:
        record = {
            "id": r.id,
            "pc_name": r.parliamentary_constituency,
            "ac_name": r.assembly_constituency,
            "category": r.respondent_category,
            "occupation": label_for("occupation", r.occupation) or r.occupation,
            "contact_name": r.contact_name,
            "contact_phone_1": r.contact_phone_1,
            "contact_phone_2": r.contact_phone_2,
        }
        results.append(strip_pii(record, user.role))
    return results


@router.get("/export.csv")
def export_csv(
    pc_name: str | None = Query(default=None),
    ac_name: str | None = Query(default=None),
    category: str | None = Query(default=None),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """CSV export with PII -- Admin only, always audit-logged."""
    q = _apply_filters(
        db.query(SurveyResponse).filter(SurveyResponse.respondent_category.in_(("Neutral Influencer", "Volunteer Army"))),
        pc_name,
        ac_name,
        category,
    )
    rows = q.all()
    audit_record(db, user.email, "export_pii", "influencers", detail=f"pc={pc_name} ac={ac_name} category={category} rows={len(rows)}")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["pc_name", "ac_name", "category", "occupation", "contact_name", "contact_phone_1", "contact_phone_2"])
    for r in rows:
        writer.writerow(
            [
                r.parliamentary_constituency,
                r.assembly_constituency,
                r.respondent_category,
                r.occupation,
                r.contact_name,
                r.contact_phone_1,
                r.contact_phone_2,
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=influencers_volunteers.csv"},
    )
