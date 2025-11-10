# streamlit_app.py
import streamlit as st
import sys
import os
from datetime import datetime

# Configuration de base
st.set_page_config(
    page_title="OLIVIA ULTIMATE", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Détection environnement cloud
IS_CLOUD = "streamlit" in os.getenv("HOME", "")

try:
    # Importations selon l'environnement
    if IS_CLOUD or os.getenv("MODE_DEMO") == "false":
        from app.config_prod import CFG_PROD as CFG
        st.success("🔒 Mode PRODUCTION PISTE")
    else:
        from app.config import CFG
        st.info("🧪 Mode SANDBOX PISTE")
    
    from app.services.legal_search_persistent import MoteurRecherchePersistent
    from app.export_manager import export_manager
    from app.database import init_database, db
    
    # Initialisation
    moteur = MoteurRecherchePersistent(CFG)
    
    # Initialisation BD au premier lancement
    if "db_initialized" not in st.session_state:
        try:
            init_database()
            st.session_state.db_initialized = True
        except Exception as e:
            st.warning(f"Base de données en mode dégradé: {e}")

except ImportError as e:
    st.error(f"❌ Erreur importation: {e}")
    st.stop()
except Exception as e:
    st.error(f"❌ Erreur initialisation: {e}")
    st.stop()

# INTERFACE UTILISATEUR (identique à la version précédente)
st.title("⚡ OLIVIA ULTIMATE v3.0")
st.markdown("Moteur de Recherche Juridique Intelligent - APIs PISTE")

# Sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    mode_demo = st.toggle("Mode Démo", value=os.getenv("MODE_DEMO", "true") == "true")
    
    if mode_demo:
        st.info("Mode démo activé - Données simulées")
    else:
        st.success("Mode production - APIs PISTE réelles")

# Section recherche principale
st.header("🎯 Recherche Stratégique")
situation = st.text_area(
    "Décrivez votre situation juridique:",
    placeholder="Ex: rupture de contrat de travail pour faute grave...",
    height=100
)

# Stratégies prédéfinies
strategies = [
    "Auto-détection",
    "Droit du travail", 
    "Droit civil",
    "Droit commercial",
    "Droit administratif",
    "Droit pénal"
]

strategie = st.selectbox("Stratégie de recherche (optionnel):", strategies)

if st.button("🔍 Lancer la Recherche", type="primary"):
    if situation:
        with st.spinner("🔎 Analyse stratégique en cours..."):
            try:
                resultats = moteur.analyser_et_rechercher_persistent(
                    situation, 
                    strategie if strategie != "Auto-détection" else None,
                    user_id="streamlit_user"  # À adapter pour multi-utilisateurs
                )
                
                st.session_state.resultats = resultats
                st.success("✅ Recherche terminée!")
                
            except Exception as e:
                st.error(f"❌ Erreur recherche: {e}")
    else:
        st.warning("⚠️ Veuillez décrire votre situation")

# Affichage résultats
if "resultats" in st.session_state:
    resultats = st.session_state.resultats
    
    # Métriques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Textes trouvés", len(resultats["legifrance"].get("results", [])))
    with col2:
        st.metric("Jurisprudence", len(resultats["judilibre"].get("results", [])))
    with col3:
        st.metric("Stratégie", resultats["analyse"].get("strategie_detectee", "N/A"))
    
    # Résultats Légifrance
    st.header("📚 Textes Législatifs")
    textes = resultats["legifrance"].get("results", [])
    
    if textes:
        for i, texte in enumerate(textes[:5]):  # Limite à 5 résultats
            with st.expander(f"📄 {texte.get('title', 'Sans titre')}"):
                st.write(f"**Code:** {texte.get('code', 'N/A')}")
                st.write(f"**Date:** {texte.get('date', 'N/A')}")
                st.write(f"**Contenu:** {texte.get('content', 'Non disponible')}")
                
                # Métadonnées
                col_meta1, col_meta2 = st.columns(2)
                with col_meta1:
                    st.caption(f"ID: {texte.get('id', 'N/A')}")
                with col_meta2:
                    st.caption(f"Nature: {texte.get('nature', 'N/A')}")
    else:
        st.info("Aucun texte législatif trouvé")
    
    # Résultats Judilibre
    st.header("⚖️ Jurisprudence")
    jurisprudences = resultats["judilibre"].get("results", [])
    
    if jurisprudences:
        for i, juri in enumerate(jurisprudences[:5]):  # Limite à 5 résultats
            with st.expander(f"⚖️ {juri.get('jurisdiction', 'Juridiction non précisée')}"):
                st.write(f"**Solution:** {juri.get('solution', 'Non précisée')}")
                st.write(f"**Date:** {juri.get('decision_date', 'N/A')}")
                st.write(f"**Résumé:** {juri.get('summary', 'Non disponible')}")
                
                # Métadonnées
                col_juri1, col_juri2 = st.columns(2)
                with col_juri1:
                    st.caption(f"N°: {juri.get('number', 'N/A')}")
                with col_juri2:
                    st.caption(f"ECLI: {juri.get('ecli', 'N/A')}")
    else:
        st.info("Aucune jurisprudence trouvée")
    
    # Section export (ADAPTÉE POUR CLOUD)
    st.header("📤 Export des Résultats")
    
    # Détection capacité PDF
    PDF_AVAILABLE = export_manager.is_pdf_available()
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        if st.button("💾 Export JSON"):
            export_path = export_manager.generer_export_json(resultats)
            with open(export_path, "rb") as f:
                st.download_button(
                    label="📥 Télécharger JSON",
                    data=f,
                    file_name=os.path.basename(export_path),
                    mime="application/json"
                )
    
    with col_exp2:
        if st.button("📝 Export Markdown"):
            export_path = export_manager.generer_export_markdown(resultats)
            with open(export_path, "rb") as f:
                st.download_button(
                    label="📥 Télécharger Markdown", 
                    data=f,
                    file_name=os.path.basename(export_path),
                    mime="text/markdown"
                )
    
    with col_exp3:
        if PDF_AVAILABLE:
            if st.button("📄 Export PDF"):
                with st.spinner("Génération PDF..."):
                    export_path = export_manager.generer_rapport_pdf(resultats)
                    with open(export_path, "rb") as f:
                        st.download_button(
                            label="📥 Télécharger PDF",
                            data=f,
                            file_name=os.path.basename(export_path),
                            mime="application/pdf"
                        )
        else:
            st.button("📄 Export PDF (indisponible)", disabled=True)
            st.caption("PDF non disponible en environnement cloud")

# Footer
st.markdown("---")
st.caption("⚡ OLIVIA ULTIMATE v3.0 - Powered by APIs PISTE")
