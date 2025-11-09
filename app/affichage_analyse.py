# app/affichage_analyse.py
# =========================
# SYSTÈME D'AFFICHAGE DES RÉSULTATS D'ANALYSE
# =========================

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

class AffichageAnalyse:
    """Système d'affichage des résultats d'analyse pour la défense des victimes"""
    
    def __init__(self):
        self.css_personnalise = """
        <style>
            .card-prejudice {
                background-color: #f8f9fa;
                border-left: 4px solid #007bff;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .card-defense {
                background-color: #e8f5e8;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            }
            .card-risque {
                background-color: #ffeaa7;
                border-left: 4px solid #fdcb6e;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            }
            .metric-card {
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
            .section-header {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .success-box {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
            }
        </style>
        """
    
    def appliquer_css(self):
        """Applique le CSS personnalisé"""
        st.markdown(self.css_personnalise, unsafe_allow_html=True)
    
    def afficher_analyse_complete(self, analyse: Dict[str, Any]):
        """Affiche l'analyse complète de façon structurée"""
        
        self.appliquer_css()
        
        # Header principal
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success("✅ **SYSTÈME EXPERT ACTIVÉ** - Analyse approfondie terminée")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<h1 class="section-header">⚖️ RAPPORT COMPLET D\'ANALYSE JURIDIQUE</h1>', unsafe_allow_html=True)
        
        # Métriques rapides
        self._afficher_metriques_rapides(analyse)
        
        # Onglets pour organiser l'information
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Préjudices", "🛡️ Défense", "💰 Indemnisation", 
            "📚 Références", "🚨 Actions"
        ])
        
        with tab1:
            self._afficher_analyse_prejudices(analyse["analyse_prejudices"])
        
        with tab2:
            self._afficher_elements_defense(analyse["elements_defense"])
        
        with tab3:
            self._afficher_strategie_indemnisation(analyse["strategie_indemnisation"])
        
        with tab4:
            self._afficher_references_juridiques(analyse)
        
        with tab5:
            self._afficher_plan_actions(analyse)
    
    def _afficher_metriques_rapides(self, analyse: Dict[str, Any]):
        """Affiche les métriques principales"""
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            score_gravite = analyse["analyse_prejudices"]["score_gravite_globale"]
            couleur = "🔴" if score_gravite > 70 else "🟡" if score_gravite > 40 else "🟢"
            st.metric("Score Gravité", f"{score_gravite}/100 {couleur}")
        
        with col2:
            nb_prejudices = len(analyse["analyse_prejudices"]["prejudices_patrimoniaux"]) + \
                           len(analyse["analyse_prejudices"]["prejudices_extrapatrimoniaux"])
            st.metric("Préjudices Identifiés", f"{nb_prejudices}")
        
        with col3:
            nb_elements_defense = len(analyse["elements_defense"])
            st.metric("Éléments Défense", f"{nb_elements_defense}")
        
        with col4:
            estimation = analyse["strategie_indemnisation"]["estimation_globale"]["fourchette_probable"]
            st.metric("Estimation Probable", estimation)
    
    def _afficher_analyse_prejudices(self, analyse_prejudices: Dict[str, Any]):
        """Affiche l'analyse détaillée des préjudices"""
        
        st.subheader("📈 Score de Gravité Global")
        score = analyse_prejudices["score_gravite_globale"]
        st.progress(score / 100)
        st.write(f"**{score}/100** - {self._get_niveau_gravite(score)}")
        
        # Préjudices patrimoniaux
        st.subheader("💰 Préjudices Patrimoniaux")
        prejudices_patrimoniaux = analyse_prejudices["prejudices_patrimoniaux"]
        
        if prejudices_patrimoniaux:
            for nom, details in prejudices_patrimoniaux.items():
                if details.get("present", False):
                    with st.container():
                        st.markdown(f'<div class="card-prejudice">', unsafe_allow_html=True)
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{self._formater_nom_prejudice(nom)}**")
                            st.write(f"*{details.get('description', '')}*")
                            if details.get('estimation'):
                                st.write(f"💶 {details['estimation']}")
                        with col2:
                            confiance = details.get('confiance', 0)
                            st.write(f"**Confiance :** {confiance:.0%}")
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("ℹ️ Aucun préjudice patrimonial significatif identifié")
        
        # Préjudices extrapatrimoniaux
        st.subheader("😔 Préjudices Extra-patrimoniaux")
        prejudices_extra = analyse_prejudices["prejudices_extrapatrimoniaux"]
        
        if prejudices_extra:
            for nom, details in prejudices_extra.items():
                if details.get("present", False):
                    with st.container():
                        st.markdown(f'<div class="card-prejudice">', unsafe_allow_html=True)
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{self._formater_nom_prejudice(nom)}**")
                            st.write(f"*{details.get('description', '')}*")
                            if details.get('estimation_euros'):
                                st.write(f"💶 {details['estimation_euros']}")
                        with col2:
                            confiance = details.get('confiance', 0)
                            st.write(f"**Confiance :** {confiance:.0%}")
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("ℹ️ Aucun préjudice extra-patrimonial significatif identifié")
    
    def _afficher_elements_defense(self, elements_defense: List[Dict[str, Any]]):
        """Affiche les éléments de défense identifiés"""
        
        if not elements_defense:
            st.warning("⚠️ Aucun élément de défense significatif identifié")
            return
        
        st.subheader("🛡️ Éléments de Défense Identifiés")
        
        for element in elements_defense:
            with st.container():
                st.markdown(f'<div class="card-defense">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{element['element']}**")
                    st.write(f"*{element.get('description', '')}*")
                    
                    # Textes de référence
                    if element.get('textes_reference'):
                        with st.expander("📚 Textes applicables"):
                            for texte in element['textes_reference']:
                                st.write(f"• {texte}")
                
                with col2:
                    force = element.get('force', 'Moyenne')
                    couleur = "🟢" if "élevée" in force.lower() else "🟡" if "moyenne" in force.lower() else "🔴"
                    st.write(f"**Force :** {force} {couleur}")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    def _afficher_strategie_indemnisation(self, strategie: Dict[str, Any]):
        """Affiche la stratégie d'indemnisation"""
        
        st.subheader("💰 Stratégie d'Indemnisation")
        
        # Estimations
        estimations = strategie["estimation_globale"]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fourchette Basse", estimations["fourchette_basse"])
        with col2:
            st.metric("Fourchette Probable", estimations["fourchette_probable"])
        with col3:
            st.metric("Fourchette Haute", estimations["fourchette_haute"])
        
        # Points de négociation
        st.subheader("💼 Points de Négociation")
        points = strategie.get("points_negociation", [])
        if points:
            for point in points:
                st.write(f"• {point}")
        else:
            st.info("ℹ️ Aucun point de négociation spécifique identifié")
        
        # Argumentaire clé
        st.subheader("🎯 Argumentaire Clé")
        argumentaire = strategie.get("argumentaire_cle", [])
        if argumentaire:
            for argument in argumentaire:
                st.write(f"• {argument}")
        
        # Délais et urgences
        st.subheader("⏰ Délais et Urgences")
        delais = strategie.get("delais_urgence", [])
        for delai in delais:
            st.write(f"• {delai}")
    
    def _afficher_references_juridiques(self, analyse: Dict[str, Any]):
        """Affiche les références juridiques"""
        
        st.subheader("📚 Textes Juridiques Applicables")
        
        textes = analyse.get("textes_applicables", [])
        if textes:
            for texte in textes:
                with st.expander(f"📄 {texte['texte']}"):
                    st.write(f"**Référence :** {texte['reference']}")
                    st.write(f"**Applicabilité :** {texte['applicabilite']}")
        else:
            st.info("ℹ️ Aucun texte spécifique identifié")
        
        # Risques et obstacles
        st.subheader("🚨 Risques et Obstacles")
        risques = analyse.get("risques_obstacles", [])
        if risques:
            for risque in risques:
                with st.container():
                    st.markdown(f'<div class="card-risque">', unsafe_allow_html=True)
                    st.write(f"**{risque['risque']}**")
                    st.write(f"*Impact : {risque['impact']}*")
                    st.write(f"💡 **Solution :** {risque['solution']}")
                    st.markdown('</div>', unsafe_allow_html=True)
    
    def _afficher_plan_actions(self, analyse: Dict[str, Any]):
        """Affiche le plan d'actions"""
        
        st.subheader("📋 Preuves à Rassembler")
        preuves = analyse.get("preuves_necessaires", [])
        
        if preuves:
            # Créer un DataFrame pour un affichage tabulaire
            data = []
            for preuve in preuves:
                data.append({
                    "Catégorie": preuve['categorie'],
                    "Preuve": preuve['preuve'],
                    "Urgence": preuve['urgence']
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Aucune preuve spécifique identifiée")
        
        # Recommandations d'actions
        st.subheader("🎯 Recommandations d'Actions")
        recommandations = analyse.get("recommandations_actions", [])
        
        if recommandations:
            for reco in recommandations:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{reco['action']}**")
                        st.write(f"*Objectif : {reco['objectif']}*")
                    with col2:
                        priorite = reco.get('priorite', 'Moyenne')
                        couleur = "🔴" if priorite == "Élevée" else "🟡" if priorite == "Moyenne" else "🟢"
                        st.write(f"**Priorité :** {priorite} {couleur}")
                    with col3:
                        st.write(f"**Délai :** {reco.get('delai', 'À définir')}")
        else:
            st.info("ℹ️ Aucune recommandation spécifique identifiée")
    
    def _get_niveau_gravite(self, score: int) -> str:
        """Retourne le niveau de gravité en fonction du score"""
        if score >= 80:
            return "Très Grave"
        elif score >= 60:
            return "Grave" 
        elif score >= 40:
            return "Modéré"
        elif score >= 20:
            return "Léger"
        else:
            return "Très Léger"
    
    def _formater_nom_prejudice(self, nom: str) -> str:
        """Formate le nom du préjudice pour l'affichage"""
        noms_formates = {
            "frais_medicaux": "Frais Médicaux et Paramédicaux",
            "pertes_gains": "Pertes de Gains Professionnels", 
            "incidence_professionnelle": "Incidence Professionnelle",
            "frais_divers": "Frais Divers",
            "deficit_fonctionnel_permanent": "Déficit Fonctionnel Permanent (IPP)",
            "souffrances_endurees": "Souffrances Endurées",
            "prejudice_esthetique": "Préjudice Esthétique",
            "prejudice_agrement": "Préjudice d'Agrément",
            "prejudice_affection": "Préjudice d'Affection"
        }
        return noms_formates.get(nom, nom.replace('_', ' ').title())

# Instance globale
affichage = AffichageAnalyse()
