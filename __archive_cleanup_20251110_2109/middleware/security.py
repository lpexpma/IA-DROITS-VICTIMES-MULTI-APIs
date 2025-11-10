# app/middleware/security.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware pour les headers de sécurité HTTP"""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Headers de sécurité modernes (2025)
        security_headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            # X-XSS-Protection retiré car obsolète - CSP est la protection moderne
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
            
        return response
    