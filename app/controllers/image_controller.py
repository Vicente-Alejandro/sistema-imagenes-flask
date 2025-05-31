from typing import List, Dict, Any, Tuple
from flask import request, jsonify, current_app, send_from_directory, flash, redirect, url_for, Response
from werkzeug.datastructures import FileStorage
from flask_login import current_user, login_required
from app.extensions import db
from app.services.image_service import ImageServiceInterface
from app.models.image import Image
from app.models.user import Role

class ImageController:
    """
    Controlador para manejar las operaciones relacionadas con imágenes.
    Sigue el principio de Responsabilidad Única (SRP) enfocándose solo en coordinar solicitudes HTTP.
    """
    def __init__(self, image_service: ImageServiceInterface):
        """
        Inicializa el controlador con dependencias inyectadas.
        Siguiendo el principio de Inversión de Dependencias (DIP).
        """
        self.image_service = image_service
    
    def index(self) -> Tuple[str, int]:
        """
        Controlador para la página principal.
        Obtiene todas las imágenes y las pasa a la plantilla.
        """
        images = self.image_service.get_all_images()
        return {'images': images}, 200
    
    def upload_images(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para subir imágenes.
        Procesa archivos cargados y los guarda utilizando el servicio de imágenes.
        Requiere autenticación.
        """
        # Verificar si el usuario está autenticado
        if not current_user.is_authenticated:
            return {'success': False, 'message': 'Debes iniciar sesión para subir imágenes', 'redirect': url_for('auth.login')}, 401
        
        if 'files' not in request.files:
            return {'success': False, 'message': 'No se seleccionaron archivos'}, 400
        
        files = request.files.getlist('files')
        custom_names = request.form.getlist('names[]') if 'names[]' in request.form else []
        uploaded_count = 0
        uploaded_files = []
        
        for i, file in enumerate(files):
            if file.filename == '':
                continue
            
            # Obtener nombre personalizado si está disponible
            custom_name = custom_names[i] if i < len(custom_names) and custom_names[i].strip() else None
                
            try:
                image = self.image_service.upload_image(file, file.filename, custom_name)
                uploaded_count += 1
                uploaded_files.append(image.filename)
            except Exception as e:
                current_app.logger.error(f"Error al subir archivo {file.filename}: {e}")
        
        if uploaded_count > 0:
            flash(f'Se subieron {uploaded_count} imagen(es) exitosamente', 'success')
            return {
                'success': True, 
                'message': f'Se subieron {uploaded_count} imagen(es) exitosamente',
                'files': uploaded_files
            }, 200
        else:
            flash('No se pudieron subir las imágenes', 'error')
            return {'success': False, 'message': 'No se pudieron subir las imágenes'}, 400
    
    def serve_image(self, filename: str) -> Any:
        """
        Controlador para servir una imagen específica.
        Maneja tanto almacenamiento local como S3.
        
        Si la imagen es local, la sirve directamente desde el directorio de archivos.
        Si la imagen está en S3, la recupera de S3 y la sirve como proxy para evitar problemas CORS.
        """
        # Buscar la imagen en la base de datos
        image = Image.query.filter_by(filename=filename).first()
        
        if not image:
            return {'error': 'Imagen no encontrada'}, 404
        
        # Si está en S3, servir como proxy (evita problemas CORS)
        if image.storage_type == 's3':
            try:
                import boto3
                from botocore.exceptions import ClientError
                
                # Configuración de S3
                s3_bucket = current_app.config.get('S3_BUCKET_NAME')
                s3_region = current_app.config.get('S3_REGION')
                s3_access_key = current_app.config.get('S3_ACCESS_KEY')
                s3_secret_key = current_app.config.get('S3_SECRET_KEY')
                s3_session_token = current_app.config.get('S3_SESSION_TOKEN')
                
                # Crear cliente S3
                s3_client_args = {
                    'region_name': s3_region,
                    'aws_access_key_id': s3_access_key,
                    'aws_secret_access_key': s3_secret_key
                }
                
                # Añadir token de sesión si existe (necesario para AWS Academy)
                if s3_session_token:
                    s3_client_args['aws_session_token'] = s3_session_token
                
                # Crear cliente S3
                s3_client = boto3.client('s3', **s3_client_args)
                
                # Obtener el objeto de S3
                response = s3_client.get_object(Bucket=s3_bucket, Key=filename)
                
                # Devolver el contenido como respuesta
                return Response(
                    response['Body'].read(),
                    mimetype='image/webp',  # Asumiendo que todas son WebP como indicas en tu configuración
                    headers={
                        "Content-Disposition": f"inline; filename={filename}",
                        "Cache-Control": "max-age=86400"  # Cache por 24 horas
                    }
                )
            except ClientError as e:
                current_app.logger.error(f"Error al obtener imagen de S3: {e}")
                return {'error': 'No se pudo recuperar la imagen'}, 500
            except Exception as e:
                current_app.logger.error(f"Error inesperado al obtener imagen de S3: {e}")
                return {'error': 'Error interno al procesar la imagen'}, 500
        
        # Si es local, servir el archivo directamente
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    
    def delete_image(self, filename: str) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para eliminar una imagen.
        Llama al servicio de imágenes para eliminar el archivo.
        Verifica que el usuario tenga permisos para eliminar la imagen.
        """
        # Verificar si el usuario está autenticado
        if not current_user.is_authenticated:
            return {'success': False, 'message': 'Debes iniciar sesión para eliminar imágenes', 'redirect': url_for('auth.login')}, 401
            
        # Verificar la imagen y los permisos
        image = Image.query.filter_by(filename=filename).first()
        if not image:
            return {'success': False, 'message': 'La imagen no existe'}, 404
            
        # Solo el propietario, moderadores y administradores pueden eliminar imágenes
        if not (current_user.has_role(Role.MODERATOR) or image.user_id == current_user.id):
            return {'success': False, 'message': 'No tienes permiso para eliminar esta imagen'}, 403
        
        try:
            if self.image_service.delete_image(filename):
                flash('Imagen eliminada correctamente', 'success')
                return {'success': True, 'message': 'Imagen eliminada correctamente'}, 200
            else:
                flash('No se pudo eliminar la imagen', 'error')
                return {'success': False, 'message': 'No se pudo eliminar la imagen'}, 404
        except Exception as e:
            current_app.logger.error(f"Error eliminando archivo {filename}: {e}")
            flash(f'Error al eliminar la imagen: {str(e)}', 'error')
            return {'success': False, 'message': f'Error eliminando archivo: {str(e)}'}, 500
            
    def update_image_name(self, filename: str) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para actualizar el nombre de una imagen.
        Toma el nuevo nombre del formulario y actualiza los metadatos.
        Verifica que el usuario tenga permisos para editar la imagen.
        """
        # Verificar si el usuario está autenticado
        if not current_user.is_authenticated:
            return {'success': False, 'message': 'Debes iniciar sesión para editar imágenes', 'redirect': url_for('auth.login')}, 401
            
        # Verificar la imagen y los permisos
        image = Image.query.filter_by(filename=filename).first()
        if not image:
            return {'success': False, 'message': 'La imagen no existe'}, 404
            
        # Verificar si el usuario puede editar esta imagen
        if not current_user.can_edit_image(image):
            return {'success': False, 'message': 'No tienes permiso para editar esta imagen'}, 403
            
        try:
            data = request.get_json()
            if not data or 'new_name' not in data:
                return {'success': False, 'message': 'No se proporcionó un nuevo nombre'}, 400
                
            new_name = data['new_name']
            if not new_name or len(new_name.strip()) == 0:
                return {'success': False, 'message': 'El nombre no puede estar vacío'}, 400
                
            updated_image = self.image_service.update_image_name(filename, new_name)
            if updated_image:
                flash('Nombre de imagen actualizado correctamente', 'success')
                return {
                    'success': True, 
                    'message': 'Nombre de imagen actualizado correctamente',
                    'image': updated_image.to_dict()
                }, 200
            else:
                flash('No se encontró la imagen', 'error')
                return {'success': False, 'message': 'No se encontró la imagen'}, 404
        except Exception as e:
            current_app.logger.error(f"Error actualizando nombre de imagen {filename}: {e}")
            flash(f'Error al actualizar el nombre: {str(e)}', 'error')
            return {'success': False, 'message': f'Error actualizando nombre: {str(e)}'}, 500
