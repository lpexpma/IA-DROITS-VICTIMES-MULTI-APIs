# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ⚠️ l'objet DOIT s'appeler "app"
app = FastAPI(title="IA Droits Victimes", version="0.1")

# Fichiers statiques (JS/CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Page d'accueil
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Petit ping de test
@app.get("/api/health")
async def health():
    return {"status": "ok"}

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

app = FastAPI(
    title="IA Droits Victimes",
    version="3.1.8",
    docs_url="/api/docs",      # 👈 ici
    redoc_url="/api/redoc"     # 👈 et ici (optionnel)
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# --- Readiness minimal, toujours présent ---
from datetime import datetime
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# si pas déjà fait, on s'assure d'avoir app et la doc au bon chemin
try:
    app
except NameError:
    from fastapi import FastAPI
    app = FastAPI(
        title="IA Droits Victimes",
        description="API d'analyse intelligente des préjudices complexes",
        version="3.1.8",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

# Fichiers statiques (si pas déjà montés)
try:
    app.user_middleware  # juste pour éviter de monter 2 fois
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception:
    pass

# Page d'accueil simple si tu n’as pas de moteur de templates
@app.get("/", include_in_schema=False)
def home():
    # Si tu as app/templates/index.html, décommente la ligne suivante :
    # return FileResponse("app/templates/index.html")
    return {"message": "IA Droits Victimes en ligne. Voir /api/docs"}

# Readiness simple (toujours OK si l’app est démarrée)
@app.get("/api/ready")
async def readiness_check():
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }
