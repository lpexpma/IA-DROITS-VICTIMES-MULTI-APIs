# app/services/api_clients.py
from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, List, Optional

from urllib.parse import urljoin
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
    raise ExternalAPIError(str(last_exc) if last_exc else "unknown error")


async def _get_oauth_token(
    session: aiohttp.ClientSession,
    token_url: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
    scope: Optional[str] = None,
) -> Optional[str]:
    """Flux OAuth2 client_credentials générique."""
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
        try:
            payload = await resp.json(content_type=None)
        except Exception:
            payload = {"text": await resp.text()}
        if 200 <= resp.status < 300:
            return payload.get("access_token")
        raise ExternalAPIError(f"OAuth token error ({resp.status}): {str(payload)[:200]}")


def _normalize_lieux_response(data: Any) -> List[Dict[str, Any]]:
    """JSON:API -> liste d'objets utiles {id, title, adresse, ...}."""
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        items: List[Dict[str, Any]] = []
        for it in data["data"]:
            attrs = (it or {}).get("attributes", {}) if isinstance(it, dict) else {}
            items.append(
                {
                    "id": (it or {}).get("id"),
                    "title": attrs.get("title"),
                    "adresse": attrs.get("field_ldj_adresse"),
                    "telephone": attrs.get("field_ldj_telephone"),
                    "courriel": attrs.get("field_ldj_courriel"),
                    "horaire": attrs.get("field_ldj_horaire"),
                    "gps_lat": attrs.get("field_ldj_gps_lat"),
                    "gps_lgn": attrs.get("field_ldj_gps_lgn"),
                }
            )
        return items
    return [{"raw": data}]


def _build_url(base: Optional[str], path_or_url: Optional[str]) -> str:
    """Si path_or_url est absolu (http...), retourne tel quel. Sinon, join(base, path)."""
    if not path_or_url:
        raise MissingEndpointError("endpoint manquant")
    if path_or_url.lower().startswith("http://") or path_or_url.lower().startswith("https://"):
        return path_or_url
    if not base:
        raise MissingEndpointError("base URL manquante")
    return urljoin(base.rstrip("/") + "/", path_or_url.lstrip("/"))


# -------------------------- Client unifié multi-APIs --------------------------
class ClientMultiAPIs:
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
        # Bases
        self.legifrance_base_url = legifrance_base_url
        self.judilibre_base_url = judilibre_base_url
        self.justice_back_base_url = justice_back_base_url

        # Auth
        self.legifrance_client_id = legifrance_client_id
        self.legifrance_client_secret = legifrance_client_secret
        self.judilibre_api_key = judilibre_api_key
        self.justice_back_client_id = justice_back_client_id
        self.justice_back_client_secret = justice_back_client_secret

        # Endpoints explicites (env)
        self.legifrance_token_url = os.getenv("LEGIFRANCE_TOKEN_URL") or None
        self.legifrance_search_url = os.getenv("LEGIFRANCE_SEARCH_URL") or None

        self.judilibre_search_url = os.getenv("JUDILIBRE_SEARCH_URL") or None

        self.justice_back_token_url = os.getenv("JUSTICE_BACK_TOKEN_URL") or None
        self.justice_back_lieux_url = os.getenv("JUSTICE_BACK_LIEUX_URL") or None

        self.debug = debug

    # -------------------------- méthodes publiques --------------------------
    async def test_apis(self) -> Dict[str, Any]:
        """Vérifie la configuration et tente un ping minimal."""
        out: Dict[str, Any] = {}
        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            # Légifrance
            legi_info: Dict[str, Any] = {"configured": bool(self.legifrance_search_url), "reachable": None, "note": None}
            if not self.legifrance_search_url:
                legi_info["note"] = "Je ne sais pas (LEGIFRANCE_SEARCH_URL manquant)"
            else:
                try:
                    headers = await self._headers_legifrance(session)
                    await _fetch_json(session, "GET", self.legifrance_search_url, headers=headers, params={"q": "test"})
                    legi_info["reachable"] = True
                except Exception as e:
                    legi_info["reachable"] = False
                    legi_info["note"] = str(e)[:200]
            out["legifrance"] = legi_info

            # Judilibre
            judi_info: Dict[str, Any] = {"configured": bool(self.judilibre_search_url), "reachable": None, "note": None}
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

            # Justice Back (JSON:API)
            jb_info: Dict[str, Any] = {"configured": bool(self.justice_back_lieux_url), "reachable": None, "note": None}
            if not self.justice_back_lieux_url:
                jb_info["note"] = "Je ne sais pas (JUSTICE_BACK_LIEUX_URL manquant)"
            else:
                try:
                    url = _build_url(self.justice_back_base_url, self.justice_back_lieux_url)
                    headers = await self._headers_justice_back(session)
                    headers["Accept"] = "application/vnd.api+json"
                    await _fetch_json(
                        session,
                        "GET",
                        url,
                        headers=headers,
                        params={"page[limit]": "1", "page[offset]": "0"},
                    )
                    jb_info["reachable"] = True
                except Exception as e:
                    jb_info["reachable"] = False
                    jb_info["note"] = str(e)[:200]
            out["justice_back"] = jb_info

        out["status"] = "ok"
        return out

    async def get_lieux_justice(self, code_postal: str | None = None) -> List[Dict[str, Any]]:
        """
        Récupère les lieux de justice via JSON:API.
        Si code_postal est fourni, filtre *côté app* (adresse/titre contient le CP).
        """
        if not self.justice_back_base_url or not self.justice_back_lieux_url:
            raise MissingEndpointError("Je ne sais pas: base ou endpoint Justice Back manquant")

        url = _build_url(self.justice_back_base_url, self.justice_back_lieux_url)

        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            headers = await self._headers_justice_back(session)
            headers["Accept"] = "application/vnd.api+json"

            all_items: List[Dict[str, Any]] = []
            limit = 50
            offset = 0

            while True:
                params = {
                    "page[limit]": str(limit),
                    "page[offset]": str(offset),
                    # include optionnel (ex: type organisme)
                    "include": "field_ldj_type_organisme",
                    "jsonapi_include": "1",
                }
                data = await _fetch_json(session, "GET", url, headers=headers, params=params)
                batch = _normalize_lieux_response(data)
                all_items.extend(batch)

                if len(batch) < limit:
                    break
                offset += limit

            if code_postal:
                cp = str(code_postal)
                all_items = [
                    it
                    for it in all_items
                    if (it.get("adresse") and cp in str(it["adresse"])) or (it.get("title") and cp in str(it["title"]))
                ]

            return all_items

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
        # Réutilise la logique principale pour rester cohérent
        data = await self.get_lieux_justice(code_postal=code_postal)
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
