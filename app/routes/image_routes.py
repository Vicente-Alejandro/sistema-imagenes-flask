from flask import Blueprint, render_template, current_app, jsonify, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.controllers.image_controller import ImageController
from app.services.image_service import ImageService
from app.services.file_service import FileService
from app.models.user import Role, User
from app.models.image import Image

# Crear blueprint para imágenes
image_bp = Blueprint('image', __name__)

# Crear instancias de servicios y controladores
file_service = FileService()
image_service = ImageService(file_service)
image_controller = ImageController(image_service)

@image_bp.route('/')
def index():
    """Ruta para la página principal/galería"""
    response, status_code = image_controller.index()
    return render_template('gallery/index.html', images=response['images'], user=current_user)

@image_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Ruta para subir imágenes (requiere autenticación)"""
    # El controlador ya verifica permisos de usuario
    response, status_code = image_controller.upload_images()
    
    # Si hay una redirección en la respuesta, seguirla
    if status_code in (301, 302) and 'redirect' in response:
        return redirect(response['redirect'])
        
    return jsonify(response), status_code

@image_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Ruta para servir una imagen desde la carpeta de uploads"""
    # Esta ruta permite acceso público a las imágenes
    return image_controller.serve_image(filename)

@image_bp.route('/delete/<filename>', methods=['POST', 'DELETE'])
@login_required
def delete_file(filename):
    """Ruta para eliminar una imagen (requiere autenticación)"""
    # El controlador ya verifica permisos de usuario
    response, status_code = image_controller.delete_image(filename)
    
    # Si hay una redirección en la respuesta, seguirla
    if status_code in (301, 302) and 'redirect' in response:
        return redirect(response['redirect'])
        
    # Si se solicita desde una página web y no es una solicitud AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest' and request.referrer:
        return redirect(request.referrer)
        
    return jsonify(response), status_code

@image_bp.route('/update-name/<filename>', methods=['PUT', 'POST'])
@login_required
def update_image_name(filename):
    """Ruta para actualizar el nombre de una imagen (requiere autenticación)"""
    # El controlador ya verifica permisos de usuario
    response, status_code = image_controller.update_image_name(filename)
    
    # Si hay una redirección en la respuesta, seguirla
    if status_code in (301, 302) and 'redirect' in response:
        return redirect(response['redirect'])
    
    # Si se solicita desde una página web y no es una solicitud AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest' and request.referrer:
        return redirect(request.referrer)
        
    return jsonify(response), status_code
