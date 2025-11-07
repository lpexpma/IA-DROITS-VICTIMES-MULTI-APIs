# app/main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import logging

app = FastAPI(
    title="IA Droits Victimes",
    description="API d'analyse intelligente des préjudices complexes",
    version="3.1.8",
    docs_url="/api/docs",      # <— on force la doc ici
    redoc_url="/api/redoc",
)

# Fichiers statiques (ok même si le dossier existe déjà)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Page d'accueil : sert index.html si présent, sinon un message simple
@app.get("/", include_in_schema=False)
def home():
    try:
        return FileResponse("app/templates/index.html")
    except Exception:
        return HTMLResponse("<h1>IA Droits Victimes</h1><p>Voir <a href='/api/docs'>/api/docs</a></p>")

# Santé simple
@app.get("/api/health")
async def health():
    return {"ok": True}

# Readiness minimal (répond 'ready' si l’app est démarrée)
@app.get("/api/ready")
async def readiness():
    return {"status": "ready", "timestamp": datetime.now().isoformat(timespec="seconds")}

# (Optionnel) Log des routes au démarrage pour debug
@app.on_event("startup")
async def log_routes():
    logger = logging.getLogger("uvicorn")
    for r in app.routes:
        logger.info(f"ROUTE: {r.path}")
