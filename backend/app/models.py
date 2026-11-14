import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
)

from app.database import Base


class Role(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.viewer)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), nullable=False, index=True)
    action = Column(String(64), nullable=False)  # e.g. "view_pii", "export_pii"
    resource = Column(String(128), nullable=False)  # e.g. "influencers"
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SyncState(Base):
    """Tracks the ODK sync watermark so pulls are incremental."""

    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True)
    form_id = Column(String(255), unique=True, nullable=False)
    last_submission_update = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)


class SurveyResponse(Base):
    """
    One row per ODK submission, flattened for the core profile + political
    sections used across all 3 dashboard pages. Profession-module-specific
    answers (which vary per occupation branch) are kept as a JSON blob in
    `profession_module_json` rather than one column per possible question,
    since only ~2-27 of the ~1315 form questions apply to any given
    respondent and the set of profession modules may still evolve.
    """

    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True)
    odk_instance_id = Column(String(255), unique=True, nullable=False, index=True)
    submitted_at = Column(DateTime, nullable=True, index=True)
    updated_at = Column(DateTime, nullable=True, index=True)
    submitter_name = Column(String(255), nullable=True)

    # Location
    parliamentary_constituency = Column(String(128), nullable=True, index=True)
    assembly_constituency = Column(String(128), nullable=True, index=True)
    # The real ECI AC number for assembly_constituency, backfilled from
    # app.constituencies_config.AC_NO -- the numeric join key to EciResult.
    # constituency_no / SecretariatProfile.ac_no, kept alongside the name
    # string rather than replacing it (the name is still what the UI
    # filters/displays by).
    ac_no = Column(Integer, nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Profile
    gender = Column(String(32), nullable=True)
    age_group = Column(String(32), nullable=True)  # the form asks an age bucket (e.g. "19_25"), not a raw age
    marital_status = Column(String(64), nullable=True)
    education = Column(String(128), nullable=True)
    occupation = Column(String(128), nullable=True)
    employment_arrangement = Column(String(64), nullable=True)
    household_size = Column(Integer, nullable=True)
    monthly_expenditure = Column(Float, nullable=True)
    has_second_income = Column(String(16), nullable=True)
    second_occupation = Column(String(128), nullable=True)

    profession_module_json = Column(Text, nullable=True)

    # Normalized cross-profession indicators extracted from profession_module_json
    # by matching each module's question labels against the Reporting Plan's
    # chapters (earnings, expenses, scheme funnel, skills, risks, resource
    # access) -- see app/sync/profession_field_categories.py. Raw indicators
    # only, no composite index score (the Reporting Plan defers benchmarks
    # and index scoring to after the pilot).
    livelihood_indicators_json = Column(Text, nullable=True)

    # Political / governance
    top_priority_problem = Column(String(255), nullable=True)
    trust_score = Column(Integer, nullable=True)  # 1-5
    scheme_awareness = Column(String(64), nullable=True)  # single select, not a list despite the old column name
    healthcare_access = Column(String(128), nullable=True)
    schooling_access = Column(String(128), nullable=True)
    emergency_line_usage = Column(String(64), nullable=True)

    # Respondent classification -- PII lives here, stripped for non-admins
    # at the API layer (see app/auth.py strip_pii / app/api/routes_influencers.py).
    respondent_category = Column(String(64), nullable=True, index=True)  # Neutral Influencer / Volunteer Army / Not applicable
    contact_name = Column(String(255), nullable=True)
    contact_phone_1 = Column(String(32), nullable=True)
    contact_phone_2 = Column(String(32), nullable=True)

    raw_json = Column(Text, nullable=True)


class EciResult(Base):
    """
    Historical ECI candidate-level results, both assembly (AE/AC) and
    parliamentary/Lok Sabha (GE/PC) elections, from the andhra_pradesh_retro
    MATData export (see backend/etl/load_eci_data.py). `level` distinguishes
    whether `constituency_name` holds an AC name or a PC name; `pc_name` is
    always the owning PC, for filtering either level by PC.
    """

    __tablename__ = "eci_results"

    id = Column(Integer, primary_key=True)
    election_type = Column(String(8), nullable=False)  # "AE" or "GE"
    level = Column(String(8), nullable=False, index=True)  # "AC" or "PC"
    year = Column(Integer, nullable=False, index=True)
    constituency_no = Column(Integer, nullable=True)
    constituency_name = Column(String(128), nullable=False, index=True)
    pc_name = Column(String(128), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=False)
    party = Column(String(64), nullable=True)
    position = Column(Integer, nullable=True)
    votes = Column(Integer, nullable=True)
    vote_share_percentage = Column(Float, nullable=True)
    margin = Column(Integer, nullable=True)  # raw vote margin; positive for the winner, negative for everyone else
    margin_percentage = Column(Float, nullable=True)
    total_electors = Column(Integer, nullable=True)
    total_votes = Column(Integer, nullable=True)
    turnout_percentage = Column(Float, nullable=True)


class SecretariatProfile(Base):
    """
    Pre-survey baseline socio-economic data (Sarkar BigQuery extract, see
    data/socioeco/00_README.txt) at secretariat granularity -- the finest
    geography that joins cleanly to pc_name/ac_name. Loaded by
    backend/etl/load_socioeco_data.py. This is intentionally the pre-survey
    baseline the North Andhra Livelihoods Survey's own findings get compared
    against, not stale data (confirmed with the user 2026-10-19) -- the BPL
    proxy and scheme-enrollment basis predate AP's 2024 change of government,
    so treat pct_bpl_proxy_hh as a baseline-era figure, not a live one.
    """

    __tablename__ = "secretariat_profiles"

    id = Column(Integer, primary_key=True)
    pc_name = Column(String(128), nullable=False, index=True)
    ac_no = Column(Integer, nullable=True)
    ac_name = Column(String(128), nullable=False, index=True)
    mandal_name = Column(String(128), nullable=True)
    secretariat_code = Column(String(32), nullable=True)
    secretariat_name = Column(String(128), nullable=True)
    rural_urban = Column(String(8), nullable=True)
    households = Column(Integer, nullable=True)
    population = Column(Integer, nullable=True)
    pct_bpl_proxy_hh = Column(Float, nullable=True)
    avg_electricity_bill_inr = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Raw head counts (not just percentages) so AC/PC-level aggregation can
    # sum counts and divide, rather than wrongly averaging percentages.
    caste_counts_json = Column(Text, nullable=True)
    caste_persons_total = Column(Integer, nullable=True)
    religion_counts_json = Column(Text, nullable=True)
    religion_persons_total = Column(Integer, nullable=True)
