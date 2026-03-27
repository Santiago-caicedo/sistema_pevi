"""
Middleware de seguridad personalizado para Sistema PEVI.

Incluye Content Security Policy (CSP) para prevenir ataques XSS.
"""


class ContentSecurityPolicyMiddleware:
    """
    Middleware que agrega headers CSP a todas las respuestas.

    CSP indica al navegador qué fuentes de contenido son confiables,
    bloqueando scripts/estilos de fuentes no autorizadas.
    """

    # =========================================================================
    # FUENTES EXTERNAS AUTORIZADAS
    # =========================================================================
    #
    # Si agregas una nueva librería externa, debes añadirla aquí:
    #
    # - cdn.jsdelivr.net     → Bootstrap CSS/JS, Bootstrap Icons, Chart.js
    # - cdnjs.cloudflare.com → Anime.js (animaciones sitio público)
    # - fonts.googleapis.com → Hojas de estilo de Google Fonts
    # - fonts.gstatic.com    → Archivos de fuentes (woff2)
    # - vadomdata.s3.amazonaws.com → Archivos estáticos y media en producción
    #
    # =========================================================================

    def __init__(self, get_response):
        self.get_response = get_response

        # Dominios autorizados por tipo de recurso
        self.csp_directives = {
            # Scripts: solo de estos CDNs, S3 (admin en producción) y del propio servidor
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Requerido para scripts inline en templates
                "cdn.jsdelivr.net",
                "cdnjs.cloudflare.com",
                "vadomdata.s3.amazonaws.com",
            ],

            # Estilos: CDNs + Google Fonts + S3 (admin en producción) + inline
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Requerido para estilos inline en templates
                "cdn.jsdelivr.net",
                "cdnjs.cloudflare.com",
                "fonts.googleapis.com",
                "vadomdata.s3.amazonaws.com",
            ],

            # Fuentes: Google Fonts + Bootstrap Icons
            'font-src': [
                "'self'",
                "fonts.gstatic.com",
                "cdn.jsdelivr.net",
            ],

            # Imágenes: servidor propio, S3, data URIs, y fuentes externas del sitio público
            'img-src': [
                "'self'",
                "data:",  # Para imágenes base64 inline
                "vadomdata.s3.amazonaws.com",
                "p4.wallpaperbetter.com",       # Hero home
                "wallpapers.com",               # Hero home
                "img.freepik.com",              # Hero home
                "lirp.cdn-website.com",         # Sección home
                "*.basemaps.cartocdn.com",      # Tiles mapa resultados
            ],

            # Conexiones AJAX/Fetch: servidor propio + CDN source maps
            'connect-src': [
                "'self'",
                "cdn.jsdelivr.net",  # Source maps de Bootstrap/Chart.js
            ],

            # Frames: no permitir embeber en iframes (anti-clickjacking)
            'frame-ancestors': [
                "'none'",
            ],

            # Formularios: solo enviar al propio servidor
            'form-action': [
                "'self'",
            ],

            # Base URI: prevenir ataques de base tag injection
            'base-uri': [
                "'self'",
            ],

            # Objetos embebidos (Flash, etc.): bloqueados
            'object-src': [
                "'none'",
            ],
        }

    def __call__(self, request):
        response = self.get_response(request)

        # Construir el header CSP
        csp_parts = []
        for directive, sources in self.csp_directives.items():
            csp_parts.append(f"{directive} {' '.join(sources)}")

        csp_header = "; ".join(csp_parts)

        # Agregar el header a la respuesta
        response['Content-Security-Policy'] = csp_header

        # Headers de seguridad adicionales
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
