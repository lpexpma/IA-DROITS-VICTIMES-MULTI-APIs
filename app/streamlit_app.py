import os
import sys
import json
import asyncio
from datetime import datetime, date
from typing import Dict, Any, List, Optional

# Correction du chemin Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Chargement variables d'environnement
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import streamlit as st

# Import des modules
from app.config import CFG
from app.models.schemas import Dossier, StatutDossier, TacheSurveillance, TypeSource
from app.services.api_clients import APIClients
from app.services.watcher import DossierWatcher
from app.services.rapport_generator import RapportGenerator

# =========================
# GESTION DES DOSSIERS (simplifiée)
# =========================

class GestionnaireDossiers:
    def __init__(self, data_dir: str = "data/dossiers"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def sauvegarder_dossier(self, dossier: Dossier):
        filepath = os.path.join(self.data_dir, f"{dossier.id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dossier.to_dict(), f, ensure_ascii=False, indent=2)
    
    def charger_dossier(self, dossier_id: str) -> Optional[Dossier]:
        filepath = os.path.join(self.data_dir, f"{dossier_id}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Dossier.from_dict(data)
        except FileNotFoundError:
            return None
    
    def lister_dossiers(self) -> List[Dict[str, Any]]:
        dossiers = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                dossier_id = filename[:-5]
                dossier = self.charger_dossier(dossier_id)
                if dossier:
                    dossiers.append({
                        'id': dossier.id,
                        'titre': dossier.titre,
                        'statut': dossier.statut.value,
                        'created_at': dossier.created_at,
                        'updated_at': dossier.updated_at
                    })
        return sorted(dossiers, key=lambda x: x['updated_at'], reverse=True)

# =========================
# INTERFACE STREAMLIT MVP
# =========================

def main():
    st.set_page_config(page_title="OLIVIA - Système Expert Défense Victimes", layout="wide")
    st.title("⚖️ OLIVIA - Système Expert Défense Victimes")
    
    # Mode démo warning
    if CFG.MODE_DEMO:
        st.warning("🔶 **MODE DÉMO ACTIVÉ** - Données de démonstration")
    else:
        st.success("🔷 **MODE PISTE ACTIVÉ** - Connexion aux APIs gouvernementales")
    
    # Initialisation session
    if 'gestionnaire' not in st.session_state:
        st.session_state.gestionnaire = GestionnaireDossiers()
    if 'api_clients' not in st.session_state:
        st.session_state.api_clients = APIClients(CFG)
    if 'watcher' not in st.session_state:
        st.session_state.watcher = DossierWatcher(st.session_state.api_clients)
    if 'selected_dossier' not in st.session_state:
        st.session_state.selected_dossier = None
    
    # Navigation simplifiée
    onglet = st.sidebar.selectbox(
        "Navigation",
        ["📋 Nouveau Dossier", "📂 Mes Dossiers", "📊 Tableau de Bord"]
    )
    
    if onglet == "📋 Nouveau Dossier":
        afficher_nouveau_dossier()
    elif onglet == "📂 Mes Dossiers":
        afficher_dossiers_existants()
    elif onglet == "📊 Tableau de Bord":
        afficher_tableau_de_bord()

def afficher_nouveau_dossier():
    st.header("📋 Créer un Nouveau Dossier")
    
    with st.form("nouveau_dossier_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            dossier_id = st.text_input("ID du dossier*", placeholder="VICT-2024-001")
            titre = st.text_input("Titre du dossier*", placeholder="Accident piéton - M. Martin")
            lieu = st.text_input("Lieu*", placeholder="Paris")
        
        with col2:
            statut = st.selectbox("Statut", [s.value for s in StatutDossier])
            parties = st.text_area("Parties impliquées*", placeholder="Victime: M. Martin\nResponsable: Conducteur\nTémoins: 2 témoins")
            mots_cles = st.text_input("Mots-clés*", placeholder="accident, piéton, fracture, indemnisation")
        
        faits = st.text_area(
            "Description des faits*",
            height=120,
            placeholder="Décrivez les circonstances de l'accident, les blessures, les soins..."
        )
        
        st.subheader("📅 Dates importantes")
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            date_accident_input = st.date_input("Date de l'accident")
        with col_date2:
            date_consolidation_input = st.date_input("Date consolidation")
        
        submitted = st.form_submit_button("💾 Créer le Dossier", use_container_width=True)
        
        if submitted:
            if not all([dossier_id, titre, faits, lieu, parties, mots_cles]):
                st.error("❌ Veuillez remplir tous les champs obligatoires (*)")
            else:
                # CORRECTION : Gestion correcte des dates (tuple ou date simple)
                dates_cles = {}
                
                # Gestion date_accident
                if date_accident_input:
                    if isinstance(date_accident_input, tuple):
                        # Si c'est un tuple, prendre le premier élément
                        date_accident = date_accident_input[0]
                    else:
                        # Si c'est une date simple
                        date_accident = date_accident_input
                    dates_cles["accident"] = date_accident.isoformat()
                
                # Gestion date_consolidation
                if date_consolidation_input:
                    if isinstance(date_consolidation_input, tuple):
                        date_consolidation = date_consolidation_input[0]
                    else:
                        date_consolidation = date_consolidation_input
                    dates_cles["consolidation"] = date_consolidation.isoformat()
                
                # Créer le dossier
                dossier = Dossier(
                    id=dossier_id,
                    titre=titre,
                    faits=faits,
                    dates_cles=dates_cles,
                    lieu=lieu,
                    parties=[p.strip() for p in parties.split('\n') if p.strip()],
                    mots_cles=[m.strip() for m in mots_cles.split(',') if m.strip()],
                    statut=StatutDossier(statut)
                )
                
                # CORRECTION : Création des tâches de surveillance avec arguments nommés
                dossier.taches_surveillance = [
                    TacheSurveillance(
                        type_source=TypeSource.LEGIFRANCE, 
                        parametres={"mots_cles": dossier.mots_cles}
                    ),
                    TacheSurveillance(
                        type_source=TypeSource.JUDILIBRE, 
                        parametres={"mots_cles": dossier.mots_cles}
                    ),
                    TacheSurveillance(
                        type_source=TypeSource.JUSTICE_BACK, 
                        parametres={"ville": lieu}
                    )
                ]
                
                # Sauvegarder
                st.session_state.gestionnaire.sauvegarder_dossier(dossier)
                st.session_state.selected_dossier = dossier
                
                st.success(f"✅ Dossier '{titre}' créé avec succès!")
                st.balloons()

def afficher_dossiers_existants():
    st.header("📂 Mes Dossiers")
    
    dossiers = st.session_state.gestionnaire.lister_dossiers()
    
    if not dossiers:
        st.info("ℹ️ Aucun dossier existant. Créez votre premier dossier !")
        return
    
    # Liste simplifiée des dossiers
    for dossier_info in dossiers:
        with st.expander(f"📁 {dossier_info['titre']} - {dossier_info['statut'].upper()}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**ID**: {dossier_info['id']}")
                st.write(f"**Mis à jour**: {dossier_info['updated_at'].strftime('%d/%m/%Y')}")
                
                if st.button("📊 Ouvrir", key=f"open_{dossier_info['id']}"):
                    dossier = st.session_state.gestionnaire.charger_dossier(dossier_info['id'])
                    st.session_state.selected_dossier = dossier
                    st.rerun()
            
            with col2:
                if st.button("🔍 Surveiller", key=f"watch_{dossier_info['id']}"):
                    asyncio.run(surveiller_dossier_immediat(dossier_info['id']))
    
    # Affichage du dossier sélectionné
    if st.session_state.selected_dossier:
        afficher_details_dossier(st.session_state.selected_dossier)

def afficher_details_dossier(dossier: Dossier):
    st.header(f"📋 Dossier: {dossier.titre}")
    
    # Onglets simplifiés
    onglets = st.tabs(["📋 Résumé", "⚖️ Textes & Jurisprudence", "📊 Rapport"])
    
    with onglets[0]:
        afficher_resume_dossier(dossier)
    
    with onglets[1]:
        afficher_contenu_juridique(dossier)
    
    with onglets[2]:
        afficher_rapport_dossier(dossier)

def afficher_resume_dossier(dossier: Dossier):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Informations")
        st.write(f"**ID**: {dossier.id}")
        st.write(f"**Statut**: {dossier.statut.value}")
        st.write(f"**Lieu**: {dossier.lieu}")
        st.write(f"**Créé le**: {dossier.created_at.strftime('%d/%m/%Y')}")
        
        st.subheader("Parties")
        for partie in dossier.parties:
            st.write(f"- {partie}")
    
    with col2:
        st.subheader("Dates clés")
        if dossier.dates_cles:
            for nom_date, valeur_date in dossier.dates_cles.items():
                st.write(f"**{nom_date.replace('_', ' ').title()}**: {valeur_date}")
        else:
            st.write("*Aucune date clé définie*")
        
        st.subheader("Mots-clés")
        st.write(", ".join(dossier.mots_cles) if dossier.mots_cles else "*Aucun mot-clé*")
        
        # Bouton surveillance
        if st.button("🔄 Vérifier les mises à jour", type="primary", key="update_main"):
            asyncio.run(surveiller_dossier_immediat(dossier.id))
    
    st.subheader("Description des faits")
    st.write(dossier.faits)

def afficher_contenu_juridique(dossier: Dossier):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📜 Textes applicables")
        textes = [s for s in dossier.sources if s.type_source == TypeSource.LEGIFRANCE]
        
        if not textes:
            st.info("Aucun texte identifié. Lancez la surveillance.")
        else:
            for texte in textes[:3]:
                with st.expander(texte.payload.get('title', 'Sans titre')):
                    st.write(texte.payload.get('content', 'Aucun contenu')[:200] + "...")
    
    with col2:
        st.subheader("⚖️ Jurisprudence")
        decisions = [s for s in dossier.sources if s.type_source == TypeSource.JUDILIBRE]
        
        if not decisions:
            st.info("Aucune décision identifiée. Lancez la surveillance.")
        else:
            for decision in decisions[:3]:
                with st.expander(f"{decision.payload.get('jurisdiction', 'Juridiction')}"):
                    st.write(f"**Date**: {decision.payload.get('decision_date', 'N/A')}")
                    st.write(f"**Solution**: {decision.payload.get('solution', 'N/A')}")
                    st.write(decision.payload.get('summary', 'Aucun résumé')[:150] + "...")

def afficher_rapport_dossier(dossier: Dossier):
    generator = RapportGenerator()
    
    st.subheader("📊 Rapport du dossier")
    
    if st.button("📄 Générer le rapport complet", type="primary", key="generate_report"):
        with st.spinner("Génération du rapport..."):
            markdown = generator.generer_rapport_markdown(dossier)
            
            # Aperçu
            st.subheader("Aperçu du rapport")
            st.markdown(markdown[:1000] + "..." if len(markdown) > 1000 else markdown)
            
            # Téléchargement
            st.download_button(
                "💾 Télécharger le rapport",
                data=markdown.encode('utf-8'),
                file_name=f"rapport_{dossier.id}.md",
                mime="text/markdown",
                key="download_report"
            )

def afficher_tableau_de_bord():
    st.header("📊 Tableau de Bord")
    
    dossiers = st.session_state.gestionnaire.lister_dossiers()
    
    if not dossiers:
        st.info("ℹ️ Aucun dossier à afficher.")
        return
    
    # Statistiques simples
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Dossiers", len(dossiers))
    
    with col2:
        dossiers_actifs = len([d for d in dossiers if d['statut'] != StatutDossier.CLOS.value])
        st.metric("Dossiers Actifs", dossiers_actifs)
    
    with col3:
        total_sources = 0
        for dossier_info in dossiers:
            dossier = st.session_state.gestionnaire.charger_dossier(dossier_info['id'])
            if dossier:
                total_sources += len(dossier.sources)
        st.metric("Sources Collectées", total_sources)
    
    with col4:
        st.metric("Mode", "PISTE" if not CFG.MODE_DEMO else "DÉMO")
    
    # Dossiers récents
    st.subheader("📅 Dossiers récents")
    for dossier in dossiers[:5]:
        st.write(f"**{dossier['titre']}** - {dossier['statut']} (MAJ: {dossier['updated_at'].strftime('%d/%m/%Y')})")

async def surveiller_dossier_immediat(dossier_id: str):
    """Lance une surveillance immédiate"""
    dossier = st.session_state.gestionnaire.charger_dossier(dossier_id)
    if dossier:
        with st.spinner("🔍 Surveillance en cours..."):
            updates = await st.session_state.watcher.surveiller_dossier(dossier)
            st.session_state.gestionnaire.sauvegarder_dossier(dossier)
        
        # CORRECTION : st.rerun() sans arguments
        if updates:
            st.success(f"✅ {len(updates)} mise(s) à jour détectée(s)")
            st.rerun()  # ✅ Appel sans arguments
        else:
            st.info("ℹ️ Aucune nouvelle mise à jour")

if __name__ == "__main__":
    main()