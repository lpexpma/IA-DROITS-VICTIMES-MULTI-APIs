# app/services/api_clients.py
import aiohttp
import asyncio
import os
import json
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

class ClientMultiAPIs:
    """
    Client robuste pour les APIs PISTE (Légifrance, Justice Back, Judilibre)
    Version 3.1.8 - Configuration PISTE SANDBOX
    """
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None, 
                 semaphore: Optional[asyncio.Semaphore] = None, max_concurrent: int = 10):
        """
        Initialise le client multi-APIs avec configuration PISTE
        """
        # Sémaphore global ou local pour limiter la concurrence
        self.semaphore = semaphore or asyncio.Semaphore(max_concurrent)
        
        # Timeouts affinés pour meilleur diagnostic
        connector = aiohttp.TCPConnector(
            limit=max_concurrent, 
            limit_per_host=5,
            use_dns_cache=True
        )
        self.session = session or aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=20),
            connector=connector
        )
        
        self.tokens: Dict[str, str] = {}
        self.token_expiry: Dict[str, datetime] = {}
        
        # Configuration PISTE SANDBOX
        self.config = {
            "legifrance": {
                "base_url": os.getenv("LEGIFRANCE_API_BASE", "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"),
                "client_id": os.getenv("LEGIFRANCE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
                "client_secret": os.getenv("LEGIFRANCE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
                "token_url": os.getenv("LEGIFRANCE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token")
            },
            "justice_back": {
                "base_url": os.getenv("JUSTICE_BACK_API_BASE", "https://sandbox-api.piste.gouv.fr/minju/v1/Justiceback"),
                "client_id": os.getenv("JUSTICE_BACK_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
                "client_secret": os.getenv("JUSTICE_BACK_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
                "token_url": os.getenv("JUSTICE_BACK_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token")
            },
            "judilibre": {
                "base_url": os.getenv("JUDILIBRE_API_BASE", "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"),
                "client_id": os.getenv("JUDILIBRE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
                "client_secret": os.getenv("JUDILIBRE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
                "token_url": os.getenv("JUDILIBRE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token")
            }
        }

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - fermeture propre"""
        await self.close()

    async def close(self):
        """Ferme la session HTTP de manière propre"""
        if not self.session.closed:
            await self.session.close()
            logger.info("Session HTTP fermée")

    def _parse_retry_after(self, headers: Dict[str, str]) -> int:
        """
        Parse Retry-After header (seconds or HTTP-date RFC 7231)
        """
        val = headers.get('Retry-After')
        if not val:
            return 1
            
        try:
            # Format seconds
            return max(1, int(val))
        except ValueError:
            # Format HTTP-date (RFC 7231)
            try:
                dt = parsedate_to_datetime(val)
                now = datetime.utcnow().replace(tzinfo=dt.tzinfo)
                delay = max(1, int((dt - now).total_seconds()))
                logger.info(f"Retry-After HTTP-date parsé: {delay}s")
                return delay
            except Exception as e:
                logger.warning(f"Impossible de parser Retry-After: {val}, erreur: {e}")
                return 1

    async def _get_piste_token(self, api_name: str) -> str:
        """
        Récupère le token OAuth2 pour une API PISTE avec gestion d'expiration
        """
        now = datetime.now()
        if (api_name in self.tokens and 
            api_name in self.token_expiry and 
            now < self.token_expiry[api_name]):
            logger.debug(f"Token {api_name} valide réutilisé")
            return self.tokens[api_name]
            
        config = self.config[api_name]
        auth = aiohttp.BasicAuth(config["client_id"], config["client_secret"])
        
        status, data, text = await self._request_json_with_retry(
            "POST", 
            config["token_url"],
            retry_non_idempotent=True,
            auth=auth, 
            data={'grant_type': 'client_credentials', 'scope': 'openid'}
        )
        
        if status == 200 and data:
            self.tokens[api_name] = data['access_token']
            expires_in = max(60, data.get('expires_in', 3600) - 300)
            self.token_expiry[api_name] = now + timedelta(seconds=expires_in)
            logger.info(f"Token {api_name} obtenu avec succès")
            return self.tokens[api_name]
        else:
            logger.error(f"Erreur auth {api_name}: {status}")
            raise Exception(f"Erreur auth {api_name}: {status}")

    async def _request_json_with_retry(self, method: str, url: str, 
                                     retry_non_idempotent: bool = False,
                                     **kwargs) -> Tuple[int, Optional[Dict[str, Any]], Optional[str]]:
        """
        Effectue une requête HTTP avec retry automatique et gestion d'erreurs robuste
        """
        max_retries = 3
        if method.upper() in {"POST", "PATCH", "PUT"} and not retry_non_idempotent:
            max_retries = 1
            
        base_delay = 1

        for attempt in range(max_retries):
            async with self.semaphore:
                resp = None
                try:
                    # Logs sécurisés (sans query params sensibles)
                    url_path = url.split('?')[0]
                    logger.info(f"Requête {method} {url_path} - tentative {attempt + 1}/{max_retries}")
                    
                    # Effectue la requête
                    resp = await self.session.request(method, url, **kwargs)
                    status = resp.status
                    
                    # Lecture UNIQUE du corps
                    ctype = (resp.headers.get('content-type') or '').lower()
                    
                    # Lire une seule fois le corps
                    raw = await resp.read()
                    charset = resp.charset or 'utf-8'
                    text_content = raw.decode(charset, errors='replace')

                    json_data: Optional[Dict[str, Any]] = None
                    # Support étendu des Content-Type JSON
                    if ('application/json' in ctype or ctype.endswith('+json')) and text_content.strip():
                        try:
                            json_data = json.loads(text_content)
                        except json.JSONDecodeError as json_error:
                            logger.warning(f"[JSON parse] {method} {url_path} -> {json_error}")

                    # Logs sécurisés (taille plutôt que contenu)
                    body_size = len(raw)
                    log_level = logging.INFO if status < 400 else logging.WARNING
                    logger.log(log_level, f"Réponse {method} {url_path} -> {status} ({body_size} bytes)")

                    # Gestion 429 avec Retry-After parsing robuste
                    if status == 429:
                        headers_dict = dict(resp.headers)
                        retry_after = self._parse_retry_after(headers_dict)
                        logger.warning(f"HTTP 429 {method} {url_path} – retry après {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    # Retry sur erreurs 5xx avec jitter
                    if 500 <= status < 600 and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.25)
                        logger.warning(f"HTTP {status} {method} {url_path} – retry dans {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue

                    return status, json_data, text_content

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(f"Erreur réseau {type(e).__name__} – tentative {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.25)
                        logger.info(f"Attente avant retry: {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    logger.error(f"Échec final après {max_retries} tentatives: {e}")
                    raise
                finally:
                    if resp:
                        resp.release()
        
        return 500, None, "Erreur inattendue"

    async def get_legifrance_token(self) -> str:
        """Récupère le token OAuth2 pour Légifrance"""
        return await self._get_piste_token("legifrance")

    async def get_justice_back_token(self) -> str:
        """Récupère le token OAuth2 pour Justice Back"""
        return await self._get_piste_token("justice_back")

    async def search_legifrance(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue une recherche dans Légifrance
        """
        token = await self.get_legifrance_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        status, data, text = await self._request_json_with_retry(
            "POST",
            f"{self.config['legifrance']['base_url']}/search",
            headers=headers,
            json=query
        )
        
        if status == 200 and data:
            return data
        elif status == 401:
            logger.warning("Token Légifrance expiré, régénération...")
            self.tokens.pop("legifrance", None)
            return await self.search_legifrance(query)
        else:
            logger.error(f"Erreur recherche Légifrance: {status}")
            raise Exception(f"Erreur recherche Légifrance: {status}")

    async def search_judilibre(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une recherche dans Judilibre (OAuth2 PISTE)
        """
        token = await self._get_piste_token("judilibre")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        url = f"{self.config['judilibre']['base_url']}/{endpoint}"
        
        status, data, text = await self._request_json_with_retry(
            "GET", url, headers=headers, params=params
        )
        
        if status == 200 and data:
            return data
        elif status == 401:
            logger.warning("Token Judilibre expiré, régénération...")
            self.tokens.pop("judilibre", None)
            return await self.search_judilibre(endpoint, params)
        else:
            logger.error(f"Erreur recherche Judilibre: {status}")
            raise Exception(f"Erreur recherche Judilibre: {status}")

    async def search_justice_back(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une recherche dans Justice Back
        """
        token = await self.get_justice_back_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }
        
        url = f"{self.config['justice_back']['base_url']}/{endpoint}"
        
        status, data, text = await self._request_json_with_retry(
            "GET", url, headers=headers, params=params
        )
        
        if status == 200 and data:
            return data
        elif status == 401:
            logger.warning("Token Justice Back expiré, régénération...")
            self.tokens.pop("justice_back", None)
            return await self.search_justice_back(endpoint, params)
        else:
            logger.error(f"Erreur recherche Justice Back: {status}")
            raise Exception(f"Erreur recherche Justice Back: {status}")

    async def health_check(self) -> Dict[str, bool]:
        """
        Vérifie la santé de toutes les APIs PISTE
        """
        health_status: Dict[str, bool] = {}
        
        try:
            await self.get_legifrance_token()
            health_status["legifrance"] = True
        except Exception as e:
            logger.error(f"Health check Légifrance échoué: {e}")
            health_status["legifrance"] = False
            
        try:
            await self.get_justice_back_token()
            health_status["justice_back"] = True
        except Exception as e:
            logger.error(f"Health check Justice Back échoué: {e}")
            health_status["justice_back"] = False
            
        try:
            await self.search_judilibre("search", {"q": "test", "size": 1})
            health_status["judilibre"] = True
        except Exception as e:
            logger.error(f"Health check Judilibre échoué: {e}")
            health_status["judilibre"] = False
            
        return health_status
    
    