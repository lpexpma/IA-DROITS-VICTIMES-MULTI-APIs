# app/services/api_clients.py

import os
import aiohttp
from typing import Any, Dict, List, Optional


class ClientMultiAPIs:
    """
    Client unifié pour interroger plusieurs APIs publiques :
    - Légifrance (textes juridiques)
    - Judilibre (jurisprudence)
    - Justice Back (annuaire des lieux de justice)
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
        self.legifrance_base_url = legifrance_base_url
        self.legifrance_client_id = legifrance_client_id
        self.legifrance_client_secret = legifrance_client_secret

        self.judilibre_base_url = judilibre_base_url
        self.judilibre_api_key = judilibre_api_key

        self.justice_back_base_url = justice_back_base_url
        self.justice_back_client_id = justice_back_client_id
        self.justice_back_client_secret = justice_back_client_secret

        self.debug = debug

    # ---------------------------------------------------------------
    # MÉTHODE 1 — Vérifier la connectivité générale
    # ---------------------------------------------------------------
    async def test_apis(self) -> Dict[str, Any]:
        return {
            "legifrance": bool(self.legifrance_base_url),
            "judilibre": bool(self.judilibre_base_url),
            "justice_back": bool(self.justice_back_base_url),
            "status": "ok",
        }

    # ---------------------------------------------------------------
    # MÉTHODE 2 — Simulation recherche de lieux de justice
    # ---------------------------------------------------------------
    async def get_lieux_justice(self, code_postal: str) -> List[Dict[str, Any]]:
        # En version de test, on renvoie une réponse fictive
        return [
            {
                "nom": "Tribunal judiciaire (exemple)",
                "code_postal": code_postal,
                "ville": "Exemple-ville",
                "adresse": "1 rue de la Loi",
            }
        ]

    # ---------------------------------------------------------------
    # MÉTHODE 3 — Simulation d’orchestration multi-APIs
    # ---------------------------------------------------------------
    async def recherche_complete(
        self,
        description_situation: str,
        include_apis: Optional[List[str]] = None,
        code_postal: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = {
            "description": description_situation,
            "sources": include_apis or ["legifrance", "judilibre", "justice_back"],
            "code_postal": code_postal,
            "resultats": [],
        }

        # Exemple de logique de simulation
        if "legifrance" in data["sources"]:
            data["resultats"].append({"source": "legifrance", "resume": "Articles du code civil liés à la situation."})
        if "judilibre" in data["sources"]:
            data["resultats"].append({"source": "judilibre", "resume": "Jurisprudence pertinente trouvée."})
        if "justice_back" in data["sources"] and code_postal:
            data["resultats"].append(
                {
                    "source": "justice_back",
                    "resume": f"Lieux de justice proches du code postal {code_postal}.",
                }
            )

        return data
