# app/streamlit_app.py - VERSION CORRECTE
# =========================

import os
import json
import time
import math
import textwrap
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

import requests
import pandas as pd
import streamlit as st

# =========================
# GESTION DES SECRETS MANQUANTS
# =========================

missing_vars = []
required_env_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]

for var in required_env_vars:
    if var not in os.environ:
        os.environ[var] = f"fake_{var.lower()}_for_demo"
        missing_vars.append(var)

# =========================
# CONFIGURATION STREAMLIT
# =========================

st.set_page_config(
    page_title="OLIVIA Droits Victimes – Autonome",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if missing_vars:
    st.warning(f"⚠️ Mode démo activé - Clés API manquantes: {', '.join(missing_vars)}")

APP_VERSION = "1.0.0-autonome"

# =========================
# FONCTIONS DE BASE
# =========================

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Récupère une valeur depuis st.secrets puis os.environ, avec fallback."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# =========================
# CONFIGURATION PISTE
# =========================

def load_env_config() -> Dict[str, Any]:
    http_timeout_str = get_secret("HTTP_TIMEOUT", "15")
    http_timeout = 15.0
    if http_timeout_str is not None:
        try:
            http_timeout = float(http_timeout_str)
        except (ValueError, TypeError):
            http_timeout = 15.0
   
    return {
        "PISTE_CLIENT_ID": get_secret("PISTE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "PISTE_CLIENT_SECRET": get_secret("PISTE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
        "LEGIFRANCE_CLIENT_ID": get_secret("LEGIFRANCE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "LEGIFRANCE_CLIENT_SECRET": get_secret("LEGIFRANCE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
        "LEGIFRANCE_API_BASE": get_secret("LEGIFRANCE_API_BASE", "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"),
        "LEGIFRANCE_TOKEN_URL": get_secret("LEGIFRANCE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"),
        "JUSTICE_BACK_CLIENT_ID": get_secret("JUSTICE_BACK_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "JUSTICE_BACK_CLIENT_SECRET": get_secret("JUSTICE_BACK_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
        "JUSTICE_BACK_API_BASE": get_secret("JUSTICE_BACK_API_BASE", "https://sandbox-api.piste.gouv.fr/minju/v1/Justiceback"),
        "JUSTICE_BACK_TOKEN_URL": get_secret("JUSTICE_BACK_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"),
        "JUDILIBRE_CLIENT_ID": get_secret("JUDILIBRE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "JUDILIBRE_CLIENT_SECRET": get_secret("JUDILIBRE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
        "JUDILIBRE_API_BASE": get_secret("JUDILIBRE_API_BASE", "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"),
        "JUDILIBRE_TOKEN_URL": get_secret("JUDILIBRE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"),
        "HTTP_TIMEOUT": http_timeout,
    }

CFG = load_env_config()

# =========================
# APIS PISTE
# =========================

@st.cache_data(show_spinner=False, ttl=3300)
def get_piste_token(client_id: str, client_secret: str, token_url: str) -> Optional[str]:
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(token_url, data=data, headers=headers, timeout=CFG["HTTP_TIMEOUT"])
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token")
    except Exception as e:
        st.error(f"❌ Erreur d'authentification PISTE: {e}")
        return None

def get_legifrance_token() -> Optional[str]:
    return get_piste_token(
        CFG["LEGIFRANCE_CLIENT_ID"],
        CFG["LEGIFRANCE_CLIENT_SECRET"],
        CFG["LEGIFRANCE_TOKEN_URL"]
    )

def get_justice_back_token() -> Optional[str]:
    return get_piste_token(
        CFG["JUSTICE_BACK_CLIENT_ID"],
        CFG["JUSTICE_BACK_CLIENT_SECRET"],
        CFG["JUSTICE_BACK_TOKEN_URL"]
    )

def get_judilibre_token() -> Optional[str]:
    return get_piste_token(
        CFG["JUDILIBRE_CLIENT_ID"],
        CFG["JUDILIBRE_CLIENT_SECRET"],
        CFG["JUDILIBRE_TOKEN_URL"]
    )

def search_legifrance(query: str, page_size: int = 5) -> Tuple[bool, Any]:
    token = get_legifrance_token()
    if not token:
        return False, "Token Légifrance non disponible"
   
    try:
        url = f"{CFG['LEGIFRANCE_API_BASE']}/search"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "pageSize": page_size,
            "searchType": "ALL"
        }
        response = requests.post(url, json=payload, headers=headers, timeout=CFG["HTTP_TIMEOUT"])
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, f"Erreur recherche Légifrance: {e}"

def search_justice_back(query: str, domain: str = "civil") -> Tuple[bool, Any]:
    token = get_justice_back_token()
    if not token:
        return False, "Token Justice Back non disponible"
   
    try:
        url = f"{CFG['JUSTICE_BACK_API_BASE']}/search"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "domain": domain,
            "limit": 5
        }
        response = requests.post(url, json=payload, headers=headers, timeout=CFG["HTTP_TIMEOUT"])
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, f"Erreur recherche Justice Back: {e}"

def search_judilibre(query: str, page_size: int = 5) -> Tuple[bool, Any]:
    token = get_judilibre_token()
    if not token:
        return False, "Token Judilibre non disponible"
   
    try:
        url = f"{CFG['JUDILIBRE_API_BASE']}/search"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "q": query,
            "page_size": page_size
        }
        response = requests.get(url, params=params, headers=headers, timeout=CFG["HTTP_TIMEOUT"])
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, f"Erreur recherche Judilibre: {e}"

# =========================
# IMPORT DES MODULES EXPERTS
# =========================

try:
    from app.analyse_victime import analyseur
    from app.affichage_analyse import affichage
    MODE_EXPERT_ACTIF = True
except ImportError as e:
    st.error(f"❌ **Modules experts manquants** : {e}")
    st.warning("""
    ⚠️ **Créer les fichiers manquants :**
    
    1. Créez `app/analyse_victime.py` avec le code fourni
    2. Créez `app/affichage_analyse.py` avec le code fourni  
    3. Redémarrez l'application
    
    **Mode simple activé en attendant...**
    """)
    
    # Fallback vers le mode simple
    class AnalyseurSimple:
        def analyser_situation_complete(self, description: str, role: str = "victime"):
            return {
                "metadata": {"mode": "simple", "erreur": "Modules experts manquants"},
                "analyse_prejudices": {"score_gravite_globale": 0},
                "elements_defense": [],
                "strategie_indemnisation": {"estimation_globale": {}},
                "recommandations_actions": [{"action": "Installer modules experts", "priorite": "Élevée"}]
            }
    
    class AffichageSimple:
        def afficher_analyse_complete(self, analyse):
            st.error("❌ **SYSTÈME EXPERT NON DISPONIBLE**")
            st.warning("Installez les modules d'analyse avancée")
    
    analyseur = AnalyseurSimple()
    affichage = AffichageSimple()
    MODE_EXPERT_ACTIF = False

# =========================
# FONCTIONS UI
# =========================

def sidebar():
    st.sidebar.header("⚙️ Paramètres")
    st.sidebar.markdown(f"- **Version**: `{APP_VERSION}`")
    st.sidebar.markdown("- **Mode**: Simple (modules avancés manquants)")
    return {"show_raw": False}

def form_section() -> Dict[str, Any]:
    st.subheader("📝 Situation de la victime")
    with st.form("form_victime"):
        col1, col2 = st.columns(2)
        with col1:
            role = st.selectbox("Qualité", ["Piéton", "Passager", "Conducteur", "Cycliste", "Autre"])
            type_accident = st.selectbox("Type d'accident", ["Accident de la circulation", "Accident médical", "Agression", "Autre"])
        with col2:
            date_accident = st.date_input("Date de l'accident", value=None)
            date_conso = st.date_input("Date consolidation", value=None)

        description = st.text_area(
            "Description de la situation",
            height=150,
            placeholder="Décrivez les circonstances, blessures, soins, impacts..."
        )

        submitted = st.form_submit_button("Analyser la situation", use_container_width=True)
    
    return {
        "submitted": submitted,
        "role": role,
        "type_accident": type_accident,
        "date_accident": date_accident.isoformat() if date_accident else None,
        "date_consolidation": date_conso.isoformat() if date_conso else None,
        "description": description,
    }

def results_section(form_values: Dict[str, Any], opts: Dict[str, Any]):
    st.subheader("📊 Analyse Avancée de la Situation")
    
    with st.spinner("🔍 Analyse approfondie en cours..."):
        analyse_complete = analyseur.analyser_situation_complete(
            form_values.get("description", ""), 
            form_values.get("role", "victime")
        )
    
    affichage.afficher_analyse_complete(analyse_complete)
    
    # Export
    st.divider()
    st.subheader("💾 Export des Résultats")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Exporter JSON", use_container_width=True):
            data_str = json.dumps(analyse_complete, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                "💾 Télécharger",
                data=data_str,
                file_name=f"analyse_{date.today().isoformat()}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📝 Générer rapport", use_container_width=True):
            rapport = f"""
# RAPPORT D'ANALYSE
**Date**: {date.today().isoformat()}

## Situation
{form_values.get('description', '')}

## Score
{analyse_complete['analyse_prejudices']['score_gravite_globale']}/100

*Généré par OLIVIA Droits des Victimes*
"""
            st.download_button(
                "📄 Télécharger",
                data=rapport.encode('utf-8'),
                file_name=f"rapport_{date.today().isoformat()}.md",
                mime="text/markdown"
            )

def jurisprudence_section():
    st.subheader("🔎 Recherche Juridique")
    query = st.text_input("Mots-clés", "indemnisation victime accident")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Légifrance", use_container_width=True):
            with st.spinner("Recherche..."):
                ok, data = search_legifrance(query)
                if ok:
                    st.success("✅ Résultats trouvés")
                    st.json(data)
                else:
                    st.error(f"❌ {data}")
    
    with col2:
        if st.button("📚 Judilibre", use_container_width=True):
            with st.spinner("Recherche..."):
                ok, data = search_judilibre(query)
                if ok:
                    st.success("✅ Résultats trouvés")
                    st.json(data)
                else:
                    st.error(f"❌ {data}")

def footer():
    st.divider()
    st.caption(f"OLIVIA Droits des Victimes • v{APP_VERSION}")

# =========================
# MAIN
# =========================

def main():
    st.title("⚖️ OLIVIA - Assistant Défense Victimes")
    st.write("**Système d'analyse juridique pour la défense des victimes**")
    
    # Avertissement modules manquants
    st.warning("""
    ⚠️ **Mode simple activé** 
    - Les modules d'analyse avancée ne sont pas installés
    - Créez les fichiers `app/analyse_victime.py` et `app/affichage_analyse.py` pour activer l'analyse experte
    """)
    
    opts = sidebar()
    form_values = form_section()

    if form_values["submitted"]:
        if not form_values.get("description"):
            st.error("❌ Veuillez décrire la situation")
        else:
            results_section(form_values, opts)
            st.divider()
            jurisprudence_section()

    footer()

if __name__ == "__main__":
    main()
