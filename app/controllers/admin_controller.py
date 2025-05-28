"""
Controlador para el panel de administración
"""
from typing import Dict, Any, Tuple, Optional
from flask import request, current_app, abort, flash, url_for
from flask_login import current_user, login_required
from app.models.user import User, Role
from app.models.image import Image
from app.extensions import db
from app.forms.admin_forms import UserEditForm, ImageFilterForm

class AdminController:
    """
    Controlador para manejar las operaciones del panel de administración.
    Sigue el principio de Responsabilidad Única (SRP).
    """
    
    def _check_admin(self) -> bool:
        """
        Verifica si el usuario actual es un administrador.
        Aborta con código 403 si no tiene permisos.
        """
        if not current_user.is_authenticated or not current_user.is_administrator():
            abort(403)
        return True
    
    def dashboard(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para el panel principal de administración.
        Muestra estadísticas generales del sistema.
        """
        self._check_admin()
        
        user_count = User.query.count()
        image_count = Image.query.count()
        latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        latest_images = Image.query.order_by(Image.created_at.desc()).limit(5).all()
        
        stats = {
            'user_count': user_count,
            'image_count': image_count,
            'latest_users': latest_users,
            'latest_images': latest_images
        }
        
        return {'stats': stats}, 200
    
    def users(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para la gestión de usuarios.
        Muestra una lista paginada de usuarios.
        """
        self._check_admin()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        users = User.query.order_by(User.role.desc(), User.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {'users': users}, 200
    
    def edit_user(self, user_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para editar un usuario.
        Permite cambiar el nombre, email y rol del usuario.
        """
        self._check_admin()
        
        user = User.query.get_or_404(user_id)
        
        # No permitir que un administrador elimine su propio rol de administrador
        admin_only = False
        if user.id == current_user.id and user.role == 'ADMINISTRATOR':
            admin_only = True
            form = UserEditForm(obj=user, original_email=user.email)
            form.role.choices = [('ADMINISTRATOR', 'Administrador (30)')]
        else:
            form = UserEditForm(obj=user, original_email=user.email)
        
        if form.validate_on_submit():
            user.name = form.name.data
            user.email = form.email.data
            if not admin_only:
                user.role = form.role.data
            
            try:
                db.session.commit()
                flash(f'Usuario {user.name} actualizado correctamente.', 'success')
                return {'redirect': url_for('admin.users')}, 302
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error al actualizar usuario: {str(e)}")
                flash(f'Error al actualizar usuario: {str(e)}', 'error')
        
        return {'form': form, 'user': user, 'admin_only': admin_only}, 200
    
    def images(self) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para la gestión de imágenes.
        Muestra una lista paginada de imágenes con filtros.
        """
        self._check_admin()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        user_id = request.args.get('user_id', type=int)
        
        # Formulario para filtrar por usuario
        form = ImageFilterForm()
        form.user.choices = [(0, 'Todos los usuarios')] + [
            (u.id, u.name) for u in User.query.order_by(User.name).all()
        ]
        
        # Aplicar filtro si existe
        query = Image.query
        if user_id:
            query = query.filter_by(user_id=user_id)
            form.user.data = user_id
        
        images = query.order_by(Image.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {'images': images, 'form': form}, 200
    
    def delete_image(self, image_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Controlador para eliminar una imagen desde el panel de admin.
        """
        self._check_admin()
        
        image = Image.query.get_or_404(image_id)
        
        try:
            # Eliminar físicamente la imagen usando el servicio
            from app.services.image_service import ImageService
            from app.services.file_service import FileService
            
            # Crear instancias de servicios
            file_service = FileService()
            image_service = ImageService(file_service)
            
            # Intentar eliminar la imagen
            if image_service.delete_image(image.filename):
                flash('Imagen eliminada correctamente.', 'success')
            else:
                flash('La imagen fue eliminada de la base de datos, pero no se pudo eliminar el archivo físico.', 'warning')
            
            # Redirigir a la página anterior o a la lista de imágenes
            prev_url = request.referrer
            return {'redirect': prev_url or url_for('admin.images')}, 302
            
        except Exception as e:
            current_app.logger.error(f"Error al eliminar imagen: {str(e)}")
            flash(f'Error al eliminar imagen: {str(e)}', 'error')
            return {'redirect': url_for('admin.images')}, 302
