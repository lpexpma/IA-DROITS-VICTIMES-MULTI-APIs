# app/main.py
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Annotated, Literal, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# Import du client multi-APIs
# ----------------------------------------------------------------------
from app.services.api_clients import ClientMultiAPIs  # type: ignore


# ----------------------------------------------------------------------
# Modèles Pydantic (v2)
# ----------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    timestamp: str = Field(..., description="Horodatage ISO 8601 (UTC)")


class ReadyResponse(BaseModel):
    status: Literal["ready"] = "ready"
    timestamp: str = Field(..., description="Horodatage ISO 8601 (UTC)")


class RechercheCompleteRequest(BaseModel):
    description_situation: str = Field(..., min_length=3, description="Texte décrivant la situation ou le préjudice")
    include_apis: Optional[list[str]] = Field(
        default=None,
        description="Liste optionnelle pour limiter les sources (ex: ['legifrance','judilibre','justice_back'])",
    )
    code_postal: Optional[str] = Field(
        default=None,
        pattern=r"^\d{5}$",
        description="Code postal français sur 5 chiffres (optionnel)",
    )


# ----------------------------------------------------------------------
# Initialisation FastAPI
# ----------------------------------------------------------------------
APP_NAME = "IA DROITS VICTIMES MULTI-APIs"
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Orchestrateur FastAPI centralisant Légifrance (DILA), Judilibre et l'Annuaire des lieux de justice.\n"
        "Routes stables sous le préfixe /api."
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

api = APIRouter(prefix="/api", tags=["api"])


# ----------------------------------------------------------------------
# CORS (Render + env)
# ----------------------------------------------------------------------
allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
origins = set()

for host in [h.strip() for h in allowed_hosts.split(",") if h.strip()]:
    if host.startswith("http://") or host.startswith("https://"):
        origins.add(host)
    else:
        origins.add(f"https://{host}")
        origins.add(f"http://{host}")

origins.update({"http://localhost:8000", "http://127.0.0.1:8000"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(list(origins)) if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------
# Client Multi-APIs (singleton)
# ----------------------------------------------------------------------
client = ClientMultiAPIs(
    legifrance_base_url=os.getenv("API_LEGIFRANCE_BASE_URL"),
    legifrance_client_id=os.getenv("API_LEGIFRANCE_CLIENT_ID"),
    legifrance_client_secret=os.getenv("API_LEGIFRANCE_CLIENT_SECRET"),
    judilibre_base_url=os.getenv("JUDILIBRE_BASE_URL"),
    judilibre_api_key=os.getenv("JUDILIBRE_API_KEY"),
    justice_back_base_url=os.getenv("JUSTICE_BACK_BASE_URL"),
    justice_back_client_id=os.getenv("JUSTICE_BACK_CLIENT_ID"),
    justice_back_client_secret=os.getenv("JUSTICE_BACK_CLIENT_SECRET"),
    debug=os.getenv("DEBUG", "false").lower() == "true",
)


# ----------------------------------------------------------------------
# Utils
# ----------------------------------------------------------------------
def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ----------------------------------------------------------------------
# Root (accueil)
# ----------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs", status_code=307)


# ----------------------------------------------------------------------
# Health & Ready
# ----------------------------------------------------------------------
@api.get("/health", response_model=HealthResponse, summary="Healthcheck simple")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=now_iso_utc())


@api.get("/ready", response_model=ReadyResponse, summary="Readiness probe")
async def ready() -> ReadyResponse:
    return ReadyResponse(status="ready", timestamp=now_iso_utc())


# ----------------------------------------------------------------------
# Lieux de justice (Justice Back)
# ----------------------------------------------------------------------
@api.get(
    "/lieux-justice",
    summary="Recherche des lieux de justice par code postal",
    description="Interroge l'annuaire des lieux de justice via le service Justice Back.",
)
async def lieux_justice(
    code_postal: Annotated[str, Query(pattern=r"^\d{5}$", description="Code postal français, 5 chiffres")],
):
    try:
        result = await client.get_lieux_justice(code_postal=code_postal)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur en interrogeant Justice Back: {exc}") from exc


# ----------------------------------------------------------------------
# Recherche complète (Légifrance / Judilibre / Justice Back)
# ----------------------------------------------------------------------
@api.post(
    "/recherche-complete",
    summary="Orchestration multi-APIs à partir d'une description",
    description=(
        "Analyse la description de la situation et interroge Légifrance, Judilibre et/ou l'annuaire des lieux de justice "
        "selon les paramètres fournis."
    ),
)
async def recherche_complete(payload: RechercheCompleteRequest):
    try:
        result = await client.recherche_complete(
            description_situation=payload.description_situation.strip(),
            include_apis=payload.include_apis,
            code_postal=payload.code_postal,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors de l'orchestration: {exc}") from exc


# ----------------------------------------------------------------------
# Test des intégrations externes
# ----------------------------------------------------------------------
@api.get(
    "/test-apis",
    summary="Vérifie la connectivité et l'authentification aux services externes",
    description="Ping des APIs externes (Légifrance, Judilibre, Justice Back) pour valider la configuration.",
)
async def test_apis():
    try:
        return await client.test_apis()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur lors des tests d'APIs: {exc}") from exc


# ----------------------------------------------------------------------
# Montage du router
# ----------------------------------------------------------------------
app.include_router(api)


# ----------------------------------------------------------------------
# Entrée locale (uvicorn)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
    )
