"""
Formularios para el panel de administración
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models.user import User, Role

class UserEditForm(FlaskForm):
    """Formulario para editar información de usuarios"""
    name = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(min=2, max=100, message="El nombre debe tener entre 2 y 100 caracteres")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Por favor, introduce un email válido"),
        Length(max=120, message="El email no puede tener más de 120 caracteres")
    ])
    role = SelectField('Rol', choices=[
        ('PENDING', 'Pendiente (0)'),
        ('VISITOR', 'Visitante (5)'),
        ('JANITOR', 'Conserje (10)'),
        ('MODERATOR', 'Moderador (15)'),
        ('ADMINISTRATOR', 'Administrador (30)')
    ])
    submit = SubmitField('Guardar Cambios')

    def __init__(self, original_email=None, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, field):
        """Valida que el email no exista ya en la base de datos (excepto si es el mismo usuario)"""
        if field.data != self.original_email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Este email ya está en uso. Por favor, utiliza otro.')

class ImageFilterForm(FlaskForm):
    """Formulario para filtrar imágenes en el panel de administración"""
    user = SelectField('Usuario', coerce=int, validators=[])
    submit = SubmitField('Filtrar')
