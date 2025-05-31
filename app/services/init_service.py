"""
Servicio para inicializar datos necesarios en la aplicación
"""
import os
import datetime
from typing import Dict, Any
from app.models.settings import *
from app.extensions import db


class InitService:
    """
    Servicio para inicializar datos necesarios para el funcionamiento de la aplicación
    """
    
    @staticmethod
    def init_aws_settings() -> None:
        """
        Inicializa las configuraciones de AWS en la base de datos
        si no existen previamente
        """
        try:
            # Comprobar si existen configuraciones previas
            existing_access_key = AppSetting.get('AWS_ACCESS_KEY')
            
            if existing_access_key is not None:
                # Si ya existe una configuración, no hacer nada
                return
        except Exception as e:
            # Si hay un error (como que la tabla no existe), simplemente salir
            # Esto ocurre durante la primera migración
            print(f"No se pudo verificar configuraciones AWS: {str(e)}")
            return
        
        # Obtener valores de las variables de entorno
        access_key = os.environ.get('S3_ACCESS_KEY', '')
        secret_key = os.environ.get('S3_SECRET_KEY', '')
        session_token = os.environ.get('S3_SESSION_TOKEN', '')
        region = os.environ.get('S3_REGION', 'us-east-1')
        bucket = os.environ.get('S3_BUCKET_NAME', '')
        
        # Crear configuraciones en la base de datos
        settings = [
            AppSetting(key='AWS_ACCESS_KEY', value=access_key),
            AppSetting(key='AWS_SECRET_KEY', value=secret_key),
            AppSetting(key='AWS_SESSION_TOKEN', value=session_token),
            AppSetting(key='AWS_REGION', value=region),
            AppSetting(key='AWS_BUCKET', value=bucket),
            AppSetting(key='AWS_LAST_UPDATED', value=datetime.datetime.now().isoformat())
        ]
        
        # Guardar configuraciones en la base de datos
        for setting in settings:
            db.session.add(setting)
        
        try:
            db.session.commit()
            print("Configuraciones AWS inicializadas correctamente")
        except Exception as e:
            db.session.rollback()
            print(f"Error al inicializar configuraciones AWS: {str(e)}")
