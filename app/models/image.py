from datetime import datetime
import os
from typing import Dict, Any, Optional

class Image:
    """
    Modelo para representar una imagen en el sistema.
    Sigue el principio de Responsabilidad Única (SRP) al encargarse solo de los datos de la imagen.
    """
    def __init__(self, filename: str, original_filename: Optional[str] = None, 
                 created_at: Optional[datetime] = None):
        self.filename = filename
        self.original_filename = original_filename or filename
        self.created_at = created_at or datetime.now()
        
    @property
    def extension(self) -> str:
        """Obtiene la extensión del archivo"""
        return self.filename.rsplit('.', 1)[1].lower() if '.' in self.filename else ''
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a un diccionario para facilitar la serialización"""
        return {
            'filename': self.filename,
            'original_filename': self.original_filename,
            'extension': self.extension,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Image':
        """Crea una instancia de Image a partir de un diccionario"""
        created_at = datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None
        return cls(
            filename=data.get('filename'),
            original_filename=data.get('original_filename'),
            created_at=created_at
        )
