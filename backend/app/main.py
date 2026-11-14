import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_auth, routes_influencers, routes_responses, routes_retrospective
from app.config import settings
from app.database import Base, engine, ensure_schema
from app.sync.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="North Andhra Livelihoods Survey Dashboard API")

# In production this should be the dashboard's own origin only -- tighten
# once the frontend's deployed URL is known, rather than leaving it open.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_retrospective.router)
app.include_router(routes_responses.router)
app.include_router(routes_influencers.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    if settings.odk_sync_enabled:
        start_scheduler()
    else:
        logging.info("ODK sync disabled (ODK_SYNC_ENABLED=false) -- serving existing data only")


@app.get("/api/health")
def health():
    return {"status": "ok"}
