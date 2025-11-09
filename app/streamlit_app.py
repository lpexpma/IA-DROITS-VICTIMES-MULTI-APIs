# app/streamlit_app.py
import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="🤖 Assistant Juridique OLIVIA Droits Victimes",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .prejudice-card {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<h1 class="main-header">🤖 Assistant Juridique OLIVIA Droits Victimes</h1>', unsafe_allow_html=True)

# Sidebar avec informations
with st.sidebar:
    st.header("ℹ️ À propos")
    st.markdown("""
    Cet assistant juridique IA vous aide à :
    - 🔍 **Analyser** votre situation juridique
    - ⚖️ **Identifier** vos préjudices
    - 📚 **Trouver** les textes de loi applicables
    - 🏛️ **Localiser** les juridictions compétentes
    - 💰 **Estimer** votre indemnisation
    
    *Données officielles : Légifrance, Justice Back, Judilibre*
    """)
    
    # Vérification du statut des APIs
    st.header("🔧 Statut des services")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=10)
        if response.status_code == 200:
            st.success("✅ API principale connectée")
        else:
            st.error("❌ API principale hors ligne")
    except:
        st.error("❌ Impossible de contacter l'API")

# Section principale
tab1, tab2, tab3 = st.tabs(["📝 Analyse de Situation", "🔍 Recherche Juridique", "🏛️ Lieux de Justice"])

with tab1:
    st.header("📝 Analyse Complète de Votre Situation")
    
    # Formulaire de saisie
    with st.form("analyse_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            situation = st.text_area(
                "Décrivez votre situation en détail :",
                height=150,
                placeholder="Exemple : J'ai eu un accident de voiture le 15 mars, fracture du bras, arrêt de travail de 2 mois, perte de salaire..."
            )
        
        with col2:
            code_postal = st.text_input(
                "Code postal (pour trouver les juridictions proches) :",
                placeholder="75001",
                max_chars=5
            )
            
            type_situation = st.selectbox(
                "Type de situation :",
                ["Accident de la route", "Accident médical", "Harcèlement", "Préjudice corporel", "Litige consommation", "Autre"]
            )
        
        submitted = st.form_submit_button("🚀 Analyser ma situation", use_container_width=True)
    
    # Traitement de l'analyse
    if submitted:
        if not situation:
            st.error("❌ Veuillez décrire votre situation")
        else:
            with st.spinner("🔍 L'IA analyse votre situation..."):
                try:
                    # Appel à l'API d'analyse
                    response = requests.post(
                        "http://localhost:8000/api/analyser-situation",
                        json={
                            "description_situation": situation,
                            "code_postal": code_postal if code_postal else None
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        
                        # Affichage des résultats
                        st.success("✅ Analyse terminée avec succès !")
                        
                        # 1. Préjudices détectés
                        st.subheader("⚖️ Préjudices identifiés")
                        analyse_desc = results.get("analyse_description", {})
                        prejudices = analyse_desc.get("prejudices_detectes", [])
                        
                        for prejudice in prejudices:
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"**{prejudice['categorie']}**")
                                    st.markdown(f"*{prejudice['description']}*")
                                with col2:
                                    st.markdown(f"**Confiance :** {prejudice.get('confiance', 'N/A')}")
                        
                        # 2. Estimation d'indemnisation
                        st.subheader("💰 Estimation d'indemnisation")
                        estimation = results.get("estimation_indemnisation", {})
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Fourchette basse",
                                f"{estimation.get('fourchette_basse', 0):,} €".replace(",", " ")
                            )
                        with col2:
                            st.metric(
                                "Fourchette haute", 
                                f"{estimation.get('fourchette_haute', 0):,} €".replace(",", " ")
                            )
                        with col3:
                            st.metric(
                                "Complexité",
                                estimation.get('niveau_complexite', 'Moyenne')
                            )
                        
                        # 3. Jurisprudence
                        st.subheader("📚 Jurisprudence pertinente")
                        jurisprudence = results.get("jurisprudence_par_prejudice", {})
                        
                        for prejudice_type, arrets in jurisprudence.items():
                            with st.expander(f"📋 Jurisprudence - {prejudice_type}"):
                                if isinstance(arrets, list):
                                    for arret in arrets[:3]:  # Limiter à 3 arrêts par préjudice
                                        st.markdown(f"**{arret.get('titre', 'Arrêt')}**")
                                        st.markdown(f"*{arret.get('juridiction', 'Juridiction')} - {arret.get('date', 'Date')}*")
                                        st.markdown(f"{arret.get('resume', 'Aucun résumé')}")
                                        st.markdown("---")
                                else:
                                    st.warning("Aucune jurisprudence trouvée")
                        
                        # 4. Ressources locales
                        if code_postal and results.get("ressources_locales"):
                            st.subheader("🏛️ Ressources locales")
                            lieux = results["ressources_locales"].get("lieux", [])
                            
                            for lieu in lieux[:3]:  # Limiter à 3 lieux
                                with st.container():
                                    st.markdown(f"**{lieu['titre']}**")
                                    st.markdown(f"📍 {lieu['adresse']}")
                                    if lieu.get('telephone') and lieu['telephone'] != "Non renseigné":
                                        st.markdown(f"📞 {lieu['telephone']}")
                                    st.markdown("---")
                        
                        # 5. Recommandations
                        st.subheader("💡 Recommandations")
                        recommandations = results.get("recommandations_generales", [])
                        
                        for reco in recommandations:
                            st.markdown(f"• {reco}")
                            
                    else:
                        st.error(f"❌ Erreur lors de l'analyse : {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Erreur de connexion à l'API : {str(e)}")
                except Exception as e:
                    st.error(f"❌ Erreur inattendue : {str(e)}")

with tab2:
    st.header("🔍 Recherche Juridique Avancée")
    
    with st.form("recherche_form"):
        recherche_texte = st.text_input(
            "Termes de recherche :",
            placeholder="ex: responsabilité civile accident"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            apis_legifrance = st.checkbox("📚 Légifrance (textes de loi)", value=True)
        with col2:
            apis_judilibre = st.checkbox("⚖️ Judilibre (jurisprudence)", value=True)
        with col3:
            apis_justice = st.checkbox("🏛️ Justice Back (ressources)", value=False)
        
        submitted_recherche = st.form_submit_button("🔎 Lancer la recherche")
    
    if submitted_recherche:
        if not recherche_texte:
            st.error("❌ Veuillez saisir des termes de recherche")
        else:
            with st.spinner("🔍 Recherche en cours..."):
                try:
                    apis_includes = []
                    if apis_legifrance: apis_includes.append("legifrance")
                    if apis_judilibre: apis_includes.append("judilibre") 
                    if apis_justice: apis_includes.append("justice_back")
                    
                    response = requests.post(
                        "http://localhost:8000/api/recherche-complete",
                        json={
                            "description_situation": recherche_texte,
                            "include_apis": apis_includes
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        st.success(f"✅ {len(apis_includes)} source(s) consultée(s)")
                        
                        # Affichage des résultats par API
                        if apis_legifrance and results.get("legifrance"):
                            st.subheader("📚 Textes Législatifs")
                            for texte in results["legifrance"]:
                                with st.expander(f"📄 {texte['titre']}"):
                                    st.markdown(f"**Nature :** {texte['nature']}")
                                    st.markdown(f"**Date :** {texte['date']}")
                                    st.markdown(f"**Résumé :** {texte['resume']}")
                        
                        if apis_judilibre and results.get("judilibre"):
                            st.subheader("⚖️ Jurisprudence")
                            for arret in results["judilibre"]:
                                with st.expander(f"⚖️ {arret['titre']}"):
                                    st.markdown(f"**Juridiction :** {arret['juridiction']}")
                                    st.markdown(f"**Date :** {arret['date']}")
                                    st.markdown(f"**Résumé :** {arret['resume']}")
                        
                        if apis_justice and results.get("justice_back"):
                            st.subheader("🏛️ Ressources Justice")
                            for lieu in results["justice_back"]:
                                st.markdown(f"**{lieu['titre']}**")
                                st.markdown(f"📍 {lieu['adresse']}")
                                
                    else:
                        st.error("❌ Erreur lors de la recherche")
                        
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

with tab3:
    st.header("🏛️ Recherche de Lieux de Justice")
    
    with st.form("lieux_form"):
        code_postal_lieux = st.text_input(
            "Code postal pour trouver les juridictions :",
            placeholder="75001",
            max_chars=5
        )
        
        submitted_lieux = st.form_submit_button("🗺️ Trouver les juridictions")
    
    if submitted_lieux:
        if not code_postal_lieux or not code_postal_lieux.isdigit() or len(code_postal_lieux) != 5:
            st.error("❌ Veuillez saisir un code postal valide (5 chiffres)")
        else:
            with st.spinner("🔍 Recherche des juridictions..."):
                try:
                    response = requests.get(
                        f"http://localhost:8000/api/lieux-justice?code_postal={code_postal_lieux}",
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        lieux = results.get("lieux", [])
                        
                        if lieux:
                            st.success(f"✅ {len(lieux)} lieu(x) de justice trouvé(s)")
                            
                            # Affichage sous forme de carte ou liste
                            for lieu in lieux:
                                with st.container():
                                    st.markdown(f"### {lieu['titre']}")
                                    st.markdown(f"**Adresse :** {lieu['adresse']}")
                                    
                                    if lieu.get('telephone') and lieu['telephone'] != "Non renseigné":
                                        st.markdown(f"**Téléphone :** {lieu['telephone']}")
                                    
                                    if lieu.get('courriel') and lieu['courriel'] != "Non renseigné":
                                        st.markdown(f"**Email :** {lieu['courriel']}")
                                    
                                    if lieu.get('horaire') and lieu['horaire'] != "Non renseigné":
                                        st.markdown(f"**Horaires :** {lieu['horaire']}")
                                    
                                    st.markdown("---")
                        else:
                            st.warning("ℹ️ Aucun lieu de justice trouvé pour ce code postal")
                            
                    else:
                        st.error("❌ Erreur lors de la recherche des lieux")
                        
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "**OLIVIA Droits Victimes** • Assistant juridique intelligent • "
    "[Documentation API](http://localhost:8000/api/docs) • "
    f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
