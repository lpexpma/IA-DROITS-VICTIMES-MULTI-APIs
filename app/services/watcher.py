# app/services/watcher.py - Version simplifiée
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# Import absolu
try:
    from app.services.api_clients import APIClients
    from app.models.schemas import Dossier, SourceJuridique, TacheSurveillance, TypeSource
except ImportError:
    # Fallback pour développement
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.services.api_clients import APIClients
    from app.models.schemas import Dossier, SourceJuridique, TacheSurveillance, TypeSource


class DossierWatcher:
    def __init__(self, api_clients: APIClients):
        self.api_clients = api_clients
        print("✅ DossierWatcher initialisé")
    
    async def surveiller_dossier(self, dossier: Dossier) -> List[Dict[str, Any]]:
        """Surveille un dossier et retourne les nouvelles sources"""
        print(f"🔍 Surveillance du dossier: {dossier.titre}")
        nouvelles_sources = []
        
        for tache in dossier.taches_surveillance:
            if not tache.active:
                continue
                
            nouvelles = await self._executer_tache_surveillance(dossier, tache)
            nouvelles_sources.extend(nouvelles)
            tache.derniere_verification = datetime.now()
        
        dossier.updated_at = datetime.now()
        print(f"✅ Surveillance terminée: {len(nouvelles_sources)} nouvelles sources")
        return nouvelles_sources
    
    async def _executer_tache_surveillance(self, dossier: Dossier, tache: TacheSurveillance) -> List[Dict[str, Any]]:
        """Exécute une tâche de surveillance spécifique"""
        if tache.type_source == TypeSource.LEGIFRANCE:
            return await self._surveiller_legifrance(dossier, tache)
        elif tache.type_source == TypeSource.JUDILIBRE:
            return await self._surveiller_judilibre(dossier, tache)
        elif tache.type_source == TypeSource.JUSTICE_BACK:
            return await self._surveiller_justice_back(dossier, tache)
        return []
    
    async def _surveiller_legifrance(self, dossier: Dossier, tache: TacheSurveillance) -> List[Dict[str, Any]]:
        """Surveillance Légifrance"""
        query = " OR ".join(dossier.mots_cles)
        success, result = self.api_clients.search_legifrance_advanced(query)
        
        nouvelles_sources = []
        if success and "results" in result:
            for item in result["results"]:
                source_id = item.get("id", f"legifrance_{len(nouvelles_sources)}")
                if not any(s.id == source_id for s in dossier.sources):
                    nouvelle_source = SourceJuridique(
                        id=source_id,
                        type_source=TypeSource.LEGIFRANCE,
                        payload=item,
                        hash_content=self.api_clients.compute_hash(item)
                    )
                    dossier.sources.append(nouvelle_source)
                    nouvelles_sources.append({
                        "type": "legifrance",
                        "id": source_id,
                        "titre": item.get("title", "Sans titre")
                    })
        return nouvelles_sources
    
    async def _surveiller_judilibre(self, dossier: Dossier, tache: TacheSurveillance) -> List[Dict[str, Any]]:
        """Surveillance Judilibre"""
        query = " OR ".join(dossier.mots_cles)
        success, result = self.api_clients.search_judilibre_advanced(query)
        
        nouvelles_sources = []
        if success and "results" in result:
            for item in result["results"]:
                source_id = item.get("id", f"judilibre_{len(nouvelles_sources)}")
                if not any(s.id == source_id for s in dossier.sources):
                    nouvelle_source = SourceJuridique(
                        id=source_id,
                        type_source=TypeSource.JUDILIBRE,
                        payload=item,
                        hash_content=self.api_clients.compute_hash(item)
                    )
                    dossier.sources.append(nouvelle_source)
                    nouvelles_sources.append({
                        "type": "judilibre", 
                        "id": source_id,
                        "jurisdiction": item.get("jurisdiction", "Inconnue")
                    })
        return nouvelles_sources
    
    async def _surveiller_justice_back(self, dossier: Dossier, tache: TacheSurveillance) -> List[Dict[str, Any]]:
        """Surveillance Justice Back"""
        success, result = self.api_clients.search_justice_back_lieux(ville=dossier.lieu)
        
        nouvelles_sources = []
        if success and "results" in result:
            for item in result["results"]:
                source_id = item.get("id", f"justice_back_{len(nouvelles_sources)}")
                if not any(s.id == source_id for s in dossier.sources):
                    nouvelle_source = SourceJuridique(
                        id=source_id,
                        type_source=TypeSource.JUSTICE_BACK,
                        payload=item,
                        hash_content=self.api_clients.compute_hash(item)
                    )
                    dossier.sources.append(nouvelle_source)
                    nouvelles_sources.append({
                        "type": "justice_back",
                        "id": source_id, 
                        "nom": item.get("name", "Lieu sans nom")
                    })
        return nouvelles_sources
    