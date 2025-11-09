# app/models/schemas.py
from typing import Annotated, Optional, List, Dict, Any
from pydantic import BaseModel, Field, StringConstraints, field_validator
import re

# Types validés avec contraintes
CodePostal = Annotated[str, StringConstraints(pattern=r"^\d{5}$")]
DescriptionSituation = Annotated[str, StringConstraints(min_length=10, max_length=2000)]
TypeAccident = Annotated[str, StringConstraints(pattern=r"^(accident_route|accident_travail|agression|erreur_medicale)$")]

class SearchRequest(BaseModel):
    """Schéma validé pour la recherche - VALIDATION RÉELLE Pydantic v2"""
    description_situation: DescriptionSituation
    type_accident: TypeAccident = "accident_route"
    code_postal: Optional[CodePostal] = None
    include_apis: List[str] = Field(
        default=["legifrance", "judilibre", "justice_back"],
        description="APIs à inclure dans la recherche"
    )

    # CORRECTION CRITIQUE - VALIDATEUR ACTIF PYDANTIC V2
    @field_validator("code_postal")
    @classmethod
    def validate_code_postal(cls, v):
        """Validation manuelle renforcée du code postal"""
        if v is None:
            return v
        if not re.match(r"^\d{5}$", v):
            raise ValueError("Le code postal doit contenir exactement 5 chiffres")
        return v

class AnalyseRequest(BaseModel):
    """Schéma validé pour l'analyse approfondie - VALIDATION RÉELLE"""
    description_situation: DescriptionSituation
    details_prejudices: Optional[Dict[str, Any]] = None
    code_postal: Optional[CodePostal] = None

class APIHealthStatus(BaseModel):
    """Statut de santé des APIs"""
    legifrance: bool
    judilibre: bool  
    justice_back: bool
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class PrejudiceDetecte(BaseModel):
    """Préjudice détecté dans l'analyse"""
    categorie: str
    description: str
    confiance: float

class AnalyseDescription(BaseModel):
    """Description de l'analyse effectuée"""
    prejudices_detectes: List[PrejudiceDetecte]
    interactions: List[str]
    complexite: str

class JurisprudenceItem(BaseModel):
    """Élément de jurisprudence"""
    titre: str
    juridiction: str
    date: str
    chambre: str
    formation: str
    theme: str
    resume: str
    fiabilite: str
    source: str

class EstimationPrejudice(BaseModel):
    """Estimation pour un préjudice spécifique"""
    min: int
    max: int
    unite: str
    source: str

class EstimationIndemnisation(BaseModel):
    """Estimation globale d'indemnisation"""
    estimations_par_prejudice: Dict[str, EstimationPrejudice]
    total_estime: EstimationPrejudice
    recommendations_calcul: List[str]

class LieuJustice(BaseModel):
    """Lieu de justice"""
    id: str
    titre: str
    type: str
    adresse: str
    telephone: str
    courriel: str
    horaire: str
    gps: Dict[str, Optional[str]]
    source: str

class AnalyseSituationResponse(BaseModel):
    """Réponse complète de l'analyse de situation"""
    analyse_description: AnalyseDescription
    jurisprudence_par_prejudice: Dict[str, Any]
    estimation_indemnisation: EstimationIndemnisation
    ressources_locales: Dict[str, Any]
    recommendations_generales: List[str]

class SearchResponse(BaseModel):
    """Réponse de recherche multi-APIs"""
    legifrance: List[Dict[str, Any]]
    judilibre: List[Dict[str, Any]]
    justice_back: List[Dict[str, Any]]
    analyse: Dict[str, Any]

class HealthResponse(BaseModel):
    """Réponse de santé"""
    status: str
    service: str
    version: str
    timestamp: str

class ReadyResponse(BaseModel):
    """Réponse de readiness"""
    status: str
    checks: Dict[str, bool]
    timestamp: str
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    error: str
    status_code: int
    request_id: str
     