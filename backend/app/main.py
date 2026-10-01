from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base, SessionLocal
from app.core.config import settings

# Import all models to ensure they are registered
import app.models  # noqa
from app.models.research import ResearchRun

from app.api import companies, thesis, signals, search, agent, evidence, inbox, research

Base.metadata.create_all(bind=engine)


def _mark_interrupted_runs():
    db = SessionLocal()
    try:
        db.query(ResearchRun).filter(ResearchRun.status.in_(["pending", "running"])).update(
            {"status": "failed", "error_message": "Interrupted by a server restart"},
            synchronize_session=False,
        )
        db.commit()
    finally:
        db.close()


_mark_interrupted_runs()

app = FastAPI(
    title="Signal API",
    description="Exa-powered thesis intelligence for buy-side equity analysts",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router)
app.include_router(companies.router)
app.include_router(thesis.router)
app.include_router(signals.router)
app.include_router(search.router)
app.include_router(agent.router)
app.include_router(evidence.router)
app.include_router(inbox.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "exa_available": settings.exa_available,
        "demo_mode": settings.is_demo_mode,
    }
