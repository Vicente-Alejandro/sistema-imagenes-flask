from typing import List, Dict, Any, Tuple
from flask import request, jsonify, current_app, send_from_directory
from werkzeug.datastructures import FileStorage
from app.services.image_service import ImageServiceInterface
from app.models.image import Image

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
        """
        if 'files' not in request.files:
            return {'success': False, 'message': 'No se seleccionaron archivos'}, 400
        
        files = request.files.getlist('files')
        uploaded_count = 0
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            try:
                image = self.image_service.upload_image(file, file.filename)
                uploaded_count += 1
                uploaded_files.append(image.filename)
            except Exception as e:
                current_app.logger.error(f"Error al subir archivo {file.filename}: {e}")
        
        if uploaded_count > 0:
            return {
                'success': True, 
                'message': f'Se subieron {uploaded_count} imagen(es) exitosamente',
                'files': uploaded_files
            }, 200
        else:
            return {'success': False, 'message': 'No se pudieron subir las imágenes'}, 400
    
    def serve_image(self, filename: str) -> Any:
        """
        Controlador para servir una imagen específica.
        Utiliza el directorio de carga configurado.
        """
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    
    def delete_image(self, filename: str) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para eliminar una imagen.
        Llama al servicio de imágenes para eliminar el archivo.
        """
        try:
            if self.image_service.delete_image(filename):
                return {'success': True, 'message': 'Imagen eliminada correctamente'}, 200
            else:
                return {'success': False, 'message': 'No se pudo eliminar la imagen'}, 404
        except Exception as e:
            current_app.logger.error(f"Error eliminando archivo {filename}: {e}")
            return {'success': False, 'message': f'Error eliminando archivo: {str(e)}'}, 500
