import boto3
from botocore.exceptions import ClientError
from flask import current_app
from datetime import datetime, timedelta
import os
import logging

class AWSCredentialService:
    """
    Servicio para gestionar credenciales AWS.
    Proporciona métodos para obtener clientes AWS con credenciales actualizadas
    desde la base de datos y actualizar dichas credenciales.
    """
    
    @staticmethod
    def get_s3_client():
        """
        Obtiene un cliente S3 con las credenciales actualizadas de la fuente configurada.
        Según AWS_CREDENTIALS_SOURCE, utiliza credenciales de la base de datos o del archivo .env.
        """
        logger = logging.getLogger(__name__)
        logger.info("Obteniendo cliente S3")
        
        # Determinar la fuente de credenciales
        credentials_source = current_app.config.get('AWS_CREDENTIALS_SOURCE', 'database').lower()
        logger.info(f"Fuente de credenciales: {credentials_source}")
        
        # Usar credenciales de la base de datos (comportamiento predeterminado)
        from app.models.settings import AppSetting
        
        # ENFOQUE DIRECTO: Buscar en la base de datos las credenciales con ambos prefijos
        logger.info("Buscando credenciales en la base de datos...")

        if credentials_source == 'env':
            logger.info("Usando credenciales desde variables de entorno")
            s3_access_key = current_app.config.get('S3_ACCESS_KEY')
            s3_secret_key = current_app.config.get('S3_SECRET_KEY')
            s3_session_token = current_app.config.get('S3_SESSION_TOKEN')
            s3_region = current_app.config.get('S3_REGION')
        elif credentials_source == 'database':
            # ACCESS KEY
            s3_key = AppSetting.query.filter_by(key='S3_ACCESS_KEY').first()
            if s3_key:
                logger.info(f"Encontrada S3_ACCESS_KEY en BD: {s3_key.value}")
            s3_access_key = s3_key.value
            # SECRET KEY
            s3_secret = AppSetting.query.filter_by(key='S3_SECRET_KEY').first()
            if s3_secret:
                logger.info(f"Encontrada S3_SECRET_KEY en BD: {s3_secret.value}")
                s3_secret_key = s3_secret.value
            else:
                logger.info("No se encontró ninguna secret key en BD")
                s3_secret_key = current_app.config.get('S3_SECRET_KEY')
                
            # SESSION TOKEN
            s3_token = AppSetting.query.filter_by(key='S3_SESSION_TOKEN').first()
            if s3_token:
                logger.info(f"Encontrado S3_SESSION_TOKEN en BD: {s3_token.value}")
                s3_session_token = s3_token.value
            else:
                logger.info("No se encontró ningún session token en BD")
                s3_session_token = current_app.config.get('S3_SESSION_TOKEN')
                
            # REGION
            s3_region = AppSetting.query.filter_by(key='S3_REGION').first()
            if s3_region:
                logger.info(f"Encontrada S3_REGION en BD: {s3_region.value}")
                s3_region = s3_region.value
            else:
                logger.info("No se encontró ninguna region en BD")
                s3_region = current_app.config.get('S3_REGION')
                
            # BUCKET
            s3_bucket_config = AppSetting.query.filter_by(key='S3_BUCKET_NAME').first()
            if s3_bucket_config:
                logger.info(f"Encontrado S3_BUCKET_NAME en BD: {s3_bucket_config.value}")
                s3_bucket = s3_bucket_config.value
            else:
                logger.info("No se encontró ningún bucket en BD")
                s3_bucket = current_app.config.get('S3_BUCKET_NAME')
        
        else:
            logger.info("No se encontró ninguna access key en BD")
            s3_access_key = current_app.config.get('S3_ACCESS_KEY')
            
        # Configurar cliente S3
        s3_client_args = {
            'region_name': s3_region,
            'aws_access_key_id': s3_access_key,
            'aws_secret_access_key': s3_secret_key
        }
        
        # Añadir token de sesión si existe
        if s3_session_token:
            s3_client_args['aws_session_token'] = s3_session_token
        
        logger.info("Creando cliente S3")
        # Crear y devolver cliente
        try:
            client = boto3.client('s3', **s3_client_args)
            logger.info("Cliente S3 creado exitosamente")
            return client
        except Exception as e:
            logger.error(f"Error al crear cliente S3: {str(e)}")
            logger.error(f"Argumentos utilizados: region={s3_region}, access_key={'*****' + s3_access_key[-4:] if s3_access_key else 'None'}, secret_key={'*****' if s3_secret_key else 'None'}, session_token={'Presente' if s3_session_token else 'None'}")
            # Intento de crear cliente sin credenciales explícitas (usando perfil predeterminado o roles IAM)
            logger.info("Intentando crear cliente S3 sin credenciales explícitas...")
            try:
                client = boto3.client('s3', region_name=s3_region)
                logger.info("Cliente S3 creado exitosamente con credenciales del entorno")
                return client
            except Exception as e2:
                logger.error(f"También falló al crear cliente sin credenciales explícitas: {str(e2)}")
                raise e  # Re-lanzar la excepción original
    
    @staticmethod
    def update_credentials(access_key, secret_key, session_token=None, region=None):
        """
        Actualiza las credenciales AWS en la base de datos.
        
        Args:
            access_key: Access Key ID de AWS
            secret_key: Secret Access Key de AWS
            session_token: Token de sesión (opcional, pero necesario para AWS Academy)
            region: Región de AWS (opcional)
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        from app.models.settings import AppSetting
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        AppSetting.set('S3_ACCESS_KEY', access_key, 
                      description="AWS Access Key ID. Actualizada: " + timestamp,
                      is_encrypted=True)
        
        AppSetting.set('S3_SECRET_KEY', secret_key, 
                      description="AWS Secret Access Key. Actualizada: " + timestamp,
                      is_encrypted=True)
        
        if session_token:
            AppSetting.set('S3_SESSION_TOKEN', session_token, 
                          description="AWS Session Token. Actualizado: " + timestamp,
                          is_encrypted=True)
        
        if region:
            AppSetting.set('S3_REGION', region, 
                          description="AWS Region. Actualizada: " + timestamp)
        
        return True
    
    @staticmethod
    def test_credentials():
        """
        Prueba las credenciales AWS actualmente configuradas.
        
        Returns:
            dict: Resultado de la prueba con información de estado
        """
        try:
            s3_client = AWSCredentialService.get_s3_client()
            # Intentar listar buckets (operación sencilla para verificar credenciales)
            response = s3_client.list_buckets()
            
            # Extraer nombres de buckets para el informe
            bucket_names = [bucket['Name'] for bucket in response['Buckets']]
            
            return {
                'success': True,
                'message': f'Credenciales válidas. Se encontraron {len(bucket_names)} buckets.',
                'buckets': bucket_names,
                'timestamp': datetime.utcnow().isoformat()
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            return {
                'success': False,
                'error_code': error_code,
                'message': f'Error de AWS: {error_message}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
