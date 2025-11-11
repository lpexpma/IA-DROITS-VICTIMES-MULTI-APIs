# app/config.py - Version définitive
import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    """Configuration pour OLIVIA"""

    def __init__(self):
        # Configuration de base
        self.HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))
        self.USER_AGENT = os.getenv("USER_AGENT", "OLIVIA-ULTIMATE/3.0")

        # Mode démo par défaut (peut être écrasé via .env)
        self.MODE_DEMO = os.getenv("MODE_DEMO", "true").lower() == "true"

        # Base de données (utilisée par les services persistants)
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///olivia.db")
        self.SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

        # Identifiants de démonstration
        self.JUDILIBRE_TOKEN_URL = os.getenv(
            "JUDILIBRE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        )
        self.JUDILIBRE_CLIENT_ID = os.getenv("JUDILIBRE_CLIENT_ID", "demo_client_id")
        self.JUDILIBRE_CLIENT_SECRET = os.getenv("JUDILIBRE_CLIENT_SECRET", "demo_client_secret")
        self.JUDILIBRE_API_BASE = os.getenv(
            "JUDILIBRE_API_BASE", "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0"
        )

        self.LEGIFRANCE_TOKEN_URL = os.getenv(
            "LEGIFRANCE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        )
        self.LEGIFRANCE_CLIENT_ID = os.getenv("LEGIFRANCE_CLIENT_ID", "demo_client_id")
        self.LEGIFRANCE_CLIENT_SECRET = os.getenv("LEGIFRANCE_CLIENT_SECRET", "demo_client_secret")
        self.LEGIFRANCE_API_BASE = os.getenv(
            "LEGIFRANCE_API_BASE", "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        )

        self.JUSTICE_BACK_TOKEN_URL = os.getenv(
            "JUSTICE_BACK_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        )
        self.JUSTICE_BACK_CLIENT_ID = os.getenv("JUSTICE_BACK_CLIENT_ID", "demo_client_id")
        self.JUSTICE_BACK_CLIENT_SECRET = os.getenv(
            "JUSTICE_BACK_CLIENT_SECRET", "demo_client_secret"
        )
        self.JUSTICE_BACK_API_BASE = os.getenv(
            "JUSTICE_BACK_API_BASE", "https://sandbox-api.piste.gouv.fr/minju/v1/Justiceback"
        )

        # Feature flags
        self.FF_JUDILIBRE = os.getenv("FF_JUDILIBRE", "true").lower() == "true"
        self.FF_LEGIFRANCE = os.getenv("FF_LEGIFRANCE", "true").lower() == "true"
        self.FF_JUSTICEBACK = os.getenv("FF_JUSTICEBACK", "true").lower() == "true"


# Instance globale
CFG = Config()

print(
    "✅ Configuration OLIVIA chargée (Mode Démo)"
    if CFG.MODE_DEMO
    else "✅ Configuration OLIVIA chargée (Mode Production)"
)