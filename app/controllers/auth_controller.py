"""
Controlador para la autenticación de usuarios
"""
from typing import Dict, Any, Tuple, Optional
from flask import request, current_app, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from app.models.user import User, Role
from app.extensions import db
from app.forms.auth_forms import LoginForm, RegistrationForm, PasswordChangeForm

class AuthController:
    """
    Controlador para manejar las operaciones relacionadas con la autenticación de usuarios.
    Sigue el principio de Responsabilidad Única (SRP).
    """
    
    def login(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para iniciar sesión.
        Verifica las credenciales y crea una sesión para el usuario.
        """
        form = LoginForm()
        
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            
            if user is not None and user.verify_password(form.password.data):
                login_user(user, form.remember_me.data)
                next_page = request.args.get('next')
                
                # Solo redirigir a URLs relativas seguras
                if next_page and next_page.startswith('/'):
                    return {'redirect': next_page}, 302
                
                return {'redirect': url_for('image.index')}, 302
            
            flash('Email o contraseña incorrectos.', 'error')
        
        return {'form': form}, 200
    
    def register(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para registrar un nuevo usuario.
        """
        form = RegistrationForm()
        
        if form.validate_on_submit():
            user = User(
                name=form.name.data,
                email=form.email.data,
                role='VISITOR'  # Rol predeterminado para nuevos usuarios
            )
            user.password = form.password.data
            
            db.session.add(user)
            db.session.commit()
            
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return {'redirect': url_for('auth.login')}, 302
        
        return {'form': form}, 200
    
    def logout(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para cerrar sesión.
        """
        logout_user()
        flash('Has cerrado sesión correctamente.', 'info')
        return {'redirect': url_for('image.index')}, 302
    
    def profile(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para mostrar el perfil del usuario.
        Requiere autenticación.
        """
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a tu perfil.', 'error')
            return {'redirect': url_for('auth.login')}, 302
        
        user_images = current_user.images.order_by(db.desc('created_at')).all()
        return {'user': current_user, 'user_images': user_images}, 200
    
    def change_password(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para cambiar la contraseña del usuario.
        Requiere autenticación.
        """
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para cambiar tu contraseña.', 'error')
            return {'redirect': url_for('auth.login')}, 302
        
        form = PasswordChangeForm()
        
        if form.validate_on_submit():
            if current_user.verify_password(form.current_password.data):
                current_user.password = form.new_password.data
                db.session.commit()
                flash('Tu contraseña ha sido actualizada.', 'success')
                return {'redirect': url_for('auth.profile')}, 302
            else:
                flash('La contraseña actual es incorrecta.', 'error')
        
        return {'form': form}, 200
