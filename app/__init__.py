from flask import Flask
from app.config import Config
from app.extensions import init_extensions

def create_app(config_class=Config):
    """Fábrica de aplicación - patrón para crear instancias de la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar la aplicación con la configuración específica
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)
    
    # Inicializar extensiones (SQLAlchemy, Migrate, Flask-Login)
    init_extensions(app)
    
    # Registrar blueprints
    from app.routes.image_routes import image_bp
    app.register_blueprint(image_bp)
    
    # Registrar blueprint de autenticación
    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # Registrar blueprint del panel de administración
    from app.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    
    # Asegurar que existan las carpetas necesarias
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Registrar error handlers
    from app.routes.errors import register_error_handlers
    register_error_handlers(app)
    
    # Registrar filtros y funciones globales para Jinja2
    from app.utils.template_filters import init_template_filters
    init_template_filters(app)
    
    # Inicializar configuraciones de AWS si no existen
    with app.app_context():
        from app.services.init_service import InitService
        InitService.init_aws_settings()
    
    return app
