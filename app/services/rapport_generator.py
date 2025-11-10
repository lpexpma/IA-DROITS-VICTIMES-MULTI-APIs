from datetime import datetime
from typing import List, Dict, Any
from ..models.schemas import Dossier, TypeSource

class RapportGenerator:
    def __init__(self):
        pass
    
    def generer_rapport_markdown(self, dossier: Dossier) -> str:
        """Génère un rapport markdown complet pour un dossier"""
        
        rapport = f"""# 📊 RAPPORT DU DOSSIER : {dossier.titre}

**Identifiant**: {dossier.id}  
**Statut**: {dossier.statut.value.upper()}  
**Lieu**: {dossier.lieu}  
**Date de création**: {dossier.created_at.strftime('%d/%m/%Y')}  
**Dernière mise à jour**: {dossier.updated_at.strftime('%d/%m/%Y')}  

---

## 📋 DESCRIPTION DES FAITS

{dossier.faits}

---

## 👥 PARTIES IMPLIQUÉES

{self._formater_parties(dossier.parties)}

---

## 📅 DATES CLÉS

{self._formater_dates_cles(dossier.dates_cles)}

---

## ⚖️ ANALYSE JURIDIQUE

{self._generer_analyse_juridique(dossier)}

---

## 📚 SOURCES JURIDIQUES IDENTIFIÉES

{self._formater_sources(dossier.sources)}

---

## 💡 RECOMMANDATIONS

{self._generer_recommandations(dossier)}

---

*Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*
"""
        return rapport
    
    def _formater_parties(self, parties: List[str]) -> str:
        if not parties:
            return "*Aucune partie spécifiée*"
        return "\n".join([f"- {partie}" for partie in parties])
    
    def _formater_dates_cles(self, dates_cles: Dict[str, str]) -> str:
        if not dates_cles:
            return "*Aucune date clé spécifiée*"
        
        formatted = []
        for nom, date_str in dates_cles.items():
            formatted.append(f"- **{nom.replace('_', ' ').title()}** : {date_str}")
        return "\n".join(formatted)
    
    def _generer_analyse_juridique(self, dossier: Dossier) -> str:
        textes = [s for s in dossier.sources if s.type_source == TypeSource.LEGIFRANCE]
        jurisprudence = [s for s in dossier.sources if s.type_source == TypeSource.JUDILIBRE]
        lieux = [s for s in dossier.sources if s.type_source == TypeSource.JUSTICE_BACK]
        
        analyse = "### 📜 Textes Applicables\n\n"
        if textes:
            for texte in textes[:3]:
                titre = texte.payload.get('title', 'Sans titre')
                contenu = texte.payload.get('content', '')[:200] + "..."
                analyse += f"**{titre}**\n\n{contenu}\n\n---\n\n"
        else:
            analyse += "*Aucun texte identifié*\n\n"
        
        analyse += "### ⚖️ Jurisprudence Pertinente\n\n"
        if jurisprudence:
            for decision in jurisprudence[:3]:
                jurisdiction = decision.payload.get('jurisdiction', 'Juridiction inconnue')
                solution = decision.payload.get('solution', 'Solution non spécifiée')
                resume = decision.payload.get('summary', 'Aucun résumé disponible')
                analyse += f"**{jurisdiction}** - *{solution}*\n\n{resume}\n\n---\n\n"
        else:
            analyse += "*Aucune décision identifiée*\n\n"
        
        analyse += "### 🏛️ Ressources Locales\n\n"
        if lieux:
            for lieu in lieux[:2]:
                nom = lieu.payload.get('name', 'Lieu sans nom')
                adresse = lieu.payload.get('address', 'Adresse non précisée')
                contact = lieu.payload.get('contact', 'Contact non disponible')
                analyse += f"**{nom}**\n\n- 📍 {adresse}\n- 📞 {contact}\n\n"
        else:
            analyse += "*Aucune ressource locale identifiée*"
        
        return analyse
    
    def _formater_sources(self, sources: List) -> str:
        if not sources:
            return "*Aucune source collectée*"
        
        formatted = f"**Total des sources : {len(sources)}**\n\n"
        
        par_type = {}
        for source in sources:
            if source.type_source not in par_type:
                par_type[source.type_source] = []
            par_type[source.type_source].append(source)
        
        for type_source, sources_list in par_type.items():
            formatted += f"### {type_source.value.upper()} ({len(sources_list)})\n\n"
            for source in sources_list[:5]:  # Limiter à 5 par type
                if type_source == TypeSource.LEGIFRANCE:
                    formatted += f"- {source.payload.get('title', 'Sans titre')}\n"
                elif type_source == TypeSource.JUDILIBRE:
                    formatted += f"- {source.payload.get('jurisdiction', 'Juridiction')} - {source.payload.get('decision_date', 'Date inconnue')}\n"
                elif type_source == TypeSource.JUSTICE_BACK:
                    formatted += f"- {source.payload.get('name', 'Lieu sans nom')}\n"
            if len(sources_list) > 5:
                formatted += f"- ... et {len(sources_list) - 5} autres\n"
            formatted += "\n"
        
        return formatted
    
    def _generer_recommandations(self, dossier: Dossier) -> str:
        recommandations = []
        
        # Recommandations basées sur le statut
        if dossier.statut.value == "nouveau":
            recommandations.append("✅ **Actions immédiates :** Compléter les informations manquantes et lancer la surveillance automatique")
        
        # Recommandations basées sur les sources
        textes = [s for s in dossier.sources if s.type_source == TypeSource.LEGIFRANCE]
        jurisprudence = [s for s in dossier.sources if s.type_source == TypeSource.JUDILIBRE]
        
        if not textes:
            recommandations.append("🔍 **Recherche nécessaire :** Aucun texte législatif identifié. Élargir les critères de recherche.")
        
        if not jurisprudence:
            recommandations.append("⚖️ **Analyse jurisprudentielle :** Aucune décision judiciaire trouvée. Vérifier la pertinence des mots-clés.")
        
        if len(jurisprudence) >= 3:
            recommandations.append("📈 **Opportunité :** Jurisprudence abondante disponible. Analyser les tendances récentes.")
        
        # Recommandation générique
        if not recommandations:
            recommandations.append("📋 **Suivi :** Le dossier semble bien documenté. Maintenir la surveillance régulière.")
        
        return "\n".join([f"- {rec}" for rec in recommandations])
    