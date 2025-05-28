from datetime import datetime
import os
from typing import Dict, Any, Optional
from flask import current_app
from app.extensions import db

class Image(db.Model):
    """
    Modelo para representar una imagen en el sistema.
    Almacena la información sobre las imágenes subidas y su relación con el usuario.
    """
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # Tamaño en bytes
    mime_type = db.Column(db.String(100))
    width = db.Column(db.Integer) # Ancho de la imagen en píxeles
    height = db.Column(db.Integer) # Altura de la imagen en píxeles
    storage_type = db.Column(db.String(20), default='local')  # 'local' o 's3'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con el usuario (muchas imágenes pertenecen a un usuario)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __init__(self, filename: str, original_filename: Optional[str] = None, 
                 created_at: Optional[datetime] = None, user_id: Optional[int] = None,
                 file_size: Optional[int] = None, mime_type: Optional[str] = None,
                 width: Optional[int] = None, height: Optional[int] = None,
                 storage_type: Optional[str] = 'local'):
        self.filename = filename
        self.original_filename = original_filename or filename
        self.created_at = created_at or datetime.utcnow()
        self.user_id = user_id
        self.file_size = file_size
        self.mime_type = mime_type
        self.width = width
        self.height = height
        self.storage_type = storage_type
        
    @property
    def extension(self) -> str:
        """Obtiene la extensión del archivo"""
        return self.filename.rsplit('.', 1)[1].lower() if '.' in self.filename else ''
        
    @property
    def url(self) -> str:
        """Devuelve la URL completa según el tipo de almacenamiento"""
        if self.storage_type == 's3':
            # URL del bucket de S3
            s3_bucket_url = current_app.config.get('S3_BUCKET_URL')
            return f"{s3_bucket_url}/{self.filename}"
        else:
            # URL local usando la ruta predeterminada
            return f"/uploads/{self.filename}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a un diccionario para facilitar la serialización"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'extension': self.extension,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'user_id': self.user_id,
            'storage_type': self.storage_type,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Image':
        """Crea una instancia de Image a partir de un diccionario"""
        return cls(
            filename=data.get('filename'),
            original_filename=data.get('original_filename'),
            created_at=datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None,
            user_id=data.get('user_id'),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            width=data.get('width'),
            height=data.get('height'),
            storage_type=data.get('storage_type', 'local')
        )
        
    def __repr__(self):
        return f"<Image {self.original_filename} ({self.filename})>"
