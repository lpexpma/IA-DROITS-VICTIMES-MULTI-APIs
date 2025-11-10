# app/services/api_clients.py - Version corrigée
import hashlib
import json
from datetime import date
from typing import Dict, Any, List, Optional, Tuple

print("🔧 Chargement de api_clients.py corrigé...")

# Import absolu
try:
    from app.config import CFG
    print("✅ CFG importé")
except ImportError as e:
    print(f"❌ Erreur import CFG: {e}")
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import CFG

# SUPPRIMER l'importation problématique et utiliser directement les strings
# On utilise des strings littéraux au lieu de l'enum pour éviter les conflits
LEGIFRANCE = "legifrance"
JUDILIBRE = "judilibre"
JUSTICE_BACK = "justice_back"

print("✅ Types sources définis directement")

class APIClients:
    """Client pour les APIs juridiques PISTE"""
    
    def __init__(self, config=None):
        self.config = config or CFG
        self._tokens = {}
        self._demo_data = self._charger_demo_data()
        print(f"🎯 APIClients initialisé - Mode: {'DÉMO' if self.config.MODE_DEMO else 'PRODUCTION'}")
    
    def _charger_demo_data(self) -> Dict[str, Any]:
        """Charge les données de démonstration"""
        return {
            "legifrance": [
                {
                    "id": "LEGI-ART-0000321952",
                    "title": "Article R412-37 du code de la route",
                    "content": "Tout conducteur est tenu de céder le passage au piéton...",
                    "date": "2023-12-12"
                },
                {
                    "id": "LEGI-TEXT-0000456712", 
                    "title": "Loi protection des piétons",
                    "content": "Renforcement des sanctions...",
                    "date": "2024-01-01"
                }
            ],
            "judilibre": [
                {
                    "id": "JURI-PARIS-2023-0456",
                    "jurisdiction": "Cour d'appel de Paris",
                    "decision_date": "2023-11-15",
                    "solution": "Indemnisation majorée",
                    "summary": "Reconnaissance du préjudice d'anxiété...",
                }
            ],
            "justice_back": [
                {
                    "id": "TJ-PARIS-001",
                    "name": "Tribunal Judiciaire de Paris",
                    "type": "tribunal",
                    "address": "4 Boulevard du Palais, 75001 Paris",
                    "contact": "01 44 32 52 52",
                    "ville": "Paris"
                }
            ]
        }
    
    def search_legifrance_advanced(self, query: str, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Tuple[bool, Any]:
        """Recherche Légifrance - mode démo"""
        print(f"🔍 Légifrance: '{query}'")
        results = [item for item in self._demo_data["legifrance"] 
                  if any(mot in query.lower() for mot in ["piéton", "accident", "responsabilité"])]
        return True, {"results": results[:3]}
    
    def search_judilibre_advanced(self, query: str, date_from: Optional[date] = None, jurisdiction: Optional[str] = None) -> Tuple[bool, Any]:
        """Recherche Judilibre - mode démo"""
        print(f"⚖️ Judilibre: '{query}'")
        results = [item for item in self._demo_data["judilibre"] 
                  if any(mot in query.lower() for mot in ["piéton", "indemnisation", "responsabilité"])]
        return True, {"results": results[:2]}
    
    def search_justice_back_lieux(self, ville: Optional[str] = None, type_lieu: Optional[str] = None) -> Tuple[bool, Any]:
        """Recherche Justice Back - mode démo"""
        print(f"🏛️ Justice Back: '{ville}'")
        results = self._demo_data["justice_back"]
        if ville:
            results = [item for item in results if ville.lower() in item.get("ville", "").lower()]
        return True, {"results": results}
    
    def compute_hash(self, data: Any) -> str:
        """Calcule un hash pour détecter les changements"""
        normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


# Test direct
if __name__ == "__main__":
    print("🧪 TEST DIRECT APIClients corrigé")
    clients = APIClients()
    print(f"✅ Instance créée - Mode: {clients.config.MODE_DEMO}")
    
    success, result = clients.search_legifrance_advanced("accident piéton")
    print(f"✅ Recherche - Succès: {success}, Résultats: {len(result.get('results', []))}")
    