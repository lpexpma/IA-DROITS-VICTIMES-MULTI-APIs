# app/config.py - Version définitive
import os
from typing import Dict, Any

class Config:
    """Configuration pour OLIVIA"""
    
    def __init__(self):
        # Configuration de base
        self.HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))
        
        # Mode démo par défaut
        self.MODE_DEMO = True
        
        # Identifiants de démonstration
        self.JUDILIBRE_TOKEN_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        self.JUDILIBRE_CLIENT_ID = "demo_client_id"
        self.JUDILIBRE_CLIENT_SECRET = "demo_client_secret"
        self.JUDILIBRE_API_BASE = "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"
        
        self.LEGIFRANCE_TOKEN_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        self.LEGIFRANCE_CLIENT_ID = "demo_client_id"
        self.LEGIFRANCE_CLIENT_SECRET = "demo_client_secret"
        self.LEGIFRANCE_API_BASE = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        
        self.JUSTICE_BACK_TOKEN_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        self.JUSTICE_BACK_CLIENT_ID = "demo_client_id"
        self.JUSTICE_BACK_CLIENT_SECRET = "demo_client_secret"
        self.JUSTICE_BACK_API_BASE = "https://sandbox-api.piste.gouv.fr/minju/v1/Justiceback"
        
        # Feature flags
        self.FF_JUDILIBRE = True
        self.FF_LEGIFRANCE = True  
        self.FF_JUSTICEBACK = True

# Instance globale
CFG = Config()

print("✅ Configuration OLIVIA chargée (Mode Démo)")