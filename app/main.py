# app/main.py - VERSION CORRECTE ET FINALE
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import des modules locaux
from app.services.api_clients import ClientMultiAPIs
from app.services.analyse_prejudices import AnalyseurPrejudicesComplexes
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.models.schemas import SearchRequest, AnalyseRequest

# Chargement configuration
from dotenv import load_dotenv
load_dotenv("config/.env")

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application FastAPI
app = FastAPI(
    title="IA Droits Victimes - API",
    description="Assistant juridique intelligent pour victimes avec analyse préjudices complexes",
    version="3.1.8",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Middlewares
app.add_middleware(CorrelationMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Servir les fichiers statiques pour CSP
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Redirection racine
@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirection vers la documentation API"""
    docs_url = app.docs_url
    if docs_url is None:
        docs_url = "/docs"
    return RedirectResponse(url=docs_url, status_code=307)

# Cache pour le endpoint readiness
class ReadinessCache:
    """Cache pour les résultats de readiness avec TTL"""
    
    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self._cache = None
        self._timestamp = None
    
    def get(self):
        """Récupère le cache s'il est encore valide"""
        if self._cache and self._timestamp:
            if datetime.now() - self._timestamp < timedelta(seconds=self.ttl_seconds):
                return self._cache
        return None
    
    def set(self, data):
        """Met à jour le cache"""
        self._cache = data
        self._timestamp = datetime.now()

readiness_cache = ReadinessCache(ttl_seconds=60)

# Session HTTP globale
@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage de l'application"""
    app.state.network_semaphore = asyncio.Semaphore(10)
    app.state.http_client = ClientMultiAPIs(semaphore=app.state.network_semaphore)
    
    logger.info("🚀 IA Droits Victimes - Version 3.1.8 démarrée")
    logger.info("📍 Documentation: http://localhost:8000/api/docs")
    logger.info("❤️  Health check: http://localhost:8000/api/health")

@app.on_event("shutdown") 
async def shutdown_event():
    """Nettoyage à l'arrêt de l'application"""
    await app.state.http_client.close()
    logger.info("🛑 Arrêt de l'application IA Droits Victimes")

def get_client() -> ClientMultiAPIs:
    """Retourne le client HTTP global"""
    return app.state.http_client

# Routes principales
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Page d'accueil de l'application"""
    logger.info(f"Requête page d'accueil - {request.state.request_id}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def api_health_check():
    """Endpoint de santé basique de l'application"""
    return {
        "status": "healthy",
        "service": "IA Droits Victimes Multi-APIs",
        "version": "3.1.8",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/ready")
async def api_readiness_check(request: Request):
    """
    Endpoint de readiness - vérifie que l'application est vraiment prête
    avec cache pour éviter le martèlement des APIs
    """
    cached_result = readiness_cache.get()
    if cached_result:
        logger.info(f"Readiness check: résultat depuis le cache - {request.state.request_id}")
        return cached_result
    
    checks = {}
    
    try:
        client = get_client()
        
        # Vérification connexion Légifrance
        token_legifrance = await client.get_legifrance_token()
        checks["legifrance_auth"] = bool(token_legifrance)
        
        # Vérification connexion Justice Back  
        token_justice_back = await client.get_justice_back_token()
        checks["justice_back_auth"] = bool(token_justice_back)
        
        # Vérification Judilibre
        test_response = await client.search_judilibre("search", {"q": "test", "page": 1, "page_size": 1})
        checks["judilibre_connect"] = bool(test_response)
        
    except Exception as e:
        logger.error(f"Erreur readiness check: {e} - {request.state.request_id}")
        result = {
            "status": "not_ready",
            "checks": checks,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        readiness_cache.set(result)
        return result
    
    all_ready = all(checks.values())
    status = "ready" if all_ready else "degraded"
    
    result = {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
    
    if status != "not_ready":
        readiness_cache.set(result)
    
    logger.info(f"Readiness check: {status} - {checks} - {request.state.request_id}")
    return result

@app.get("/api/test-apis")
async def test_apis(request: Request):
    """Test de connexion à toutes les APIs externes"""
    logger.info(f"Test des APIs - {request.state.request_id}")
    
    results = {}
    client = get_client()
    
    try:
        token = await client.get_legifrance_token()
        results["legifrance"] = {"status": "success", "message": "✅ Connecté à Légifrance"}
    except Exception as e:
        logger.error(f"Erreur Légifrance: {str(e)} - {request.state.request_id}")
        results["legifrance"] = {"status": "error", "message": f"❌ Erreur de connexion à Légifrance: {str(e)}"}
    
    try:
        token = await client.get_justice_back_token()
        results["justice_back"] = {"status": "success", "message": "✅ Connecté à Justice Back"}
    except Exception as e:
        logger.error(f"Erreur Justice Back: {str(e)} - {request.state.request_id}")
        results["justice_back"] = {"status": "error", "message": f"❌ Erreur de connexion à Justice Back: {str(e)}"}
    
    try:
        await client.search_judilibre("search", {"q": "test", "size": 1})
        results["judilibre"] = {"status": "success", "message": "✅ Connecté à Judilibre"}
    except Exception as e:
        logger.error(f"Erreur Judilibre: {str(e)} - {request.state.request_id}")
        results["judilibre"] = {"status": "error", "message": f"❌ Erreur de connexion à Judilibre: {str(e)}"}
    
    return results

@app.get("/api/test-piste-auth")
async def test_piste_auth_direct():
    """Test direct de l'authentification PISTE"""
    import aiohttp
    import base64
    
    # Utilisez les mêmes identifiants pour les 3 APIs
    client_id = os.getenv("LEGIFRANCE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff")
    client_secret = os.getenv("LEGIFRANCE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e")
    
    # Encodage Basic Auth
    auth_str = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://sandbox-oauth.piste.gouv.fr/api/oauth/token",
            headers={
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data="grant_type=client_credentials&scope=openid"
        ) as response:
            response_text = await response.text()
            return {
                "status_code": response.status,
                "client_id_used": client_id,
                "client_secret_length": len(client_secret) if client_secret else 0,
                "response_body": response_text,
                "auth_url": "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
            }

@app.post("/api/analyser-situation")
async def analyser_situation_endpoint(request: AnalyseRequest, http_request: Request):
    """
    Analyse complète d'une situation avec détection automatique des préjudices
    et recherche de jurisprudence spécialisée
    """
    logger.info(f"Analyse situation - {http_request.state.request_id}")
    
    client = get_client()
    analyseur = AnalyseurPrejudicesComplexes()
    
    try:
        # 1. Analyse de la description
        analyse_description = analyseur.analyser_description(request.description_situation)
        prejudices_detectes = [p["categorie"] for p in analyse_description["prejudices_detectes"]]
        
        logger.info(f"Préjudices détectés: {prejudices_detectes} - {http_request.state.request_id}")
        
        # 2. Construction des requêtes spécialisées
        requetes = analyseur.construire_requetes_jurisprudence(prejudices_detectes)
        
        # 3. Recherche parallèle de jurisprudence
        tasks = []
        for prejudice, requete in requetes.items():
            tasks.append(client.search_judilibre("search", requete))
        
        resultats_jurisprudence = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. Formatage des résultats
        jurisprudence_par_prejudice = {}
        for i, (prejudice, resultat) in enumerate(zip(requetes.keys(), resultats_jurisprudence)):
            if not isinstance(resultat, Exception) and isinstance(resultat, dict):
                jurisprudence_par_prejudice[prejudice] = formater_resultats_judilibre_func(resultat)
            else:
                logger.error(f"Erreur jurisprudence {prejudice}: {str(resultat)} - {http_request.state.request_id}")
                jurisprudence_par_prejudice[prejudice] = {"erreur": "Erreur lors de la recherche"}
        
        # 5. Estimation indemnisation
        estimation = analyseur.estimer_indemnisation(prejudices_detectes)
        
        # 6. Recherche ressources locales si code postal fourni
        ressources_locales = {}
        if request.code_postal:
            try:
                lieux = await client.search_justice_back(
                    "node/lieu_de_justice", 
                    {"page[limit]": 5, "filter[code_postal]": request.code_postal}
                )
                ressources_locales = formater_lieux_justice_func(lieux)
            except Exception as e:
                logger.error(f"Erreur ressources locales: {str(e)} - {http_request.state.request_id}")
                ressources_locales = {"erreur": "Erreur lors de la recherche des ressources locales"}
        
        return {
            "analyse_description": analyse_description,
            "jurisprudence_par_prejudice": jurisprudence_par_prejudice,
            "estimation_indemnisation": estimation,
            "ressources_locales": ressources_locales,
            "recommandations_generales": generer_recommandations_func(analyse_description)
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse situation: {str(e)} - {http_request.state.request_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'analyse de la situation"
        )

@app.post("/api/recherche-complete")
async def recherche_complete_endpoint(request: SearchRequest, http_request: Request):
    """Recherche multi-APIs classique avec gestion des erreurs"""
    logger.info(f"Recherche complète - {http_request.state.request_id}")
    
    client = get_client()
    
    try:
        tasks = []
        
        if "legifrance" in request.include_apis:
            query_legifrance = {
                "fond": "ALL",
                "recherche": {
                    "champs": [{
                        "typeChamp": "ALL",
                        "operateur": "ET",
                        "criteres": [{
                            "typeRecherche": "TOUS_LES_MOTS",
                            "valeur": f"{request.description_situation} accident indemnisation responsabilité"
                        }]
                    }],
                    "filtres": [{"facette": "NATURE", "valeurs": ["LOI", "DECRET", "ARRET", "CODE"]}],
                    "pageNumber": 1,
                    "pageSize": 8,
                    "sort": "SIGNATURE_DATE_DESC"
                }
            }
            tasks.append(client.search_legifrance(query_legifrance))
        
        if "judilibre" in request.include_apis:
            query_judilibre = {
                "q": request.description_situation,
                "size": 8,
                "sort": [{"date": "desc"}]
            }
            tasks.append(client.search_judilibre("search", query_judilibre))
        
        if "justice_back" in request.include_apis:
            justice_params: Dict[str, Any] = {"page[limit]": 8}
            
            if hasattr(request, 'code_postal') and request.code_postal is not None:
                code_postal_value = request.code_postal
                if not isinstance(code_postal_value, str):
                    code_postal_value = str(code_postal_value)
                if re.match(r'^\d{5}$', code_postal_value):
                    justice_params["filter[code_postal]"] = code_postal_value
                else:
                    logger.warning(f"Code postal invalide ignoré: {code_postal_value}")
            
            tasks.append(client.search_justice_back("node/lieu_de_justice", justice_params))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return formater_resultats_complets_func(results, request.include_apis)
        
    except Exception as e:
        logger.error(f"Erreur recherche complète: {str(e)} - {http_request.state.request_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recherche multi-APIs"
        )

@app.get("/api/lieux-justice")
async def lieux_justice_endpoint(code_postal: str, request: Request):
    """Recherche de lieux de justice par code postal"""
    logger.info(f"Recherche lieux justice: {code_postal} - {request.state.request_id}")
    
    if not code_postal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le code postal est requis"
        )
    
    if not re.match(r'^\d{5}$', code_postal):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code postal invalide - doit contenir 5 chiffres"
        )
    
    client = get_client()
    
    try:
        resultats = await client.search_justice_back(
            "node/lieu_de_justice", 
            {"page[limit]": 15, "filter[code_postal]": code_postal}
        )
        return formater_lieux_justice_func(resultats)
        
    except Exception as e:
        logger.error(f"Erreur recherche lieux: {str(e)} - {request.state.request_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recherche des lieux de justice"
        )

# Fonctions utilitaires
def formater_resultats_judilibre_func(resultats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Formate les résultats Judilibre pour l'affichage"""
    formatted = []
    for item in resultats.get("results", [])[:5]:
        formatted.append({
            "titre": f"Arrêt {item.get('number', 'N/A')}",
            "juridiction": item.get("jurisdiction", "Inconnue"),
            "date": item.get("creation", item.get("date", "Date inconnue")),
            "chambre": (item.get("chamber") or {}).get("name", "N/A"),
            "formation": item.get("formation", "N/A"),
            "theme": item.get("theme", "N/A"),
            "resume": ((item.get("solution") or "Aucun résumé disponible")[:200] + "..."),
            "fiabilite": "✅ Source officielle Cour de Cassation",
            "source": f"judilibre:{item.get('id', item.get('number', 'unknown'))}"
        })
    return formatted

def formater_lieux_justice_func(resultats: Dict[str, Any]) -> Dict[str, Any]:
    """Formate les lieux de justice avec gestion robuste des champs GPS"""
    lieux = []
    for item in resultats.get("data", []):
        attributes = item.get("attributes", {})
        
        gps_lat = (attributes.get("field_ldj_gps_lat") or 
                   attributes.get("field_ldj_gps_latitude") or
                   attributes.get("field_ldj_lat"))
        
        gps_lng = (attributes.get("field_ldj_gps_lgn") or 
                   attributes.get("field_ldj_gps_lng") or 
                   attributes.get("field_ldj_gps_long") or
                   attributes.get("field_ldj_lng") or
                   attributes.get("field_ldj_long"))
        
        lieu = {
            "id": item.get("id"),
            "titre": attributes.get("title", "Lieu de justice"),
            "type": "Tribunal",
            "adresse": attributes.get("field_ldj_adresse", "Non renseigné"),
            "telephone": attributes.get("field_ldj_telephone", "Non renseigné"),
            "courriel": attributes.get("field_ldj_courriel", "Non renseigné"),
            "horaire": attributes.get("field_ldj_horaire", "Non renseigné"),
            "gps": {
                "lat": gps_lat,
                "lng": gps_lng
            },
            "source": f"justice_back:{item.get('id', 'unknown')}"
        }
        lieux.append(lieu)
    
    return {"lieux": lieux, "total": len(lieux)}

def formater_resultats_complets_func(results: List[Any], apis_includes: List[str]) -> Dict[str, Any]:
    """Formate les résultats complets multi-APIs"""
    formatted: Dict[str, Any] = {
        "legifrance": [],
        "judilibre": [],
        "justice_back": [],
        "analyse": {"timestamp": datetime.utcnow().isoformat() + "Z"}
    }
    
    result_index = 0
    
    if "legifrance" in apis_includes and result_index < len(results):
        if not isinstance(results[result_index], Exception) and isinstance(results[result_index], dict):
            data = results[result_index]
            formatted["legifrance"] = [
                {
                    "titre": r.get("title", "Sans titre"),
                    "nature": r.get("nature", "Inconnue"),
                    "date": r.get("date", "Date inconnue"),
                    "id": r.get("id"),
                    "resume": (r.get("content", "")[:150] + "...") if r.get("content") else "Aucun résumé"
                }
                for r in data.get("results", [])[:5]
            ]
            formatted["analyse"]["nombre_textes"] = len(formatted["legifrance"])
        result_index += 1
    
    if "judilibre" in apis_includes and result_index < len(results):
        if not isinstance(results[result_index], Exception) and isinstance(results[result_index], dict):
            data = results[result_index]
            formatted["judilibre"] = formater_resultats_judilibre_func(data)
            formatted["analyse"]["nombre_jurisprudence"] = len(formatted["judilibre"])
        result_index += 1
    
    if "justice_back" in apis_includes and result_index < len(results):
        if not isinstance(results[result_index], Exception) and isinstance(results[result_index], dict):
            data = results[result_index]
            justice_data = formater_lieux_justice_func(data)
            formatted["justice_back"] = justice_data.get("lieux", [])
            formatted["analyse"]["nombre_lieux"] = len(formatted["justice_back"])
    
    return formatted

def generer_recommandations_func(analyse_description: Dict[str, Any]) -> List[str]:
    """Génère des recommandations basées sur l'analyse des préjudices"""
    recommendations = []
    
    if analyse_description["complexite"] == "élevée":
        recommendations.append("📋 Dossier complexe nécessitant un avocat spécialisé en droit des victimes")
    
    if len(analyse_description["interactions"]) > 0:
        recommendations.append("⚖️ Préjudices multiples - expertise pluridisciplinaire recommandée")
    
    if any(p["categorie"] in ["psychique", "physique"] for p in analyse_description["prejudices_detectes"]):
        recommendations.append("🏥 Expertise médicale nécessaire pour quantification des préjudices corporels")
    
    if any(p["categorie"] in ["patrimonial", "professionnel"] for p in analyse_description["prejudices_detectes"]):
        recommendations.append("💼 Documentation comptable et professionnelle requise pour évaluation")
    
    recommendations.append("⏱️ Délai de prescription : généralement 10 ans pour les accidents corporels")
    recommendations.append("📄 Conservez tous les documents médicaux, factures et justificatifs")
    
    return recommendations

# Gestion des erreurs globales
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Gestionnaire global des erreurs HTTP"""
    logger.error(f"Erreur HTTP {exc.status_code}: {exc.detail} - {request.state.request_id}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request.state.request_id
        }
    )

@app.exception_handler(Exception)
async def custom_global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire global des exceptions non gérées"""
    logger.error(f"Erreur interne: {str(exc)} - {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Erreur interne du serveur",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "request_id": request.state.request_id
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
