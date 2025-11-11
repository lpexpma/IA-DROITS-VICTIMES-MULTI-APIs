"""Moteur de recherche persistant pour OLIVIA.

Le but de ce module est de fournir une façade unique pour orchestrer les
différentes recherches métiers (Légifrance, Judilibre, Justice Back) tout en
réutilisant un cache persistant pour éviter de recalculer des résultats
identiques.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import RechercheCache, db
from app.services.api_clients import APIClients


DEFAULT_CACHE_TTL = timedelta(minutes=30)


@dataclass
class AnalyseSituation:
    """Résultat d'analyse d'une situation utilisateur."""

    situation: str
    strategie_detectee: str
    mots_cles: Tuple[str, ...]
    resume: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "situation": self.situation,
            "strategie_detectee": self.strategie_detectee,
            "mots_cles": list(self.mots_cles),
            "resume": self.resume,
        }


class MoteurRecherchePersistent:
    """Coordonne les recherches juridiques avec mise en cache."""

    def __init__(self, config):
        self.config = config
        self.clients = APIClients(config)
        self.cache_ttl = DEFAULT_CACHE_TTL

    # ------------------------------------------------------------------
    # Entrée principale
    # ------------------------------------------------------------------
    def analyser_et_rechercher_persistent(
        self,
        situation: str,
        strategie: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        situation = situation.strip()
        if not situation:
            raise ValueError("La situation ne peut pas être vide")

        analyse = self._analyser_situation(situation, strategie)
        query_hash = self.clients.compute_hash(
            {
                "situation": analyse.situation,
                "strategie": analyse.strategie_detectee,
            }
        )

        cached = self._charger_depuis_cache(user_id, query_hash)
        if cached is not None:
            cached.setdefault("from_cache", True)
            return cached

        legifrance = self._rechercher_legifrance(analyse)
        judilibre = self._rechercher_judilibre(analyse)
        justice_back = self._rechercher_justice_back(analyse)

        resultats = {
            "situation": analyse.situation,
            "strategie": strategie or analyse.strategie_detectee,
            "analyse": {
                **analyse.to_dict(),
                "nombre_textes": len(legifrance.get("results", [])),
                "nombre_jurisprudence": len(judilibre.get("results", [])),
                "nombre_lieux": len(justice_back.get("results", [])),
            },
            "legifrance": legifrance,
            "judilibre": judilibre,
            "justice_back": justice_back,
            "timestamp": datetime.utcnow().isoformat(),
            "from_cache": False,
        }

        self._enregistrer_cache(user_id, query_hash, analyse, resultats)
        return resultats

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------
    def _charger_depuis_cache(self, user_id: str, query_hash: str) -> Optional[Dict[str, Any]]:
        with db.session() as session:
            entry = (
                session.execute(
                    select(RechercheCache)
                    .where(
                        RechercheCache.user_id == user_id,
                        RechercheCache.query_hash == query_hash,
                    )
                    .order_by(RechercheCache.created_at.desc())
                )
                .scalars()
                .first()
            )

            if entry is None:
                return None

            if entry.created_at < datetime.utcnow() - self.cache_ttl:
                return None

            # Le contenu JSON est déjà un dict Python
            return dict(entry.resultats)

    def _enregistrer_cache(
        self,
        user_id: str,
        query_hash: str,
        analyse: AnalyseSituation,
        resultats: Dict[str, Any],
    ) -> None:
        with db.session() as session:
            cache = RechercheCache(
                user_id=user_id,
                query_hash=query_hash,
                situation=analyse.situation,
                strategie=analyse.strategie_detectee,
                resultats=resultats,
            )
            session.add(cache)
            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                return

    # ------------------------------------------------------------------
    # Recherches concrètes
    # ------------------------------------------------------------------
    def _rechercher_legifrance(self, analyse: AnalyseSituation) -> Dict[str, Any]:
        if not getattr(self.config, "FF_LEGIFRANCE", True):
            return {"results": []}

        success, payload = self.clients.search_legifrance_advanced(
            self._build_query_from_keywords(analyse.mots_cles)
        )
        return payload if success else {"results": []}

    def _rechercher_judilibre(self, analyse: AnalyseSituation) -> Dict[str, Any]:
        if not getattr(self.config, "FF_JUDILIBRE", True):
            return {"results": []}

        success, payload = self.clients.search_judilibre_advanced(
            self._build_query_from_keywords(analyse.mots_cles)
        )
        return payload if success else {"results": []}

    def _rechercher_justice_back(self, analyse: AnalyseSituation) -> Dict[str, Any]:
        if not getattr(self.config, "FF_JUSTICEBACK", True):
            return {"results": []}

        # Le premier mot-clé est souvent le plus pertinent pour la localisation
        ville = next(iter(analyse.mots_cles), None)
        success, payload = self.clients.search_justice_back_lieux(ville=ville)
        return payload if success else {"results": []}

    # ------------------------------------------------------------------
    # Analyse de la situation
    # ------------------------------------------------------------------
    def _analyser_situation(
        self, situation: str, strategie: Optional[str] = None
    ) -> AnalyseSituation:
        mots_cles = self._extraire_mots_cles(situation)
        strategie_detectee = strategie or self._detecter_strategie(mots_cles)
        resume = self._generer_resume(situation, strategie_detectee)
        return AnalyseSituation(situation=situation, strategie_detectee=strategie_detectee, mots_cles=mots_cles, resume=resume)

    @staticmethod
    def _extraire_mots_cles(situation: str) -> Tuple[str, ...]:
        tokens = re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ-]{4,}", situation.lower())
        seen = []
        for token in tokens:
            if token not in seen:
                seen.append(token)
        return tuple(seen[:8])

    @staticmethod
    def _detecter_strategie(mots_cles: Iterable[str]) -> str:
        domaines = {
            "travail": "Droit du travail",
            "licenciement": "Droit du travail",
            "contrat": "Droit civil",
            "divorce": "Droit civil",
            "entreprise": "Droit commercial",
            "societe": "Droit commercial",
            "mairie": "Droit administratif",
            "prefecture": "Droit administratif",
            "plainte": "Droit pénal",
            "agression": "Droit pénal",
        }
        for mot in mots_cles:
            domaine = domaines.get(mot)
            if domaine:
                return domaine
        return "Auto-détection"

    @staticmethod
    def _generer_resume(situation: str, strategie: str) -> str:
        return f"Stratégie: {strategie}. Analyse de la situation: {situation[:120]}..." if len(situation) > 120 else f"Stratégie: {strategie}. Analyse de la situation: {situation}"

    @staticmethod
    def _build_query_from_keywords(mots_cles: Iterable[str]) -> str:
        mots = list(mots_cles)
        return " ".join(mots[:5]) if mots else "victime droits protection"


__all__ = ["MoteurRecherchePersistent"]

