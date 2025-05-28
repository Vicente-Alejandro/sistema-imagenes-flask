from typing import List, Dict, Any, Optional, BinaryIO, Tuple
from app.models.image import Image
from app.services.file_service import FileServiceInterface
from app.extensions import db
from flask import current_app, g
from flask_login import current_user
import os
import tempfile
import uuid
import datetime
from PIL import Image as PILImage
import shutil
import io
import boto3
from botocore.exceptions import ClientError
import logging

class ImageServiceInterface:
    """
    Interfaz para el servicio de imágenes.
    Sigue el principio de Segregación de Interfaces (ISP).
    """
    def upload_image(self, file_data: BinaryIO, original_filename: str) -> Image:
        """Sube una imagen y devuelve el objeto Image creado"""
        pass
    
    def delete_image(self, filename: str) -> bool:
        """Elimina una imagen y devuelve True si fue exitoso"""
        pass
    
    def get_all_images(self) -> List[Image]:
        """Obtiene todas las imágenes disponibles"""
        pass
    
    def get_image(self, filename: str) -> Optional[Image]:
        """Obtiene una imagen específica por su nombre de archivo"""
        pass
        
    def convert_to_webp(self, input_file: str, output_file: str) -> bool:
        """Convierte una imagen al formato WebP preservando sus características"""
        pass

class ImageService(ImageServiceInterface):
    """
    Implementación concreta del servicio de imágenes.
    Sigue el principio de Responsabilidad Única (SRP) enfocándose solo en la lógica de negocio para imágenes.
    """
    def __init__(self, file_service: FileServiceInterface):
        """
        Inicializa el servicio con dependencias inyectadas.
        Siguiendo el principio de Inversión de Dependencias (DIP).
        """
        self.file_service = file_service
    
    def _get_current_user_id(self) -> Optional[int]:
        """
        Obtiene el ID del usuario actual si está autenticado,
        o None si es un usuario anónimo o no hay sesión.
        """
        if current_user and current_user.is_authenticated:
            return current_user.id
        return None
    
    def convert_to_webp(self, input_file: str, output_file: str) -> bool:
        """
        Convierte una imagen al formato WebP preservando sus características originales como transparencia.
        Retorna True si la conversión fue exitosa, False en caso contrario.
        """
        try:
            # Abrir la imagen original
            with PILImage.open(input_file) as img:
                # Determinar si la imagen tiene transparencia
                has_transparency = False
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    has_transparency = True
                    # Convertir a RGBA si es necesario para preservar transparencia
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                
                # Obtener configuración de WebP desde Config
                from app.config import Config
                
                # Configuración de calidad para WebP
                quality = Config.WEBP_QUALITY  # Valor de .env o predeterminado (85)
                method = 4  # 0-6, mayor número = mejor compresión pero más lento
                
                # Determinar si se usa compresión sin pérdida para transparencia
                use_lossless = has_transparency and Config.WEBP_LOSSLESS_TRANSPARENCY
                
                # Guardar como WebP
                img.save(
                    output_file, 
                    format='WEBP', 
                    quality=quality, 
                    method=method,
                    lossless=use_lossless
                )
                
                return True
        except Exception as e:
            print(f"Error al convertir a WebP: {e}")
            return False
    
    def upload_to_s3(self, local_path: str, filename: str) -> bool:
        """
        Sube un archivo a Amazon S3
        
        Args:
            local_path: Ruta local del archivo a subir
            filename: Nombre del archivo en S3
            
        Returns:
            True si la subida fue exitosa, False en caso contrario
        """
        try:
            # Configuración de S3 desde la aplicación
            s3_bucket = current_app.config.get('S3_BUCKET_NAME')
            s3_region = current_app.config.get('S3_REGION')
            s3_access_key = current_app.config.get('S3_ACCESS_KEY')
            s3_secret_key = current_app.config.get('S3_SECRET_KEY')
            
            # Crear cliente de S3
            s3_client = boto3.client(
                's3',
                region_name=s3_region,
                aws_access_key_id=s3_access_key,
                aws_secret_access_key=s3_secret_key
            )
            
            # Subir archivo a S3
            s3_client.upload_file(
                local_path, 
                s3_bucket,
                filename,
                ExtraArgs={'ContentType': 'image/webp'}
            )
            
            current_app.logger.info(f"Imagen {filename} subida con éxito a S3")
            return True
        except ClientError as e:
            current_app.logger.error(f"Error al subir a S3: {e}")
            return False
        except Exception as e:
            current_app.logger.error(f"Error inesperado al subir a S3: {e}")
            return False
            
    def upload_image(self, file_data: BinaryIO, original_filename: str, custom_name: str = None, user_id: int = None) -> Image:
        """
        Sube una imagen, la convierte a WebP y devuelve el objeto Image creado.
        Determina automáticamente si usar almacenamiento local o S3 según la configuración.
        
        Args:
            file_data: Datos del archivo subido
            original_filename: Nombre original del archivo
            custom_name: Nombre personalizado para la imagen (opcional)
            user_id: ID del usuario que sube la imagen (opcional)
        
        Returns:
            Objeto Image creado
        """
        # Obtener el ID del usuario actual si no se proporcionó
        user_id = user_id or self._get_current_user_id()
        if not user_id:
            raise ValueError("Debes iniciar sesión para subir imágenes")
            
        # Crear archivo temporal para trabajar con la imagen
        temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(original_filename)[1])
        os.close(temp_fd)
        
        # Webp temporal path que usaremos para la conversión
        webp_temp_path = None
        
        try:
            # Escribir los datos del archivo al archivo temporal
            file_data.seek(0)
            with open(temp_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)
            
            # Obtener metadatos del archivo
            # Tamaño del archivo en bytes
            file_size = os.path.getsize(temp_path)
            
            # Obtener tipo MIME y dimensiones
            try:
                with PILImage.open(temp_path) as img:
                    width, height = img.size
                    mime_type = PILImage.MIME[img.format] if img.format in PILImage.MIME else None
            except Exception as e:
                current_app.logger.error(f"Error al leer metadatos de imagen: {e}")
                width, height = None, None
                mime_type = None
            
            # Generar nombre único para el archivo
            unique_id = uuid.uuid4().hex
            # Si se proporciona un nombre personalizado, usarlo; de lo contrario, usar el nombre original
            display_filename = custom_name or os.path.basename(original_filename)
            # Extraer la extensión original para conservarla en el nuevo nombre
            timestamp = datetime.datetime.now().strftime("%d%m%y_%H%M%S")
            webp_filename = f"{unique_id}-{timestamp}.webp"
            
            # Determinar el tipo de almacenamiento basado en la configuración
            storage_type = current_app.config.get('STORAGE_TYPE', 'local')
            
            # Determinar la ruta completa del archivo WebP para conversión temporal
            webp_temp_path = os.path.join(tempfile.gettempdir(), webp_filename)
            
            # Convertir a WebP
            conversion_success = self.convert_to_webp(temp_path, webp_temp_path)
            
            if not conversion_success:
                # Si la conversión falla, usar el archivo original
                filename = f"{unique_id}-{timestamp}{os.path.splitext(original_filename)[1]}"
                mime_type = mime_type or "image/jpeg"  # Valor predeterminado
                
                if storage_type == 's3':
                    # Subir archivo original a S3
                    s3_success = self.upload_to_s3(temp_path, filename)
                    if not s3_success:
                        # Si falla la subida a S3, intentar almacenar localmente
                        file_data.seek(0)
                        filename = self.file_service.save_file(file_data, original_filename)
                        storage_type = 'local'
                else:
                    # Almacenamiento local
                    file_data.seek(0)
                    filename = self.file_service.save_file(file_data, original_filename)
            else:
                # Conversión exitosa a WebP
                filename = webp_filename
                mime_type = "image/webp"
                
                if storage_type == 's3':
                    # Subir archivo WebP a S3
                    s3_success = self.upload_to_s3(webp_temp_path, filename)
                    if not s3_success:
                        # Si falla la subida a S3, intentar almacenar localmente
                        storage_type = 'local'
                        # Copiar a la carpeta de uploads local
                        webp_local_path = os.path.join(self.file_service.upload_folder, webp_filename)
                        shutil.copy2(webp_temp_path, webp_local_path)
                        file_size = os.path.getsize(webp_local_path)
                    else:
                        # Actualizar tamaño para archivo WebP
                        file_size = os.path.getsize(webp_temp_path)
                else:
                    # Almacenamiento local
                    webp_local_path = os.path.join(self.file_service.upload_folder, webp_filename)
                    shutil.copy2(webp_temp_path, webp_local_path)
                    file_size = os.path.getsize(webp_local_path)
            
            # Crear y guardar metadatos en la base de datos
            image = Image(
                filename=filename,
                original_filename=display_filename,
                user_id=user_id,
                file_size=file_size,
                mime_type=mime_type,
                width=width,
                height=height,
                storage_type=storage_type
            )
            
            # Guardar en la base de datos
            db.session.add(image)
            db.session.commit()
            
            return image
            
        finally:
            # Eliminar archivos temporales
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if 'webp_temp_path' in locals() and os.path.exists(webp_temp_path):
                os.unlink(webp_temp_path)
    
    def delete_image(self, filename: str) -> bool:
        """
        Elimina una imagen y sus metadatos.
        Maneja la eliminación tanto en almacenamiento local como en S3.
        
        Si el usuario actual no es el dueño de la imagen o un administrador, no se permitirá la eliminación.
        
        Args:
            filename: Nombre del archivo a eliminar
            
        Returns:
            True si la imagen fue eliminada correctamente, False en caso contrario
        """
        # Buscar la imagen en la base de datos
        image = Image.query.filter_by(filename=filename).first()
        
        if not image:
            return False
            
        # Verificar permisos
        user_id = self._get_current_user_id()
        if not user_id:
            return False
            
        # Verificar si el usuario puede eliminar la imagen
        from app.models.user import Role
        user = g.get('user', None) or current_user
        if not (user.has_role(Role.MODERATOR) or user.id == image.user_id):
            return False
        
        # Eliminar según el tipo de almacenamiento
        success = False
        if image.storage_type == 's3':
            # Implementar eliminación de S3
            try:
                # Configuración de S3 desde la aplicación
                s3_bucket = current_app.config.get('S3_BUCKET_NAME')
                s3_region = current_app.config.get('S3_REGION')
                s3_access_key = current_app.config.get('S3_ACCESS_KEY')
                s3_secret_key = current_app.config.get('S3_SECRET_KEY')
                
                # Crear cliente de S3
                s3_client = boto3.client(
                    's3',
                    region_name=s3_region,
                    aws_access_key_id=s3_access_key,
                    aws_secret_access_key=s3_secret_key
                )
                
                # Eliminar archivo de S3
                s3_client.delete_object(Bucket=s3_bucket, Key=image.filename)
                current_app.logger.info(f"Imagen {filename} eliminada de S3")
                success = True
            except Exception as e:
                current_app.logger.error(f"Error al eliminar de S3: {e}")
                success = False
        else:
            # Eliminar archivo local
            success = self.file_service.delete_file(filename)
        
        if success:
            # Eliminar de la base de datos
            db.session.delete(image)
            db.session.commit()
            return True
        
        return False
    
    def get_all_images(self) -> List[Image]:
        """
        Obtiene todas las imágenes disponibles.
        
        Returns:
            Lista de objetos Image ordenados por fecha de creación (más reciente primero)
        """
        # Obtener desde la base de datos ordenando por fecha de creación (más reciente primero)
        return Image.query.order_by(Image.created_at.desc()).all()
    
    def get_image(self, filename: str) -> Optional[Image]:
        """Obtiene una imagen específica por su nombre de archivo"""
        return Image.query.filter_by(filename=filename).first()
        
    def update_image_name(self, filename: str, new_original_filename: str) -> Optional[Image]:
        """Actualiza el nombre original de una imagen existente"""
        # Buscar la imagen en la base de datos
        image = Image.query.filter_by(filename=filename).first()
        
        if not image:
            return None
            
        # Verificar permisos
        user_id = self._get_current_user_id()
        if not user_id:
            return None
            
        # Verificar si el usuario puede editar la imagen
        from app.models.user import Role
        user = g.get('user', None) or current_user
        if not user.can_edit_image(image):
            return None
        
        # Actualizar el nombre
        image.original_filename = new_original_filename
        image.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return image
