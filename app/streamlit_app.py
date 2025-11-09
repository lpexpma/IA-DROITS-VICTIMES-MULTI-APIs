# app/streamlit_app.py
# -----------------------------------------
# OLIVIA Droits des Victimes – App autonome (UI + logique locale)
# Compatible Streamlit Cloud (share.streamlit.io) et local
# Python 3.10+, Streamlit 1.28+

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
# GESTION DES SECRETS MANQUANTS - CORRECTION CRITIQUE
# =========================

# Vérifier et définir les variables d'environnement manquantes AVANT tout
missing_vars = []
required_env_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]

for var in required_env_vars:
    if var not in os.environ:
        os.environ[var] = f"fake_{var.lower()}_for_demo"
        missing_vars.append(var)

# =========================
# CONFIGURATION STREAMLIT (DOIT ÊTRE APRÈS LA GESTION DES SECRETS)
# =========================

st.set_page_config(
    page_title="OLIVIA Droits Victimes – Autonome",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Afficher un avertissement si des clés sont manquantes
if missing_vars:
    st.warning(f"⚠️ Mode démo activé - Clés API manquantes: {', '.join(missing_vars)}")

APP_VERSION = "1.0.0-autonome"

# =========================
# FONCTION GET_SECRET (DOIT ÊTRE DÉFINIE AVANT UTILISATION)
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
# CONFIGURATION PISTE - SANDBOX
# =========================

def load_env_config() -> Dict[str, Any]:
    """Charge la configuration PISTE sandbox et autres paramètres."""
   
    # CORRECTION : Gestion sécurisée de HTTP_TIMEOUT
    http_timeout_str = get_secret("HTTP_TIMEOUT", "15")
    http_timeout = 15.0  # valeur par défaut
    if http_timeout_str is not None:
        try:
            http_timeout = float(http_timeout_str)
        except (ValueError, TypeError):
            http_timeout = 15.0
   
    return {
        # Identifiants communs aux 3 APIs
        "PISTE_CLIENT_ID": get_secret("PISTE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "PISTE_CLIENT_SECRET": get_secret("PISTE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
       
        # API LÉGIFRANCE
        "LEGIFRANCE_CLIENT_ID": get_secret("LEGIFRANCE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "LEGIFRANCE_CLIENT_SECRET": get_secret("LEGIFRANCE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
        "LEGIFRANCE_API_BASE": get_secret("LEGIFRANCE_API_BASE", "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"),
        "LEGIFRANCE_TOKEN_URL": get_secret("LEGIFRANCE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"),
       
        # API JUSTICE BACK  
        "JUSTICE_BACK_CLIENT_ID": get_secret("JUSTICE_BACK_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "JUSTICE_BACK_CLIENT_SECRET": get_secret("JUSTICE_BACK_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
        "JUSTICE_BACK_API_BASE": get_secret("JUSTICE_BACK_API_BASE", "https://sandbox-api.piste.gouv.fr/minju/v1/Justiceback"),
        "JUSTICE_BACK_TOKEN_URL": get_secret("JUSTICE_BACK_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"),
       
        # API JUDILIBRE
        "JUDILIBRE_CLIENT_ID": get_secret("JUDILIBRE_CLIENT_ID", "5518da20-9f9c-48ee-849b-1c0af46be1ff"),
        "JUDILIBRE_CLIENT_SECRET": get_secret("JUDILIBRE_CLIENT_SECRET", "19048806-5b4e-41cc-b419-ee1d7241151e"),
        "JUDILIBRE_API_BASE": get_secret("JUDILIBRE_API_BASE", "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"),
        "JUDILIBRE_TOKEN_URL": get_secret("JUDILIBRE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"),
       
        # Paramètres généraux
        "HTTP_TIMEOUT": http_timeout,
    }

CFG = load_env_config()

# =========================
# GESTION DES TOKENS PISTE
# =========================

@st.cache_data(show_spinner=False, ttl=3300)  # 55 minutes
def get_piste_token(client_id: str, client_secret: str, token_url: str) -> Optional[str]:
    """
    Récupère un token OAuth PISTE pour une API spécifique.
    """
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
    """Token spécifique pour Légifrance"""
    return get_piste_token(
        CFG["LEGIFRANCE_CLIENT_ID"],
        CFG["LEGIFRANCE_CLIENT_SECRET"],
        CFG["LEGIFRANCE_TOKEN_URL"]
    )

def get_justice_back_token() -> Optional[str]:
    """Token spécifique pour Justice Back"""
    return get_piste_token(
        CFG["JUSTICE_BACK_CLIENT_ID"],
        CFG["JUSTICE_BACK_CLIENT_SECRET"],
        CFG["JUSTICE_BACK_TOKEN_URL"]
    )

def get_judilibre_token() -> Optional[str]:
    """Token spécifique pour Judilibre"""
    return get_piste_token(
        CFG["JUDILIBRE_CLIENT_ID"],
        CFG["JUDILIBRE_CLIENT_SECRET"],
        CFG["JUDILIBRE_TOKEN_URL"]
    )

# =========================
# APIS PISTE - IMPLÉMENTATIONS
# =========================

def search_legifrance(query: str, page_size: int = 5) -> Tuple[bool, Any]:
    """
    Recherche dans Légifrance Sandbox.
    """
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
    """
    Recherche dans Justice Back Sandbox.
    """
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
    """
    Recherche dans Judilibre Sandbox.
    """
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
# Caching HTTP simple
# =========================

@st.cache_data(show_spinner=False, ttl=3600)
def cached_get(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: float = 15.0):
    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return r.text

@st.cache_data(show_spinner=False, ttl=3600)
def cached_post(url: str, data: Optional[Dict[str, Any]] = None, json_payload: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None, timeout: float = 15.0):
    r = requests.post(url, data=data, json=json_payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return r.text

# =========================
# Analyse locale des préjudices (démo)
# =========================

HEADS = [
    ("Déficit fonctionnel temporaire", "DFT"),
    ("Déficit fonctionnel permanent", "DFP"),
    ("Souffrances endurées", "SE"),
    ("Préjudice esthétique", "PE"),
    ("Préjudice d'agrément", "PA"),
    ("Frais médicaux et paramédicaux", "FM"),
    ("Frais de véhicule adapté / aménagement logement", "FVA"),
    ("Tierce personne (temporaire / permanent)", "TP"),
    ("Pertes de gains professionnels (actuels / futurs)", "PGPA/PGPF"),
    ("Incidence professionnelle", "IP"),
    ("Préjudice sexuel", "PS"),
    ("Préjudice scolaire / universitaire / de formation", "PSU"),
    ("Préjudice d'établissement", "PÉtab"),
    ("Préjudices des proches (d'affection, d'accompagnement…)", "PP"),
]

def quick_keywords(text: str) -> List[str]:
    """Extraction ultra-simple (démo) : découpe et filtre les mots significatifs."""
    if not text:
        return []
    raw = text.lower().replace("\n", " ")
    tokens = [t.strip(".,;:!?()[]{}\"'") for t in raw.split()]
    stop = {"le","la","les","un","une","des","de","du","au","aux","et","ou","dans","sur","par","pour","à","avec","en","d'","l'","deux","trois"}
    return sorted({t for t in tokens if len(t) >= 3 and t not in stop})

# app/streamlit_app.py
# CORRECTION DE LA FONCTION suggest_heads

def suggest_heads(description: str, role: str) -> pd.DataFrame:
    """
    Heuristiques de détection de chefs de préjudice pertinents
    (démo pédagogique, non substitut à un avis juridique).
    """
    kws = set(quick_keywords(description))
    rows = []
    for label, code in HEADS:
        score = 0
        # Scorings simplifiés pour la démo
        if code in ("DFT","DFP") and any(k in kws for k in ("fracture","hospitalisation","rééducation","handicap","ipp","consolidation")):
            score += 3
        if code == "SE" and any(k in kws for k in ("douleur","souffrance","algodystrophie","dépression","stress","anxiété")):
            score += 2
        if code == "PE" and any(k in kws for k in ("cicatrice","esthétique","séquelle")):
            score += 2
        if code == "TP" and any(k in kws for k in ("aide","tierce","accompagne","autonomie","garde")):
            score += 2
        if code.startswith("PGP") and any(k in kws for k in ("arrêt","travail","perte","salaire","emploi","licenciement")):
            score += 2
        if code == "IP" and any(k in kws for k in ("reconversion","adaptation","poste","handicap")):
            score += 1
        if code == "FM" and any(k in kws for k in ("kiné","irm","radio","soins","médicaments","prothèse","fauteuil")):
            score += 1
        if role.lower() == "conducteur" and "faute" in kws:
            score += 0
        
        # CORRECTION : Assurer que le score est un entier, pas None
        final_score = min(int(score), 5) if score is not None else 0
        rows.append({
            "Chef de préjudice": label, 
            "Code": code, 
            "Pertinence (0-5)": final_score
        })
    
    # CORRECTION : Créer le DataFrame SANS dtype= puis convertir les types
    df = pd.DataFrame(rows)
    
    # Convertir les types explicitement
    df["Chef de préjudice"] = df["Chef de préjudice"].astype(str)
    df["Code"] = df["Code"].astype(str)
    df["Pertinence (0-5)"] = df["Pertinence (0-5)"].astype(int)
    
    return df.sort_values(by="Pertinence (0-5)", ascending=False).reset_index(drop=True)

def make_markdown_summary(form_values: Dict[str, Any], heads_df: pd.DataFrame) -> str:
    bullets = "\n".join(
        f"- {row['Chef de préjudice']} ({row['Code']}) — score {row['Pertinence (0-5)']}"
        for _, row in heads_df.iterrows()
    )
    desc_block = textwrap.indent(form_values.get("description","").strip(), "    ")
    return f"""# Note d'analyse (préjudices corporels)

**Date**: {date.today().isoformat()}
**Victime**: {form_values.get('role','(non précisé)')}
**Accident**: {form_values.get('type_accident','(non précisé)')} — **Date**: {form_values.get('date_accident') or '(non précisée)'}
**Consolidation**: {form_values.get('date_consolidation') or '(non précisée)'}
**Description (extrait)**:
{desc_block}

## Chefs de préjudices potentiels (triés par pertinence)
{bullets}

> ⚠️ Outil d'aide à la structuration. Ne remplace pas une expertise médicale ni un avis juridique.
"""

# =========================
# UI AMÉLIORÉE AVEC PISTE
# =========================

def sidebar():
    st.sidebar.header("⚙️ Paramètres")
    st.sidebar.markdown(
        f"- **Version app**: `{APP_VERSION}`\n"
        f"- **Mode**: Sandbox PISTE activé\n"
        f"- **Environnement**: Sandbox\n"
    )
    show_raw = st.sidebar.checkbox("Afficher les structures brutes (JSON)", value=False)
    st.sidebar.divider()
    st.sidebar.subheader("🔐 Configuration PISTE")
    st.sidebar.markdown(
        "- **Légifrance**: ✅ Sandbox\n"
        "- **Justice Back**: ✅ Sandbox\n"
        "- **Judilibre**: ✅ Sandbox\n"
        "- **Client ID**: `5518da20-9f9c-48ee-849b-1c0af46be1ff`\n"
    )
    return {"show_raw": show_raw}

def form_section() -> Dict[str, Any]:
    st.subheader("📝 Situation de la victime")
    with st.form("form_victime"):
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            role = st.selectbox("Qualité de la victime", ["Piéton", "Passager", "Conducteur", "Cycliste", "Autre"], index=0)
            type_accident = st.selectbox("Type d'accident", ["Accident de la circulation", "Accident médical", "Agression", "Autre"], index=0)
        with c2:
            # CORRECTION : Gestion sécurisée des dates
            date_accident_input = st.date_input("Date de l'accident", value=None, format="DD/MM/YYYY")
            date_conso_input = st.date_input("Date de consolidation (si connue)", value=None, format="DD/MM/YYYY")
           
            # CORRECTION : Gestion robuste du tuple vide
            def safe_extract_date(date_input):
                if isinstance(date_input, tuple):
                    if len(date_input) > 0:
                        return date_input[0]
                    else:
                        return None
                return date_input
           
            date_accident = safe_extract_date(date_accident_input)
            date_conso = safe_extract_date(date_conso_input)
           
        with c3:
            commune = st.text_input("Commune (facultatif)")
            code_postal = st.text_input("Code postal (facultatif)")

        description = st.text_area(
            "Description libre (faits, lésions, soins, arrêts, impacts…)",
            height=180,
            placeholder="Décris les circonstances, les blessures, les soins, les arrêts de travail, etc."
        )

        submitted = st.form_submit_button("Analyser la situation", use_container_width=True)
    return {
        "submitted": submitted,
        "role": role,
        "type_accident": type_accident,
        "date_accident": date_accident.isoformat() if date_accident else None,
        "date_consolidation": date_conso.isoformat() if date_conso else None,
        "commune": commune,
        "code_postal": code_postal,
        "description": description,
    }

def results_section(form_values: Dict[str, Any], opts: Dict[str, Any]):
    st.subheader("📊 Analyse de premiers chefs de préjudice")
    df = suggest_heads(form_values.get("description",""), form_values.get("role",""))
    st.dataframe(df, use_container_width=True, height=420)

    # Export
    c1, c2, c3 = st.columns([1,1,1])
    md = make_markdown_summary(form_values, df)
    with c1:
        st.download_button(
            "Télécharger la note (Markdown)",
            data=md.encode("utf-8"),
            file_name=f"note_prejudices_{date.today().isoformat()}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        payload = {"form": form_values, "analysis": df.to_dict(orient="records")}
        st.download_button(
            "Exporter en JSON",
            data=json.dumps(payload, ensure_ascii=False, indent=2),
            file_name=f"analyse_prejudices_{date.today().isoformat()}.json",
            mime="application/json",
            use_container_width=True,
        )
    with c3:
        st.info("Astuce : vous pouvez joindre la note à un e-mail ou l'importer dans un dossier.")

    if opts.get("show_raw"):
        with st.expander("Détails (debug)"):
            st.write("Form values:", form_values)
            st.json(payload)

def jurisprudence_section():
    st.subheader("🔎 Recherche PISTE Sandbox")
    query = st.text_input(
        "Mots-clés pour la recherche juridique",
        "indemnisation victime accident circulation",
        placeholder="Ex: déficit fonctionnel temporaire IPP 10%"
    )
   
    col1, col2, col3 = st.columns([1,1,1])
   
    with col1:
        if st.button("🔍 Légifrance", use_container_width=True):
            with st.spinner("Recherche dans Légifrance Sandbox..."):
                ok, data = search_legifrance(query)
                if ok:
                    st.success(f"✅ {len(data.get('results', []))} résultats Légifrance")
                    st.json(data)
                else:
                    st.error(f"❌ {data}")
   
    with col2:
        if st.button("⚖️ Justice Back", use_container_width=True):
            with st.spinner("Recherche dans Justice Back Sandbox..."):
                ok, data = search_justice_back(query)
                if ok:
                    st.success(f"✅ {len(data.get('results', []))} résultats Justice Back")
                    st.json(data)
                else:
                    st.error(f"❌ {data}")
   
    with col3:
        if st.button("📚 Judilibre", use_container_width=True):
            with st.spinner("Recherche dans Judilibre Sandbox..."):
                ok, data = search_judilibre(query)
                if ok:
                    st.success(f"✅ {len(data.get('results', []))} résultats Judilibre")
                    st.json(data)
                else:
                    st.error(f"❌ {data}")

def footer():
    st.divider()
    st.caption(
        "IA d'aide à la structuration des préjudices • Sandbox PISTE • "
        f"v{APP_VERSION} • Ne remplace ni une expertise médicale ni un conseil d'avocat."
    )

# =========================
# Entrée principale
# =========================

def main():
    st.title("⚖️ OLIVIA Droits des Victimes — Sandbox PISTE")
    st.write(
        "Cette application utilise les **APIs PISTE Sandbox** pour vous aider à structurer les informations "
        "d'un dossier et rechercher des références juridiques."
    )

    # Test de connexion PISTE
    with st.expander("🔧 Test de connexion PISTE", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Test Légifrance"):
                token = get_legifrance_token()
                if token:
                    st.success("✅ Légifrance: Token valide")
                else:
                    st.error("❌ Légifrance: Échec authentification")
        with col2:
            if st.button("Test Justice Back"):
                token = get_justice_back_token()
                if token:
                    st.success("✅ Justice Back: Token valide")
                else:
                    st.error("❌ Justice Back: Échec authentification")
        with col3:
            if st.button("Test Judilibre"):
                token = get_judilibre_token()
                if token:
                    st.success("✅ Judilibre: Token valide")
                else:
                    st.error("❌ Judilibre: Échec authentification")

    opts = sidebar()
    form_values = form_section()

    if form_values["submitted"]:
        if not form_values.get("description"):
            st.error("Merci d'ajouter quelques informations dans la description pour lancer l'analyse.")
        else:
            results_section(form_values, opts)
            st.divider()
            jurisprudence_section()

    footer()

if __name__ == "__main__":
    main()