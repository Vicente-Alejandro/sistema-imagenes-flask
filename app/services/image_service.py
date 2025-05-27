from typing import List, Dict, Any, Optional, BinaryIO, Tuple
from app.models.image import Image
from app.services.file_service import FileServiceInterface
import os
import json
import tempfile
from PIL import Image as PILImage
import shutil
import io

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
        # Guardar el archivo de metadatos dentro de la carpeta app
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._metadata_file = os.path.join(app_dir, 'image_metadata.json')
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Carga los metadatos de las imágenes desde el archivo JSON"""
        self._metadata = {}
        if os.path.exists(self._metadata_file):
            try:
                with open(self._metadata_file, 'r') as f:
                    data = json.load(f)
                    for filename, img_data in data.items():
                        self._metadata[filename] = Image.from_dict(img_data)
            except Exception as e:
                print(f"Error cargando metadatos: {e}")
    
    def _save_metadata(self) -> None:
        """Guarda los metadatos de las imágenes en el archivo JSON"""
        try:
            data = {filename: img.to_dict() for filename, img in self._metadata.items()}
            with open(self._metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error guardando metadatos: {e}")
    
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
    
    def upload_image(self, file_data: BinaryIO, original_filename: str) -> Image:
        """
        Sube una imagen, la convierte a WebP y devuelve el objeto Image creado.
        Delega el almacenamiento real al file_service.
        """
        # Crear un archivo temporal para la imagen original
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Guardar el archivo original temporalmente
            file_data.seek(0)
            temp_file.write(file_data.read())
            temp_file.flush()
            temp_path = temp_file.name
        
        try:
            # Generar nombre único para la imagen WebP
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            base_filename = self.file_service.generate_unique_filename(original_filename)
            base_filename_without_ext = base_filename.rsplit('.', 1)[0] if '.' in base_filename else base_filename
            webp_filename = f"{base_filename_without_ext}.webp"
            
            # Ruta completa para el archivo WebP
            webp_path = os.path.join(self.file_service.upload_folder, webp_filename)
            
            # Convertir a WebP
            conversion_success = self.convert_to_webp(temp_path, webp_path)
            
            if not conversion_success:
                # Si la conversión falla, usar el archivo original
                file_data.seek(0)  # Reiniciar el puntero del archivo
                filename = self.file_service.save_file(file_data, original_filename)
            else:
                filename = webp_filename
            
            # Crear y guardar metadatos
            image = Image(filename=filename, original_filename=original_filename)
            self._metadata[filename] = image
            self._save_metadata()
            
            return image
        finally:
            # Eliminar el archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def delete_image(self, filename: str) -> bool:
        """
        Elimina una imagen y sus metadatos.
        Delega la eliminación del archivo al file_service.
        """
        # Eliminar archivo
        if self.file_service.delete_file(filename):
            # Eliminar metadatos
            if filename in self._metadata:
                del self._metadata[filename]
                self._save_metadata()
            return True
        return False
    
    def get_all_images(self) -> List[Image]:
        """
        Obtiene todas las imágenes disponibles.
        Sincroniza los metadatos con los archivos reales.
        """
        # Obtener archivos existentes
        existing_files = set(self.file_service.list_files())
        
        # Sincronizar metadatos (eliminar los que ya no existen)
        for filename in list(self._metadata.keys()):
            if filename not in existing_files:
                del self._metadata[filename]
        
        # Crear metadatos para archivos sin ellos
        for filename in existing_files:
            if filename not in self._metadata:
                self._metadata[filename] = Image(filename=filename)
        
        # Guardar cambios si hubo sincronización
        self._save_metadata()
        
        # Devolver lista ordenada por fecha de creación (más reciente primero)
        return sorted(
            self._metadata.values(),
            key=lambda img: img.created_at,
            reverse=True
        )
    
    def get_image(self, filename: str) -> Optional[Image]:
        """Obtiene una imagen específica por su nombre de archivo"""
        return self._metadata.get(filename)
