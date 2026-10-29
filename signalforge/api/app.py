import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from signalforge.config import settings
from signalforge.db.connection import init_db
from signalforge.api.routes import router

app = FastAPI(
    title="SignalForge",
    description="Production-Grade Data Engineering, Pipeline Reliability & Observability Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.on_event("startup")
def on_startup():
    init_db()

# Serve static frontend build if present
frontend_dist = settings.data_dir.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
