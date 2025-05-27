from flask import Flask
from app.config import Config

def create_app(config_class=Config):
    """Fábrica de aplicación - patrón para crear instancias de la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar la aplicación con la configuración específica
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)
    
    # Registrar blueprints
    from app.routes.image_routes import image_bp
    app.register_blueprint(image_bp)
    
    # Asegurar que existan las carpetas necesarias
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app
