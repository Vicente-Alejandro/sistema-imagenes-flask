"""
Manejadores de errores para la aplicación
"""
from flask import render_template, request, jsonify

def register_error_handlers(app):
    """
    Registra los manejadores de error para la aplicación
    
    Args:
        app: La instancia de la aplicación Flask
    """
    
    @app.errorhandler(403)
    def forbidden(error):
        """Maneja errores 403 - Acceso prohibido"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Acceso prohibido"), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def page_not_found(error):
        """Maneja errores 404 - Página no encontrada"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Recurso no encontrado"), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Maneja errores 500 - Error interno del servidor"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Error interno del servidor"), 500
        return render_template('errors/500.html'), 500
