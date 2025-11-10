# app/middleware/correlation.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)

class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware pour ajouter un ID de corrélation à chaque requête"""
    
    async def dispatch(self, request: Request, call_next):
        # Récupère ou génère un request_id
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        
        # Ajoute le request_id à l'état de la requête
        request.state.request_id = request_id
        
        # Log de début de requête
        logger.info(f"Requête {request_id} - {request.method} {request.url.path}")
        
        # Traitement de la requête
        response = await call_next(request)
        
        # Ajoute le request_id dans les headers de réponse
        response.headers['X-Request-ID'] = request_id
        
        # Log de fin de requête
        logger.info(f"Réponse {request_id} - Statut {response.status_code}")
        
        return response
    