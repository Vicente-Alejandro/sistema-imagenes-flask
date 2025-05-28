"""
Modelo de usuario para la aplicación
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

class Role:
    """Constantes para roles de usuario con sus niveles de acceso"""
    PENDING = 0       # Usuario sin cuenta
    VISITOR = 5       # Usuario básico
    JANITOR = 10      # Puede gestionar algunas cosas
    MODERATOR = 15    # Puede moderar contenido
    ADMINISTRATOR = 30 # Control total

    # Mapeo de nombres a niveles para facilitar la conversión
    ROLE_NAMES = {
        'PENDING': PENDING,
        'VISITOR': VISITOR,
        'JANITOR': JANITOR,
        'MODERATOR': MODERATOR,
        'ADMINISTRATOR': ADMINISTRATOR
    }
    
    # Mapeo inverso de niveles a nombres
    ROLE_LEVELS = {
        PENDING: 'PENDING',
        VISITOR: 'VISITOR',
        JANITOR: 'JANITOR',
        MODERATOR: 'MODERATOR',
        ADMINISTRATOR: 'ADMINISTRATOR'
    }

class User(UserMixin, db.Model):
    """Modelo de usuario para la aplicación"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con las imágenes (un usuario tiene muchas imágenes)
    images = db.relationship('Image', backref='owner', lazy='dynamic')
    
    @property
    def role_level(self):
        """Obtener el nivel numérico del rol del usuario"""
        return Role.ROLE_NAMES.get(self.role, Role.PENDING)
    
    @property
    def password(self):
        """Prevenir acceso a la contraseña hasheada"""
        raise AttributeError('La contraseña no es un atributo legible')
    
    @password.setter
    def password(self, password):
        """Hashear y guardar la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Verificar si la contraseña es correcta"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_level):
        """Verificar si el usuario tiene un rol de nivel suficiente"""
        if isinstance(role_level, str):
            role_level = Role.ROLE_NAMES.get(role_level, Role.PENDING)
        return self.role_level >= role_level
    
    def can_edit_image(self, image):
        """Verificar si el usuario puede editar una imagen"""
        # El administrador puede editar cualquier imagen
        if self.has_role(Role.ADMINISTRATOR):
            return True
        # Moderadores pueden editar cualquier imagen
        if self.has_role(Role.MODERATOR):
            return True
        # Los usuarios normales solo pueden editar sus propias imágenes
        return image.user_id == self.id
    
    def is_administrator(self):
        """Verificar si el usuario es administrador"""
        return self.has_role(Role.ADMINISTRATOR)
    
    def __repr__(self):
        return f"<User {self.name} ({self.email})>"

@login_manager.user_loader
def load_user(user_id):
    """Función requerida por Flask-Login para cargar un usuario desde la base de datos"""
    return User.query.get(int(user_id))
