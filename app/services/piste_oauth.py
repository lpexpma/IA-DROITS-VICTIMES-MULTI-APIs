"""Utilities for retrieving OAuth tokens from the French PISTE platform.

This module exposes a small command line interface so developers can test
that their credentials are correctly configured.  It intentionally avoids
outputting secrets in clear text and behaves safely when the application is
running in demo mode (the default configuration bundled with this repository).
"""
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional

import requests

try:  # Local imports are optional during documentation builds.
    from app.config import CFG
except ImportError as exc:  # pragma: no cover - executed only in unusual envs.
    raise RuntimeError("Unable to import application configuration") from exc

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ServiceSettings:
    """Configuration required to request an OAuth token for a service."""

    name: str
    token_url: str
    client_id: Optional[str]
    client_secret: Optional[str]
    scope: Optional[str] = None

    def obfuscated_client_id(self) -> str:
        """Return a user friendly, but anonymised, version of the client id."""

        if not self.client_id:
            return "<non configuré>"
        if len(self.client_id) <= 6:
            return self.client_id
        return f"{self.client_id[:3]}…{self.client_id[-3:]}"


class PisteOAuthError(RuntimeError):
    """Raised when the PISTE platform cannot provide an OAuth token."""


class PisteOAuthClient:
    """Minimal wrapper around :mod:`requests` for the PISTE OAuth workflow."""

    def __init__(self, *, timeout: Optional[int] = None, session: Optional[requests.Session] = None) -> None:
        self._timeout = timeout or getattr(CFG, "HTTP_TIMEOUT", 15)
        self._session = session or requests.Session()

    def fetch_token(self, settings: ServiceSettings) -> Mapping[str, object]:
        """Request a token for ``settings``.

        Parameters
        ----------
        settings:
            Service definition containing the OAuth credentials.

        Returns
        -------
        Mapping[str, object]
            The JSON payload returned by the OAuth server.
        """

        if not settings.token_url:
            raise PisteOAuthError(f"Aucune URL de token fournie pour le service '{settings.name}'.")
        if not settings.client_id or not settings.client_secret:
            raise PisteOAuthError(
                "Identifiants OAuth manquants. Vérifiez les variables d'environnement ou la configuration."
            )

        payload: MutableMapping[str, str] = {"grant_type": "client_credentials"}
        if settings.scope:
            payload["scope"] = settings.scope

        try:
            response = self._session.post(
                settings.token_url,
                data=payload,
                auth=(settings.client_id, settings.client_secret),
                timeout=self._timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network layer is not unit tested here.
            raise PisteOAuthError(f"Requête OAuth échouée: {exc}") from exc

        if response.status_code >= 400:
            LOGGER.debug("OAuth error response: %s", response.text)
            raise PisteOAuthError(self._format_error(settings.name, response))

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive branch.
            raise PisteOAuthError("Réponse OAuth invalide (JSON introuvable).") from exc

    @staticmethod
    def _format_error(service_name: str, response: requests.Response) -> str:
        """Generate a readable error message for failed requests."""

        snippet = response.text.strip()
        if len(snippet) > 250:
            snippet = f"{snippet[:247]}…"
        return (
            f"Erreur OAuth pour '{service_name}' (HTTP {response.status_code}). "
            "Détails fournis par l'API: "
            f"{snippet or '<aucun détail>'}"
        )


def build_service_settings(config: object) -> Dict[str, ServiceSettings]:
    """Convert the global configuration object into :class:`ServiceSettings`."""

    services = {
        "legifrance": ServiceSettings(
            name="legifrance",
            token_url=getattr(config, "LEGIFRANCE_TOKEN_URL", ""),
            client_id=getattr(config, "LEGIFRANCE_CLIENT_ID", None),
            client_secret=getattr(config, "LEGIFRANCE_CLIENT_SECRET", None),
            scope=getattr(config, "LEGIFRANCE_SCOPE", None),
        ),
        "judilibre": ServiceSettings(
            name="judilibre",
            token_url=getattr(config, "JUDILIBRE_TOKEN_URL", ""),
            client_id=getattr(config, "JUDILIBRE_CLIENT_ID", None),
            client_secret=getattr(config, "JUDILIBRE_CLIENT_SECRET", None),
            scope=getattr(config, "JUDILIBRE_SCOPE", None),
        ),
        "justice_back": ServiceSettings(
            name="justice_back",
            token_url=getattr(config, "JUSTICE_BACK_TOKEN_URL", ""),
            client_id=getattr(config, "JUSTICE_BACK_CLIENT_ID", None),
            client_secret=getattr(config, "JUSTICE_BACK_CLIENT_SECRET", None),
            scope=getattr(config, "JUSTICE_BACK_SCOPE", None),
        ),
    }

    return services


def _redact_token(token: Optional[str]) -> str:
    if not token:
        return "<vide>"
    if len(token) <= 8:
        return "••••"
    return f"{token[:4]}…{token[-4:]}"


def _select_services(requested: Iterable[str], available: Mapping[str, ServiceSettings]) -> List[ServiceSettings]:
    requested = list(requested)
    if not requested or "all" in requested:
        return list(available.values())
    missing = [name for name in requested if name not in available]
    if missing:
        raise ValueError(
            "Service(s) inconnu(s): " + ", ".join(sorted(missing)) + ". "
            "Services disponibles: " + ", ".join(sorted(available))
        )
    return [available[name] for name in requested]


def main(argv: Optional[List[str]] = None) -> int:
    """Entry-point for the ``python -m app.services.piste_oauth`` command."""

    parser = argparse.ArgumentParser(description="Client OAuth PISTE")
    parser.add_argument(
        "services",
        nargs="*",
        help="Services à tester (legifrance, judilibre, justice_back). Laisser vide pour tous.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Affiche le résultat en JSON brut (tokens partiellement masqués).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Effectue les requêtes même si la configuration est en mode démonstration.",
    )

    args = parser.parse_args(argv)

    services = build_service_settings(CFG)
    chosen_services = _select_services(args.services, services)

    if getattr(CFG, "MODE_DEMO", False) and not args.force:
        print("Configuration en mode DÉMO - aucune requête réseau n'a été effectuée.")
        print("Utilisez --force pour tester les appels OAuth malgré tout.")
        for service in chosen_services:
            print(f"- {service.name}: client_id={service.obfuscated_client_id()}")
        return 0

    client = PisteOAuthClient()
    results: Dict[str, Mapping[str, object]] = {}

    for service in chosen_services:
        try:
            payload = client.fetch_token(service)
        except PisteOAuthError as exc:
            print(f"[{service.name}] ❌ {exc}")
            continue

        results[service.name] = payload
        if args.json:
            continue

        access_token = _redact_token(str(payload.get("access_token", "")))
        expires_in = payload.get("expires_in", "?")
        token_type = payload.get("token_type", "?")
        print(f"[{service.name}] ✅ token_type={token_type} expires_in={expires_in}s token={access_token}")

    if args.json:
        sanitized = {
            name: {
                **data,
                "access_token": _redact_token(str(data.get("access_token", ""))),
            }
            for name, data in results.items()
        }
        print(json.dumps(sanitized, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
