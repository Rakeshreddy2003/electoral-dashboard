from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://crawworkds:crawworkds@localhost:5432/crawworkds"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Temporary: skips login and role checks entirely, treating every
    # request as an admin. See app/deps.py::get_current_user. Flip back to
    # False (or unset) to re-require login.
    auth_disabled: bool = False

    odk_base_url: str = "https://your-odk-central-host.example"
    odk_email: str = ""
    odk_password: str = ""
    odk_project_id: int = 1
    odk_form_id: str = "na_livelihoods_survey_v4"
    odk_sync_interval_minutes: int = 20
    # Set false to pause pulling from ODK Central entirely -- the scheduler
    # just never starts, so the API still serves whatever's already in
    # Postgres. Flip back to true (or unset) to resume live syncing.
    odk_sync_enabled: bool = True

    # The 5 parliamentary constituencies this survey covers.
    pc_names: list[str] = [
        "Araku",
        "Srikakulam",
        "Vizianagaram",
        "Visakhapatnam",
        "Anakapalli",
    ]


settings = Settings()
