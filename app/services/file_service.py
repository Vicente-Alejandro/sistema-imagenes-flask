from abc import ABC, abstractmethod
from typing import List, Optional, BinaryIO, Tuple, Dict, Any
import os
import uuid
import imghdr
import re
from PIL import Image as PILImage
from werkzeug.utils import secure_filename
from app.config import Config

# Intentar importar magic, pero hacerlo opcional
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("WARNING: python-magic no está disponible. Se usará validación básica de imágenes.")

class FileServiceInterface(ABC):
    """
    Interfaz para el servicio de manejo de archivos.
    Siguiendo el principio de Segregación de Interfaces (ISP).
    """
    @abstractmethod
    def save_file(self, file_data: BinaryIO, original_filename: str) -> str:
        """Guarda un archivo y devuelve el nombre del archivo guardado"""
        pass
    
    @abstractmethod
    def delete_file(self, filename: str) -> bool:
        """Elimina un archivo y devuelve True si fue exitoso"""
        pass
    
    @abstractmethod
    def get_file_path(self, filename: str) -> str:
        """Obtiene la ruta completa de un archivo"""
        pass
    
    @abstractmethod
    def list_files(self) -> List[str]:
        """Lista todos los archivos disponibles"""
        pass
    
    @abstractmethod
    def is_allowed_file(self, filename: str) -> bool:
        """Verifica si el archivo tiene una extensión permitida"""
        pass
        
    @abstractmethod
    def validate_image(self, file_data: BinaryIO) -> Tuple[bool, str]:
        """Valida que el archivo sea una imagen válida y segura"""
        pass

class FileService(FileServiceInterface):
    """
    Implementación concreta del servicio de archivos.
    Sigue el principio de Responsabilidad Única (SRP) enfocándose solo en el manejo de archivos.
    """
    def __init__(self, upload_folder: str = None, allowed_extensions: set = None):
        """
        Inicializa el servicio con configuraciones personalizables.
        Siguiendo el principio de Inversión de Dependencias (DIP).
        """
        self.upload_folder = upload_folder or Config.UPLOAD_FOLDER
        self.allowed_extensions = allowed_extensions or Config.ALLOWED_EXTENSIONS
        
        # Asegurar que la carpeta de subidas exista
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Verifica si el archivo tiene una extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def validate_image(self, file_data: BinaryIO) -> Tuple[bool, str]:
        """Valida que el archivo sea una imagen válida y segura"""
        # Guardar posición actual del puntero
        current_pos = file_data.tell()
        
        try:
            # Leer los primeros bytes para identificar el tipo de archivo
            file_data.seek(0)
            header = file_data.read(2048)
            file_data.seek(0)
            
            # Verificar tipo MIME, usando magic si está disponible o imghdr si no
            if MAGIC_AVAILABLE:
                mime = magic.Magic(mime=True)
                mime_type = mime.from_buffer(header)
                
                if not mime_type.startswith('image/'):
                    return False, f"El archivo no es una imagen válida. Tipo detectado: {mime_type}"
            else:
                # Alternativa usando imghdr (menos preciso pero viene con Python)
                file_data.seek(0)
                img_type = imghdr.what(None, h=header)
                if not img_type:
                    return False, "El archivo no parece ser una imagen válida."
            
            # Validar con PIL para verificar que la imagen se puede abrir
            try:
                with PILImage.open(file_data) as img:
                    # Verificar dimensiones razonables
                    width, height = img.size
                    if width <= 0 or height <= 0 or width > 10000 or height > 10000:
                        return False, f"Dimensiones de imagen no válidas: {width}x{height}"
                    
                    # Verificar que no tenga contenido malicioso (validación básica)
                    if 'comment' in img.info and len(img.info['comment']) > 1000:
                        return False, "La imagen contiene metadata sospechosa"
            except Exception as e:
                return False, f"Error al procesar la imagen: {str(e)}"
                
            # Volver a la posición original del puntero
            file_data.seek(0)
            
            return True, "La imagen es válida"
            
        except Exception as e:
            return False, f"Error validando imagen: {str(e)}"
        finally:
            # Restaurar posición del puntero en cualquier caso
            file_data.seek(current_pos)
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Genera un nombre único para el archivo basado en UUID"""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        return f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    
    def save_file(self, file_data: BinaryIO, original_filename: str) -> str:
        """
        Guarda un archivo y devuelve el nombre del archivo guardado.
        Maneja el almacenamiento seguro de archivos.
        """
        # Validar extensión de archivo
        if not self.is_allowed_file(original_filename):
            raise ValueError(f"Tipo de archivo no permitido: {original_filename}")
        
        # Validar que sea una imagen válida y segura
        is_valid, message = self.validate_image(file_data)
        if not is_valid:
            raise ValueError(message)
        
        # Generar nombre único para evitar conflictos
        filename = self.generate_unique_filename(original_filename)
        
        # Guardar archivo
        filepath = os.path.join(self.upload_folder, filename)
        file_data.save(filepath)
        
        return filename
    
    def delete_file(self, filename: str) -> bool:
        """Elimina un archivo y devuelve True si fue exitoso"""
        filepath = self.get_file_path(filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error eliminando archivo {filename}: {e}")
            return False
    
    def get_file_path(self, filename: str) -> str:
        """Obtiene la ruta completa de un archivo"""
        return os.path.join(self.upload_folder, filename)
    
    def list_files(self) -> List[str]:
        """Lista todos los archivos disponibles"""
        if not os.path.exists(self.upload_folder):
            return []
        
        return [
            filename for filename in os.listdir(self.upload_folder)
            if self.is_allowed_file(filename)
        ]
