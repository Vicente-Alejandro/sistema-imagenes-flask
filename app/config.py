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
    
# Configuración de base de datos
DB_CONNECTION = os.environ.get('DB_CONNECTION', 'sqlite').lower()
DB_DRIVER = os.environ.get('DB_DRIVER', 'mysqlclient').lower()
DB_USE_SSL = os.environ.get('DB_USE_SSL', 'false').lower() in ('true', 't', '1', 'yes', 'y')
DB_VERIFY_SSL = os.environ.get('DB_VERIFY_SSL', 'true').lower() in ('true', 't', '1', 'yes', 'y')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', 3306)
DB_DATABASE = os.environ.get('DB_DATABASE', 'piton')
DB_USERNAME = os.environ.get('DB_USERNAME', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

class Config:
    """Clase base de configuración para la aplicación"""
    # Nombre de la aplicación
    APP_NAME = os.environ.get('APP_NAME', 'Sistema de Gestión de Imágenes PITON')
    
    # Configuración de almacenamiento
    STORAGE_TYPE = os.environ.get('STORAGE_TYPE', 'local')
    
    # Carpeta para archivos subidos (para almacenamiento local)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads')
    
    # Extensiones permitidas para archivos
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # Configuración de Amazon S3
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_BUCKET_URL = os.environ.get('S3_BUCKET_URL')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
    S3_SESSION_TOKEN = os.environ.get('S3_SESSION_TOKEN')  # Añadido para AWS Academy
    S3_REGION = os.environ.get('S3_REGION', 'us-east-1')
    
    # Fuente de las credenciales AWS: 'database' o 'env'
    AWS_CREDENTIALS_SOURCE = os.environ.get('AWS_CREDENTIALS_SOURCE', 'database')
    
    # En desarrollo, generar una clave aleatoria para la sesión
    # En producción, SIEMPRE usar la variable de entorno SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Configuración de debug
    DEBUG = os.environ.get('DEBUG', 'false').lower() in ('true', 't', '1', 'yes', 'y')
    
    # Configuración para conversión WebP
    try:
        WEBP_QUALITY = int(os.environ.get('WEBP_QUALITY', 85))
        if WEBP_QUALITY < 0 or WEBP_QUALITY > 100:
            WEBP_QUALITY = 85
    except (ValueError, TypeError):
        WEBP_QUALITY = 85
        
    WEBP_LOSSLESS_TRANSPARENCY = os.environ.get('WEBP_LOSSLESS_TRANSPARENCY', 'true').lower() in ('true', 't', '1', 'yes', 'y')
    
    # Configuración de la base de datos
    # Configurando la URL de la base de datos según el tipo de conexión
    if DB_CONNECTION == 'sqlite':
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, DB_DATABASE + ".db")}'
    elif DB_CONNECTION in ['mysql', 'mariadb']:
        # Construir la cadena de conexión según las configuraciones
        driver_string = ''
        if DB_DRIVER in ['pymysql', 'mysqlclient']:
            # Si se especificó pymysql, usarlo como driver
            if DB_DRIVER == 'pymysql':
                driver_string = '+pymysql'
            
            # Construir URL base
            url = f'{DB_CONNECTION}{driver_string}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
            
            # Añadir parámetros SSL si es necesario
            if DB_USE_SSL:
                if DB_DRIVER == 'pymysql':
                    # Parámetros para PyMySQL
                    url += f'?ssl=True&ssl_verify_identity={"True" if DB_VERIFY_SSL else "False"}'
                else:
                    # Parámetros para mysqlclient
                    url += f'?ssl_mode={"VERIFY_IDENTITY" if DB_VERIFY_SSL else "REQUIRED"}'
            
            SQLALCHEMY_DATABASE_URI = url
        else:
            # Si no se especifica un driver válido, usar la configuración por defecto
            SQLALCHEMY_DATABASE_URI = f'{DB_CONNECTION}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
    else:
        # Valor predeterminado es SQLite si no se especifica un tipo de conexión válido
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "piton.db")}'
        
    # Otras configuraciones de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
        # Sin argumentos de conexión adicionales
    }
    
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
