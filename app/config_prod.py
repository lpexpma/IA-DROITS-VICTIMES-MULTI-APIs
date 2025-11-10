# app/config_prod.py - Configuration PRODUCTION PISTE
import os

class ConfigProduction:
    """Configuration PISTE production"""
    
    def __init__(self):
        # URLs PRODUCTION PISTE
        self.LEGIFRANCE_API_BASE = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        self.JUDILIBRE_API_BASE = "https://api.piste.gouv.fr/cassation/judilibre/v1.0"
        self.JUSTICE_BACK_API_BASE = "https://api.piste.gouv.fr/minju/v1/Justiceback"
        
        # Tokens production (à définir dans les variables d'environnement)
        self.LEGIFRANCE_CLIENT_ID = os.getenv("LEGIFRANCE_CLIENT_ID_PROD")
        self.LEGIFRANCE_CLIENT_SECRET = os.getenv("LEGIFRANCE_CLIENT_SECRET_PROD")
        
        # Configuration optimisée production
        self.HTTP_TIMEOUT = 30
        self.MODE_DEMO = os.getenv("MODE_DEMO", "false").lower() == "true"
        self.USER_AGENT = "OLIVIA-PROD/3.0 (Recherche Juridique Professionnelle)"
        
        # Quotas et limitations
        self.MAX_REQUESTS_PER_MINUTE = 60
        self.CACHE_TTL = 600  # 10 minutes en production

CFG_PROD = ConfigProduction()
