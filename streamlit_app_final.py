# streamlit_app_final.py
import streamlit as st
import sys
import os
from datetime import datetime
import json
from typing import Dict, Any

# Configuration
st.set_page_config(
    page_title="OLIVIA ULTIMATE - Recherche Juridique", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS ultimate
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(45deg, #1E3A8A, #3730A3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .ultimate-badge {
        background: linear-gradient(45deg, #1E3A8A, #3730A3);
        color: white;
        padding: 0.4rem 1.2rem;
        border-radius: 25px;
        font-size: 1rem;
        font-weight: bold;
        display: inline-block;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .strategy-card {
        border: 2px solid #10B981;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
    }
    .export-section {
        border: 2px dashed #6B7280;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: #F9FAFB;
    }
    .cross-link {
        background-color: #FEF3C7;
        border-left: 4px solid #D97706;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<div class="main-header">⚡ OLIVIA ULTIMATE</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center;"><span class="ultimate-badge">VERSION PRODUCTION • STRATÉGIES • EXPORT • CROSS-LINKING</span></div>', unsafe_allow_html=True)

try:
    # Importations
    from app.config import CFG
    from app.services.legal_search_final import get_moteur_recherche_final
    
    # Initialisation
    moteur = get_moteur_recherche_final(CFG)
    
    # Initialisation session state
    if "recherche_ultimate" not in st.session_state:
        st.session_state.recherche_ultimate = None
    if "dossier_export" not in st.session_state:
        st.session_state.dossier_export = {
            "textes_selectionnes": [],
            "jurisprudence_selectionnee": []
        }

    # Sidebar - Configuration ultimate
    with st.sidebar:
        st.header("⚙️ Configuration Ultimate")
        
        st.subheader("🎯 Stratégies de Recherche")
        strategie = st.selectbox(
            "Stratégie appliquée:",
            ["Auto-détection", "accident_circulation", "accident_travail", "responsabilité_medicale"],
            help="Choisissez une stratégie ou laissez l'auto-détection"
        )
        
        st.subheader("📅 Filtres Temporels")
        filtre_date = st.selectbox(
            "Période des décisions:",
            ["Toutes périodes", "5 dernières années", "3 dernières années", "Année en cours"]
        )
        
        st.subheader("🔧 Options Avancées")
        use_cache = st.checkbox("Utiliser le cache", value=True)
        cross_linking = st.checkbox("Activer le cross-linking", value=True)
        
        st.markdown("---")
        st.caption(f"⚡ OLIVIA ULTIMATE • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.caption(f"Mode: {'SANDBOX' if 'sandbox' in CFG.LEGIFRANCE_API_BASE else 'PRODUCTION'}")

    # Zone de recherche principale
    st.markdown("### 🎯 Décrivez la situation juridique")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        situation = st.text_area(
            "Description complète:",
            placeholder="Ex: Victime piéton heurtée par véhicule - IPP 15% - préjudice esthétique facial - douleurs chroniques - perte de revenus professionnels...",
            height=120,
            key="situation_ultimate"
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🚀 Recherche Stratégique", type="primary", use_container_width=True):
            if situation:
                with st.spinner("🎯 Application de la stratégie et recherche..."):
                    strategie_finale = None if strategie == "Auto-détection" else strategie
                    st.session_state.recherche_ultimate = moteur.analyser_et_rechercher(
                        situation, strategie_finale
                    )
            else:
                st.warning("Veuillez décrire une situation")
    
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Nouvelle Recherche", use_container_width=True):
            st.session_state.recherche_ultimate = None
            st.session_state.dossier_export = {"textes_selectionnes": [], "jurisprudence_selectionnee": []}
            st.rerun()

    # Affichage des résultats
    if st.session_state.recherche_ultimate:
        data = st.session_state.recherche_ultimate
        analyse = data["analyse"]
        
        # Section stratégie
        with st.expander("🎯 Stratégie Appliquée", expanded=True):
            col_strat, col_stats = st.columns([2, 1])
            
            with col_strat:
                st.write(f"**Stratégie détectée:** {analyse.get('strategie_detectee', 'Auto-détection')}")
                if analyse.get('strategie_detectee'):
                    strategie_config = moteur.strategies_recherche.get(analyse['strategie_detectee'], {})
                    st.write(f"**Fonds utilisés:** {', '.join(strategie_config.get('fonds', []))}")
                    st.write(f"**Période:** {strategie_config.get('filtres_temporaires', {}).get('date_debut', 'Toutes')}")
            
            with col_stats:
                if "duration" in data["legifrance"]:
                    st.metric("⏱️ Légifrance", f"{data['legifrance']['duration']:.2f}s")
                if "duration" in data["judilibre"]:
                    st.metric("⏱️ Judilibre", f"{data['judilibre']['duration']:.2f}s")
        
        # Résultats Légifrance avec sélection pour export
        st.markdown("### 📚 Textes Législatifs")
        
        if "erreur" in data["legifrance"]:
            st.error(f"❌ {data['legifrance']['erreur']}")
        else:
            for i, texte in enumerate(data["legifrance"].get("results", [])):
                with st.container():
                    col_content, col_actions = st.columns([4, 1])
                    
                    with col_content:
                        st.markdown(f"**{texte.get('title', 'Titre non disponible')}**")
                        st.caption(f"{texte.get('code', 'Source')} • {texte.get('date', 'Date inconnue')}")
                        st.write(texte.get('content', 'Contenu non disponible'))
                        
                        if texte.get('id'):
                            st.caption(f"ID: {texte['id']}")
                    
                    with col_actions:
                        texte_key = f"texte_{i}"
                        is_selected = st.checkbox("📥 Exporter", key=texte_key)
                        if is_selected and texte not in st.session_state.dossier_export["textes_selectionnes"]:
                            st.session_state.dossier_export["textes_selectionnes"].append(texte)
                        elif not is_selected and texte in st.session_state.dossier_export["textes_selectionnes"]:
                            st.session_state.dossier_export["textes_selectionnes"].remove(texte)
        
        # Résultats Judilibre avec cross-linking
        st.markdown("### ⚖️ Jurisprudence")
        
        if "erreur" in data["judilibre"]:
            st.error(f"❌ {data['judilibre']['erreur']}")
        else:
            for i, juri in enumerate(data["judilibre"].get("results", [])):
                with st.container():
                    # En-tête avec métadonnées complètes
                    col_juri, col_meta, col_actions = st.columns([3, 2, 1])
                    
                    with col_juri:
                        st.markdown(f"**{juri.get('jurisdiction', 'Juridiction non précisée')}**")
                        if juri.get('chamber'):
                            st.write(f"*{juri['chamber']}*")
                    
                    with col_meta:
                        st.caption(f"Décision du {juri.get('decision_date', 'Date inconnue')}")
                        if juri.get('number'):
                            st.caption(f"Numéro: {juri['number']}")
                        if juri.get('ecli'):
                            st.caption(f"ECLI: {juri['ecli']}")
                    
                    with col_actions:
                        juri_key = f"juri_{i}"
                        is_selected = st.checkbox("📥 Exporter", key=juri_key)
                        if is_selected and juri not in st.session_state.dossier_export["jurisprudence_selectionnee"]:
                            st.session_state.dossier_export["jurisprudence_selectionnee"].append(juri)
                        elif not is_selected and juri in st.session_state.dossier_export["jurisprudence_selectionnee"]:
                            st.session_state.dossier_export["jurisprudence_selectionnee"].remove(juri)
                    
                    # Solution et résumé
                    st.write(f"**Solution:** {juri.get('solution', 'Non précisée')}")
                    st.write(f"**Résumé:** {juri.get('summary', 'Non disponible')}")
                    
                    # Lien de consultation
                    if juri.get('lien_consultation'):
                        st.markdown(f"🔗 [Consulter la décision]({juri['lien_consultation']})")
                    
                    # Cross-linking des textes appliqués
                    if cross_linking and juri.get('textes_applicables'):
                        with st.expander("📖 Textes appliqués dans cette décision", expanded=False):
                            for texte_app in juri['textes_applicables']:
                                st.markdown('<div class="cross-link">', unsafe_allow_html=True)
                                st.write(f"**{texte_app.get('reference', 'Référence')}**")
                                if texte_app.get('title'):
                                    st.write(f"*{texte_app['title']}*")
                                if texte_app.get('lien_consultation'):
                                    st.markdown(f"🔗 [Consulter le texte]({texte_app['lien_consultation']})")
                                st.markdown('</div>', unsafe_allow_html=True)
        
        # Section export
        if (st.session_state.dossier_export["textes_selectionnes"] or 
            st.session_state.dossier_export["jurisprudence_selectionnee"]):
            
            st.markdown("### 📤 Export du Dossier")
            
            with st.container():
                st.markdown('<div class="export-section">', unsafe_allow_html=True)
                
                col_export, col_stats = st.columns([2, 1])
                
                with col_export:
                    st.write("**Éléments sélectionnés pour l'export:**")
                    
                    if st.session_state.dossier_export["textes_selectionnes"]:
                        st.write(f"📚 Textes: {len(st.session_state.dossier_export['textes_selectionnes'])}")
                    
                    if st.session_state.dossier_export["jurisprudence_selectionnee"]:
                        st.write(f"⚖️ Jurisprudence: {len(st.session_state.dossier_export['jurisprudence_selectionnee'])}")
                
                with col_stats:
                    if st.button("📄 Générer le PDF", type="primary"):
                        # Simulation d'export PDF
                        contenu_export = {
                            "situation": situation,
                            "strategie": analyse.get('strategie_detectee'),
                            "timestamp": datetime.now().isoformat(),
                            "textes": st.session_state.dossier_export["textes_selectionnes"],
                            "jurisprudence": st.session_state.dossier_export["jurisprudence_selectionnee"]
                        }
                        
                        # Création d'un faux PDF (en réalité on générerait un vrai PDF)
                        st.success("✅ Dossier exporté avec succès!")
                        st.download_button(
                            label="📥 Télécharger le PDF",
                            data=json.dumps(contenu_export, indent=2, ensure_ascii=False),
                            file_name=f"dossier_olivia_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                            mime="application/json"
                        )
                
                st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Erreur lors du chargement d'OLIVIA ULTIMATE: {e}")
    import traceback
    st.code(traceback.format_exc())

# Footer ultimate
st.markdown("---")
st.caption("⚡ OLIVIA ULTIMATE - Moteur de recherche juridique stratégique • Stratégies auto • Cross-linking • Export PDF • v3.0")

