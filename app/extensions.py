"""
Extensiones para Flask
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Crear las instancias de las extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Configuración del Login Manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

def init_extensions(app):
    """
    Inicializa todas las extensiones con la aplicación Flask
    
    Args:
        app: Instancia de la aplicación Flask
    """
    # Inicializar la base de datos
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Inicializar el gestor de login
    login_manager.init_app(app)
    
    # Inicializar protección CSRF
