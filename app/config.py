import os
import secrets
import logging
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

# Obtener host y puerto de las variables de entorno
HOST = os.environ.get('HOST', '0.0.0.0')
try:
    PORT = int(os.environ.get('PORT', 3000))
except (ValueError, TypeError):
    PORT = 3000

class Config:
    """Clase base de configuración para la aplicación"""
    # Nombre de la aplicación
    APP_NAME = os.environ.get('APP_NAME', 'Sistema de Gestión de Imágenes PITON')
    
    # En desarrollo, generar una clave aleatoria para la sesión
    # En producción, SIEMPRE usar la variable de entorno SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Solo para desarrollo - no usar en producción
        print("ADVERTENCIA: Usando una SECRET_KEY temporal. Esto no es seguro para producción.")
        SECRET_KEY = secrets.token_hex(32)
    
    # Configuración de debug
    DEBUG = os.environ.get('DEBUG', 'false').lower() in ('true', 't', '1', 'yes', 'y')
    
    # Cargar rutas y límites desde variables de entorno o usar valores predeterminados
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads')
    
    # Obtener MAX_CONTENT_LENGTH del .env o usar el valor predeterminado
    try:
        MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 48 * 1024 * 1024))  # Valor predeterminado: 48MB
    except (ValueError, TypeError):
        MAX_CONTENT_LENGTH = 48 * 1024 * 1024  # Valor predeterminado si hay un error de conversión
        
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # Configuración para conversión WebP
    try:
        WEBP_QUALITY = int(os.environ.get('WEBP_QUALITY', 85))
        if WEBP_QUALITY < 0 or WEBP_QUALITY > 100:
            WEBP_QUALITY = 85
    except (ValueError, TypeError):
        WEBP_QUALITY = 85
        
    WEBP_LOSSLESS_TRANSPARENCY = os.environ.get('WEBP_LOSSLESS_TRANSPARENCY', 'true').lower() in ('true', 't', '1', 'yes', 'y')
    
    # Configuración de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.environ.get('LOG_FILE')
    
    @classmethod
    def init_app(cls, app):
        """Inicializa la aplicación con la configuración"""
        # Configurar logging
        log_level = getattr(logging, cls.LOG_LEVEL, logging.INFO)
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        if cls.LOG_FILE:
            logging.basicConfig(filename=cls.LOG_FILE, level=log_level, format=log_format)
        else:
            logging.basicConfig(level=log_level, format=log_format)

class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo"""
    DEBUG = True
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        app.logger.info('Aplicación iniciada en modo DESARROLLO')
        
        # Mostrar advertencias de desarrollo
        if not cls.SECRET_KEY or cls.SECRET_KEY == cls.generate_dev_key():
            app.logger.warning(
                "ADVERTENCIA: Usando una SECRET_KEY temporal en desarrollo. "
                "Para mayor seguridad, configura SECRET_KEY en el archivo .env"
            )

    @staticmethod
    def generate_dev_key():
        """Genera una clave temporal para desarrollo"""
        return secrets.token_hex(32)

class TestingConfig(Config):
    """Configuración para entorno de pruebas"""
    DEBUG = False
    TESTING = True
    # Usar una carpeta temporal para las pruebas
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests', 'uploads')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        app.logger.info('Aplicación iniciada en modo PRUEBAS')

class ProductionConfig(Config):
    """Configuración para entorno de producción"""
    DEBUG = False
    TESTING = False
    
    # Verificar que exista una SECRET_KEY en producción
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        app.logger.info('Aplicación iniciada en modo PRODUCCIÓN')
        
        # Verificación de seguridad para producción
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'tu_clave_secreta_aqui':
            app.logger.error(
                "ERROR: No se ha configurado una SECRET_KEY para producción. "
                "Esto es un riesgo de seguridad. Configura SECRET_KEY en el archivo .env"
            )
            raise ValueError(
                "La SECRET_KEY no está configurada para el entorno de producción. "
                "Por favor, configura una SECRET_KEY segura en el archivo .env"
            )

# Mapa de configuraciones disponibles
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}


def get_config():
    """Obtiene la configuración adecuada basada en las variables de entorno
    
    Returns:
        object: La clase de configuración adecuada para el entorno actual
    """
    # Determinar la configuración basada en FLASK_ENV
    env = os.environ.get('FLASK_ENV', 'development').lower()
    
    # Usar la configuración correspondiente al entorno o DevelopmentConfig como fallback
    config_class = config_map.get(env, DevelopmentConfig)
    
    # Obtener el modo debug de las variables de entorno
    # Si está especificado en .env, se usa ese valor, de lo contrario se usa el valor de la clase
    debug_env = os.environ.get('DEBUG', '').lower()
    if debug_env in ('true', 't', '1', 'yes', 'y'):
        config_class.DEBUG = True
    elif debug_env in ('false', 'f', '0', 'no', 'n'):
        config_class.DEBUG = False
        
    return config_class
