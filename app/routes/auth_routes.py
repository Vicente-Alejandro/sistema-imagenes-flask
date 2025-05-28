"""
Rutas para autenticación de usuarios
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth_forms import LoginForm, RegistrationForm, PasswordChangeForm
from app.models.user import User, Role
from app.extensions import db

# Crear blueprint para rutas de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Vista para inicio de sesión"""
    # Redirigir si el usuario ya está autenticado
    if current_user.is_authenticated:
        return redirect(url_for('image.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next_page = request.args.get('next')
            # Solo seguir la redirección si la URL es segura (relativa)
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('image.index'))
        flash('Email o contraseña incorrectos.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Vista para registro de usuarios"""
    # Redirigir si el usuario ya está autenticado
    if current_user.is_authenticated:
        return redirect(url_for('image.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            role='VISITOR',  # Rol predeterminado para nuevos usuarios
        )
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Vista para cierre de sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('image.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Vista para el perfil de usuario"""
    user_images = current_user.images.order_by(db.desc('created_at')).all()
    return render_template('auth/profile.html', user=current_user, user_images=user_images)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Vista para cambio de contraseña"""
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.current_password.data):
            current_user.password = form.new_password.data
            db.session.commit()
            flash('Tu contraseña ha sido actualizada.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('La contraseña actual es incorrecta.', 'error')
    
    return render_template('auth/change_password.html', form=form)
