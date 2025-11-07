# app/services/api_clients.py
from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, List, Optional, Tuple

import aiohttp


# ----------------------------- Exceptions propres -----------------------------
class ExternalAPIError(RuntimeError):
    pass


class MissingEndpointError(RuntimeError):
    pass


# ----------------------------- Utilitaires HTTP -------------------------------
_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)  # 15s global
_RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


async def _fetch_json(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    max_retries: int = 2,
) -> Any:
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            async with session.request(method, url, headers=headers, params=params, json=json) as resp:
                ct = resp.headers.get("content-type", "")
                if resp.status in _RETRY_STATUS:
                    text = await resp.text()
                    raise ExternalAPIError(f"HTTP {resp.status} on {url}: {text[:200]}")
                if "application/json" not in ct:
                    text = await resp.text()
                    # on accepte une payload non-JSON si l’API renvoie ainsi ; mais ici on standardise
                    return {"status": resp.status, "content_type": ct, "text": text}
                data = await resp.json(content_type=None)
                if 200 <= resp.status < 300:
                    return data
                raise ExternalAPIError(f"HTTP {resp.status} on {url}: {str(data)[:200]}")
        except (aiohttp.ClientError, asyncio.TimeoutError, ExternalAPIError) as exc:
            last_exc = exc
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            raise ExternalAPIError(f"request failed after retries: {exc}") from exc
    # ne devrait pas arriver
    raise ExternalAPIError(str(last_exc) if last_exc else "unknown error")


async def _get_oauth_token(
    session: aiohttp.ClientSession,
    token_url: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
    scope: Optional[str] = None,
) -> Optional[str]:
    """
    Flux OAuth2 client_credentials générique.
    Si token_url ou credentials manquants -> retourne None (l’appelant gère).
    """
    if not token_url or not client_id or not client_secret:
        return None
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if scope:
        data["scope"] = scope
    async with session.post(token_url, data=data) as resp:
        # on accepte JSON ou x-www-form-urlencoded
        try:
            payload = await resp.json(content_type=None)
        except Exception:
            payload = {"text": await resp.text()}
        if 200 <= resp.status < 300:
            # format attendu: { "access_token": "...", "token_type": "Bearer", ... }
            token = payload.get("access_token")
            return token
        raise ExternalAPIError(f"OAuth token error ({resp.status}): {str(payload)[:200]}")


# -------------------------- Client unifié multi-APIs --------------------------
class ClientMultiAPIs:
    """
    Client unifié configurable via variables d’environnement.
    - Ne suppose AUCUN endpoint par défaut (à remplir côté Render).
    - Supporte OAuth2 client_credentials là où c’est nécessaire.
    """

    def __init__(
        self,
        legifrance_base_url: Optional[str] = None,
        legifrance_client_id: Optional[str] = None,
        legifrance_client_secret: Optional[str] = None,
        judilibre_base_url: Optional[str] = None,
        judilibre_api_key: Optional[str] = None,
        justice_back_base_url: Optional[str] = None,
        justice_back_client_id: Optional[str] = None,
        justice_back_client_secret: Optional[str] = None,
        debug: bool = False,
    ) -> None:
        # Bases (potentiellement utiles ailleurs dans ton app)
        self.legifrance_base_url = legifrance_base_url
        self.judilibre_base_url = judilibre_base_url
        self.justice_back_base_url = justice_back_base_url

        # Auth
        self.legifrance_client_id = legifrance_client_id
        self.legifrance_client_secret = legifrance_client_secret
        self.judilibre_api_key = judilibre_api_key
        self.justice_back_client_id = justice_back_client_id
        self.justice_back_client_secret = justice_back_client_secret

        # Endpoints explicites (à fournir côté Render)
        self.legifrance_token_url = os.getenv("LEGIFRANCE_TOKEN_URL") or None
        self.legifrance_search_url = os.getenv("LEGIFRANCE_SEARCH_URL") or None

        self.judilibre_search_url = os.getenv("JUDILIBRE_SEARCH_URL") or None

        self.justice_back_token_url = os.getenv("JUSTICE_BACK_TOKEN_URL") or None
        self.justice_back_lieux_url = os.getenv("JUSTICE_BACK_LIEUX_URL") or None

        self.debug = debug

    # -------------------------- méthodes publiques --------------------------
    async def test_apis(self) -> Dict[str, Any]:
        """
        Vérifie la configuration et tente un appel minimal (sans faire d’hypothèses).
        - Renvoie 'Je ne sais pas' si un endpoint requis est manquant.
        """
        out: Dict[str, Any] = {}

        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            # Légifrance
            legi_info: Dict[str, Any] = {
                "configured": bool(self.legifrance_search_url),
                "reachable": None,
                "note": None,
            }
            if not self.legifrance_search_url:
                legi_info["note"] = "Je ne sais pas (LEGIFRANCE_SEARCH_URL manquant)"
            else:
                try:
                    headers = await self._headers_legifrance(session)
                    # ping GET sans param, juste pour statut (si l’API l’autorise)
                    await _fetch_json(session, "GET", self.legifrance_search_url, headers=headers)
                    legi_info["reachable"] = True
                except Exception as e:
                    legi_info["reachable"] = False
                    legi_info["note"] = str(e)[:200]
            out["legifrance"] = legi_info

            # Judilibre
            judi_info: Dict[str, Any] = {
                "configured": bool(self.judilibre_search_url),
                "reachable": None,
                "note": None,
            }
            if not self.judilibre_search_url:
                judi_info["note"] = "Je ne sais pas (JUDILIBRE_SEARCH_URL manquant)"
            else:
                try:
                    headers = await self._headers_judilibre()
                    await _fetch_json(session, "GET", self.judilibre_search_url, headers=headers, params={"q": "test"})
                    judi_info["reachable"] = True
                except Exception as e:
                    judi_info["reachable"] = False
                    judi_info["note"] = str(e)[:200]
            out["judilibre"] = judi_info

            # Justice Back
            jb_info: Dict[str, Any] = {
                "configured": bool(self.justice_back_lieux_url),
                "reachable": None,
                "note": None,
            }
            if not self.justice_back_lieux_url:
                jb_info["note"] = "Je ne sais pas (JUSTICE_BACK_LIEUX_URL manquant)"
            else:
                try:
                    headers = await self._headers_justice_back(session)
                    await _fetch_json(session, "GET", self.justice_back_lieux_url, headers=headers, params={"code_postal": "75001"})
                    jb_info["reachable"] = True
                except Exception as e:
                    jb_info["reachable"] = False
                    jb_info["note"] = str(e)[:200]
            out["justice_back"] = jb_info

        out["status"] = "ok"
        return out

    async def get_lieux_justice(self, code_postal: str) -> List[Dict[str, Any]]:
        if not self.justice_back_lieux_url:
            raise MissingEndpointError("Je ne sais pas: JUSTICE_BACK_LIEUX_URL non défini")
        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            headers = await self._headers_justice_back(session)
            data = await _fetch_json(
                session, "GET", self.justice_back_lieux_url, headers=headers, params={"code_postal": code_postal}
            )
        # on suppose un tableau JSON ; si différent, adapte ici
        if isinstance(data, dict) and "results" in data:
            return data["results"]  # type: ignore[return-value]
        if isinstance(data, list):
            return data  # type: ignore[return-value]
        return [{"raw": data}]

    async def recherche_complete(
        self,
        description_situation: str,
        include_apis: Optional[List[str]] = None,
        code_postal: Optional[str] = None,
    ) -> Dict[str, Any]:
        targets = include_apis or ["legifrance", "judilibre", "justice_back"]
        results: List[Dict[str, Any]] = []

        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            tasks: List[asyncio.Task] = []

            if "legifrance" in targets and self.legifrance_search_url:
                tasks.append(asyncio.create_task(self._search_legifrance(session, description_situation)))

            if "judilibre" in targets and self.judilibre_search_url:
                tasks.append(asyncio.create_task(self._search_judilibre(session, description_situation)))

            if "justice_back" in targets and self.justice_back_lieux_url and code_postal:
                tasks.append(asyncio.create_task(self._search_justice_back(session, code_postal)))

            if not tasks:
                # Aucun endpoint configuré → on l’explique
                return {
                    "description": description_situation,
                    "sources": targets,
                    "code_postal": code_postal,
                    "resultats": [],
                    "note": "Je ne sais pas : aucun endpoint configuré pour les sources demandées.",
                }

            done = await asyncio.gather(*tasks, return_exceptions=True)
            for item in done:
                if isinstance(item, Exception):
                    results.append({"error": str(item)[:300]})
                else:
                    results.append(item)  # type: ignore[arg-type]

        return {
            "description": description_situation,
            "sources": targets,
            "code_postal": code_postal,
            "resultats": results,
        }

    # ----------------------- sous-appels spécifiques -----------------------
    async def _search_legifrance(self, session: aiohttp.ClientSession, query: str) -> Dict[str, Any]:
        if not self.legifrance_search_url:
            raise MissingEndpointError("Je ne sais pas: LEGIFRANCE_SEARCH_URL non défini")
        headers = await self._headers_legifrance(session)
        data = await _fetch_json(session, "GET", self.legifrance_search_url, headers=headers, params={"q": query})
        return {"source": "legifrance", "data": data}

    async def _search_judilibre(self, session: aiohttp.ClientSession, query: str) -> Dict[str, Any]:
        if not self.judilibre_search_url:
            raise MissingEndpointError("Je ne sais pas: JUDILIBRE_SEARCH_URL non défini")
        headers = await self._headers_judilibre()
        data = await _fetch_json(session, "GET", self.judilibre_search_url, headers=headers, params={"q": query})
        return {"source": "judilibre", "data": data}

    async def _search_justice_back(self, session: aiohttp.ClientSession, code_postal: str) -> Dict[str, Any]:
        if not self.justice_back_lieux_url:
            raise MissingEndpointError("Je ne sais pas: JUSTICE_BACK_LIEUX_URL non défini")
        headers = await self._headers_justice_back(session)
        data = await _fetch_json(
            session, "GET", self.justice_back_lieux_url, headers=headers, params={"code_postal": code_postal}
        )
        return {"source": "justice_back", "data": data}

    # ------------------------------ headers/auth ------------------------------
    async def _headers_legifrance(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        token = await _get_oauth_token(
            session,
            token_url=self.legifrance_token_url,
            client_id=self.legifrance_client_id,
            client_secret=self.legifrance_client_secret,
        )
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _headers_judilibre(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.judilibre_api_key:
            # selon l’API, c’est parfois Authorization: Bearer <key>, parfois X-API-Key...
            # on choisit un header générique et on permettra d’adapter vite :
            headers["Authorization"] = f"Bearer {self.judilibre_api_key}"
        return headers

    async def _headers_justice_back(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        token = await _get_oauth_token(
            session,
            token_url=self.justice_back_token_url,
            client_id=self.justice_back_client_id,
            client_secret=self.justice_back_client_secret,
        )
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
