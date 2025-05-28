"""
Rutas para el panel de administración
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models.user import User, Role
from app.models.image import Image
from app.forms.admin_forms import UserEditForm, ImageFilterForm
from app.extensions import db

# Crear blueprint para rutas de administración
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorador para comprobar si el usuario es administrador
def admin_required(func):
    """Decorador para restringir acceso solo a administradores"""
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_administrator():
            abort(403)
        return func(*args, **kwargs)
    # Preservar el nombre de la función para Flask
    decorated_view.__name__ = func.__name__
    return decorated_view

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Vista principal del panel de administración"""
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
    
    return render_template('admin/index.html', stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Vista para gestionar usuarios"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.role.desc(), User.name).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Vista para editar un usuario"""
    user = User.query.get_or_404(user_id)
    
    # No permitir que un administrador elimine su propio rol de administrador
    if user.id == current_user.id and user.role == 'ADMINISTRATOR':
        admin_only = True
        form = UserEditForm(original_email=user.email, obj=user)
        form.role.choices = [('ADMINISTRATOR', 'Administrador (30)')]
    else:
        admin_only = False
        form = UserEditForm(original_email=user.email, obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        if not admin_only:
            user.role = form.role.data
        db.session.commit()
        flash(f'Usuario {user.name} actualizado correctamente.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user, admin_only=admin_only)

@admin_bp.route('/images')
@login_required
@admin_required
def images():
    """Vista para gestionar imágenes"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    # Obtener todas las imágenes para la búsqueda en el frontend
    query = Image.query
    
    # Ordenar por fecha de creación (más reciente primero)
    query = query.order_by(Image.created_at.desc())
    
    # Paginar los resultados
    images = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/images.html', images=images)

@admin_bp.route('/images/<int:image_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_image(image_id):
    """Vista para eliminar una imagen"""
    image = Image.query.get_or_404(image_id)
    
    # Eliminar físicamente la imagen
    from app.services.image_service import ImageService
    from app.services.file_service import FileService
    
    # Crear instancias de servicios
    file_service = FileService()
    image_service = ImageService(file_service)
    
    try:
        image_service.delete_image(image.filename)
        db.session.delete(image)
        db.session.commit()
        flash('Imagen eliminada correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar la imagen: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin.images'))
