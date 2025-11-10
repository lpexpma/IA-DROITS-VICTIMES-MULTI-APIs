from enum import Enum
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class TypeSource(str, Enum):
    LEGIFRANCE = "legifrance"
    JUDILIBRE = "judilibre" 
    JUSTICE_BACK = "justice_back"

class StatutDossier(str, Enum):
    NOUVEAU = "nouveau"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    CLOS = "clos"

class SourceJuridique(BaseModel):
    id: str
    type_source: TypeSource
    payload: Dict[str, Any]
    date_extraction: datetime = Field(default_factory=datetime.now)
    hash_content: Optional[str] = None

class TacheSurveillance(BaseModel):
    type_source: TypeSource
    parametres: Dict[str, Any]
    active: bool = True
    derniere_verification: Optional[datetime] = None

class Dossier(BaseModel):
    id: str
    titre: str
    faits: str
    dates_cles: Dict[str, str] = Field(default_factory=dict)
    lieu: str
    parties: List[str] = Field(default_factory=list)
    mots_cles: List[str] = Field(default_factory=list)
    statut: StatutDossier = StatutDossier.NOUVEAU
    sources: List[SourceJuridique] = Field(default_factory=list)
    taches_surveillance: List[TacheSurveillance] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "titre": self.titre,
            "faits": self.faits,
            "dates_cles": self.dates_cles,
            "lieu": self.lieu,
            "parties": self.parties,
            "mots_cles": self.mots_cles,
            "statut": self.statut.value,
            "sources": [
                {
                    "id": s.id,
                    "type_source": s.type_source.value,
                    "payload": s.payload,
                    "date_extraction": s.date_extraction.isoformat(),
                    "hash_content": s.hash_content
                }
                for s in self.sources
            ],
            "taches_surveillance": [
                {
                    "type_source": t.type_source.value,
                    "parametres": t.parametres,
                    "active": t.active,
                    "derniere_verification": t.derniere_verification.isoformat() if t.derniere_verification else None
                }
                for t in self.taches_surveillance
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dossier':
        # Conversion des dates
        sources = []
        for s in data.get("sources", []):
            sources.append(SourceJuridique(
                id=s["id"],
                type_source=TypeSource(s["type_source"]),
                payload=s["payload"],
                date_extraction=datetime.fromisoformat(s["date_extraction"]),
                hash_content=s.get("hash_content")
            ))
        
        taches = []
        for t in data.get("taches_surveillance", []):
            taches.append(TacheSurveillance(
                type_source=TypeSource(t["type_source"]),
                parametres=t["parametres"],
                active=t["active"],
                derniere_verification=datetime.fromisoformat(t["derniere_verification"]) if t.get("derniere_verification") else None
            ))
        
        return cls(
            id=data["id"],
            titre=data["titre"],
            faits=data["faits"],
            dates_cles=data.get("dates_cles", {}),
            lieu=data["lieu"],
            parties=data.get("parties", []),
            mots_cles=data.get("mots_cles", []),
            statut=StatutDossier(data["statut"]),
            sources=sources,
            taches_surveillance=taches,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )