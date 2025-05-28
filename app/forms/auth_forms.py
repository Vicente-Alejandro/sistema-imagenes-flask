"""
Formularios para la autenticación de usuarios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """Formulario para iniciar sesión"""
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Por favor, introduce un email válido")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria")
    ])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    """Formulario para registrar un nuevo usuario"""
    name = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(min=2, max=100, message="El nombre debe tener entre 2 y 100 caracteres")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Por favor, introduce un email válido"),
        Length(max=120, message="El email no puede tener más de 120 caracteres")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria"),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)', message="La contraseña debe contener al menos una letra y un número")
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message="La confirmación de contraseña es obligatoria"),
        EqualTo('password', message="Las contraseñas deben coincidir")
    ])
    submit = SubmitField('Registrarse')

    def validate_email(self, field):
        """Valida que el email no exista ya en la base de datos"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Este email ya está en uso. Por favor, utiliza otro o inicia sesión.')

class PasswordChangeForm(FlaskForm):
    """Formulario para cambiar la contraseña"""
    current_password = PasswordField('Contraseña Actual', validators=[
        DataRequired(message="La contraseña actual es obligatoria")
    ])
    new_password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(message="La nueva contraseña es obligatoria"),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)', message="La contraseña debe contener al menos una letra y un número")
    ])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[
        DataRequired(message="La confirmación de contraseña es obligatoria"),
        EqualTo('new_password', message="Las contraseñas deben coincidir")
    ])
    submit = SubmitField('Cambiar Contraseña')
