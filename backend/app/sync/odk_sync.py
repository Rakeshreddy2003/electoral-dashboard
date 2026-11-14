"""
Incremental sync of ODK Central submissions into Postgres.

Uses pyodk's Client against the ODK Central OData table endpoint for the
configured form, watermarked by __system/submissionDate so each run only
pulls new/changed submissions. Run standalone (`python -m app.sync.odk_sync`)
or via the scheduler in app/sync/scheduler.py.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from pyodk.client import Client

from app.config import settings
from app.constituencies_config import ac_to_no
from app.database import SessionLocal
from app.models import SurveyResponse, SyncState
from app.sync.field_map import AC_SLUG_TO_NAME, FIELD_MAP, PC_SLUG_TO_NAME, RESPONDENT_CATEGORY_LABELS, get_nested
from app.sync.profession_field_categories import FIELD_CATEGORY

# Categories whose source field is select_multiple (ODK serializes the value
# as a space-separated string of choice names) -- kept as a list. Everything
# else is a scalar (number or single choice) and the first value found wins.
_LIST_CATEGORIES = {
    "scheme_aware",
    "scheme_applied",
    "scheme_received",
    "risk_incidents",
    "skills_held",
    "documents_rights",
    "assets_resources",
}

logger = logging.getLogger(__name__)

PYODK_CONFIG_PATH = Path("/tmp/pyodk_config.toml")


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_client() -> Client:
    # pyodk always requires a TOML config file -- it does NOT fall back to
    # plain env vars (confirmed against pyodk._utils.config.read_config,
    # which unconditionally opens a file). Generate that file from our own
    # settings (which already come from ODK_BASE_URL/ODK_EMAIL/ODK_PASSWORD/
    # ODK_PROJECT_ID) rather than maintaining credentials in two places.
    PYODK_CONFIG_PATH.write_text(
        "[central]\n"
        f'base_url = "{_toml_escape(settings.odk_base_url)}"\n'
        f'username = "{_toml_escape(settings.odk_email)}"\n'
        f'password = "{_toml_escape(settings.odk_password)}"\n'
        f"default_project_id = {settings.odk_project_id}\n",
        encoding="utf-8",
    )
    return Client(config_path=str(PYODK_CONFIG_PATH))


def _parse_odk_datetime(value: str | None) -> datetime | None:
    # Stored as naive UTC (the DateTime columns aren't timezone-aware) --
    # strip tzinfo after parsing so this compares cleanly against
    # state.last_submission_update, which comes back naive from Postgres.
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(UTC).replace(tzinfo=None)
    except ValueError:
        return None


def _to_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_livelihood_indicators(module: dict) -> dict | None:
    """
    Applies the label-derived FIELD_CATEGORY mapping to one respondent's
    active profession-module answers, producing normalized cross-profession
    indicators (earnings, expenses, scheme funnel, skills, risks, ...) --
    see app/sync/profession_field_categories.py for how this was built.

    Several modules use a "status then enter-number" pair (e.g. mf_q04_status
    + mf_q04) where both fields carry the same question label, so both land
    in the same category here. A numeric answer always wins over a status
    sentinel like "don't know" -- collect every candidate per scalar
    category, then prefer the first numeric one, falling back to the first
    qualitative value only if nothing numeric was given.
    """
    candidates: dict[str, list] = {}
    out: dict = {}
    for field_name, value in module.items():
        if value is None:
            continue
        category = FIELD_CATEGORY.get(field_name)
        if category is None:
            continue
        if category in _LIST_CATEGORIES:
            out.setdefault(category, []).extend(str(value).split())
        else:
            candidates.setdefault(category, []).append(value)

    for category, values in candidates.items():
        numeric = next((n for v in values if (n := _to_float(v)) is not None), None)
        out[category] = numeric if numeric is not None else values[0]

    return out or None


def _flatten_submission(sub: dict) -> dict:
    out = {}
    for column, path in FIELD_MAP.items():
        out[column] = get_nested(sub, path)

    # The form stores lowercase choice slugs for PC/AC; every filter
    # elsewhere expects the Title Case display name (see field_map.py).
    out["parliamentary_constituency"] = PC_SLUG_TO_NAME.get(
        out.get("parliamentary_constituency"), out.get("parliamentary_constituency")
    )
    out["assembly_constituency"] = AC_SLUG_TO_NAME.get(out.get("assembly_constituency"), out.get("assembly_constituency"))

    # interview_geopoint is a GeoJSON Point: coordinates = [lon, lat, alt].
    geopoint = get_nested(sub, "grp_profile.interview_geopoint")
    if isinstance(geopoint, dict):
        coords = geopoint.get("coordinates") or []
        if len(coords) >= 2:
            out["longitude"], out["latitude"] = coords[0], coords[1]

    # 1-5 scale questions are select_ones (string choice names), not integers.
    out["trust_score"] = _to_int(out.get("trust_score"))

    # Translate the respondent-category slug to the Title Case label the
    # API/frontend filter on (see field_map.py).
    raw_category = out.get("respondent_category")
    out["respondent_category"] = RESPONDENT_CATEGORY_LABELS.get(raw_category, raw_category)

    # Profession-module answers live in a group named after the chosen
    # occupation (grp_prof_<occupation>) -- pull whichever one is present.
    occupation = out.get("occupation")
    if occupation:
        module = sub.get(f"grp_prof_{occupation}")
        if isinstance(module, dict) and any(v is not None for v in module.values()):
            out["profession_module_json"] = json.dumps(module)
            indicators = _extract_livelihood_indicators(module)
            if indicators:
                out["livelihood_indicators_json"] = json.dumps(indicators)

    return out


def sync_once() -> int:
    db = SessionLocal()
    pulled = 0
    try:
        state = db.query(SyncState).filter(SyncState.form_id == settings.odk_form_id).first()
        if state is None:
            state = SyncState(form_id=settings.odk_form_id)
            db.add(state)
            db.commit()

        client = _build_client()
        table = client.submissions.get_table(
            form_id=settings.odk_form_id,
            project_id=settings.odk_project_id,
        )
        rows = table.get("value", table) if isinstance(table, dict) else table

        latest_seen = state.last_submission_update

        for sub in rows:
            system = sub.get("__system", {})
            instance_id = system.get("instanceId") or sub.get("meta", {}).get("instanceID")
            if not instance_id:
                continue

            submission_date = _parse_odk_datetime(system.get("submissionDate"))
            updated_date = _parse_odk_datetime(system.get("updatedAt")) or submission_date

            if state.last_submission_update and updated_date and updated_date <= state.last_submission_update:
                continue

            flat = _flatten_submission(sub)

            existing = db.query(SurveyResponse).filter(SurveyResponse.odk_instance_id == instance_id).first()
            record = existing or SurveyResponse(odk_instance_id=instance_id)

            record.submitted_at = submission_date
            record.updated_at = updated_date
            record.submitter_name = system.get("submitterName")
            record.parliamentary_constituency = flat.get("parliamentary_constituency")
            record.assembly_constituency = flat.get("assembly_constituency")
            record.ac_no = ac_to_no(flat.get("assembly_constituency"))
            record.latitude = flat.get("latitude")
            record.longitude = flat.get("longitude")
            record.gender = flat.get("gender")
            record.age_group = flat.get("age_group")
            record.marital_status = flat.get("marital_status")
            record.education = flat.get("education")
            record.occupation = flat.get("occupation")
            record.employment_arrangement = flat.get("employment_arrangement")
            record.household_size = _to_int(flat.get("household_size"))
            record.monthly_expenditure = flat.get("monthly_expenditure")
            record.has_second_income = flat.get("has_second_income")
            record.second_occupation = flat.get("second_occupation")
            record.profession_module_json = flat.get("profession_module_json")
            record.livelihood_indicators_json = flat.get("livelihood_indicators_json")
            record.top_priority_problem = flat.get("top_priority_problem")
            record.trust_score = flat.get("trust_score")
            record.scheme_awareness = flat.get("scheme_awareness")
            record.healthcare_access = flat.get("healthcare_access")
            record.schooling_access = flat.get("schooling_access")
            record.emergency_line_usage = flat.get("emergency_line_usage")
            record.respondent_category = flat.get("respondent_category")
            record.contact_name = flat.get("contact_name")
            record.contact_phone_1 = flat.get("contact_phone_1")
            record.contact_phone_2 = flat.get("contact_phone_2")
            record.raw_json = json.dumps(sub)

            if not existing:
                db.add(record)
            pulled += 1

            if updated_date and (latest_seen is None or updated_date > latest_seen):
                latest_seen = updated_date

        state.last_submission_update = latest_seen
        state.last_run_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        logger.info("ODK sync complete: %s submissions processed", pulled)
        return pulled
    except Exception:
        db.rollback()
        logger.exception("ODK sync failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync_once()
