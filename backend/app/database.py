from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """
    Base.metadata.create_all only creates missing tables, not columns added to
    a model after the table already exists in a deployed DB -- there's no
    Alembic in this project, so new columns need a small idempotent ALTER
    here instead. Add one line per column added after initial deploy.
    """
    inspector = inspect(engine)
    if "survey_responses" not in inspector.get_table_names():
        return  # create_all (called right before this) will make it fresh, with ac_no already present
    existing_columns = {c["name"] for c in inspector.get_columns("survey_responses")}
    if "ac_no" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE survey_responses ADD COLUMN ac_no INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_survey_responses_ac_no ON survey_responses (ac_no)"))
