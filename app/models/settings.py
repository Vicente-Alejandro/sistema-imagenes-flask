from app.extensions import db
import datetime

class AppSetting(db.Model):
    """
    Modelo para almacenar configuraciones de la aplicación en la base de datos.
    Permite guardar pares clave-valor para configuraciones dinámicas.
    """
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    is_encrypted = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    @classmethod
    def get(cls, key, default=None):
        """Obtiene un valor de configuración por su clave"""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
        
    @classmethod
    def set(cls, key, value, description=None, is_encrypted=False):
        """Establece un valor de configuración"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
            setting.is_encrypted = is_encrypted
        else:
            setting = cls(
                key=key, 
                value=value, 
                description=description,
                is_encrypted=is_encrypted
            )
            db.session.add(setting)
        db.session.commit()
        return setting
    
    def __repr__(self):
        return f'<AppSetting {self.key}>'
