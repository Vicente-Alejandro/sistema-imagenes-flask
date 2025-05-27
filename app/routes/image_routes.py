from flask import Blueprint, render_template, current_app, jsonify, request
from app.controllers.image_controller import ImageController
from app.services.image_service import ImageService
from app.services.file_service import FileService

# Crear blueprint para imágenes
image_bp = Blueprint('images', __name__)

# Crear instancias de servicios y controladores
file_service = FileService()
image_service = ImageService(file_service)
image_controller = ImageController(image_service)

@image_bp.route('/')
def index():
    """Ruta para la página principal"""
    response, status_code = image_controller.index()
    return render_template('gallery/index.html', images=response['images'])

@image_bp.route('/upload', methods=['POST'])
def upload_file():
    """Ruta para subir imágenes"""
    response, status_code = image_controller.upload_images()
    return jsonify(response), status_code

@image_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Ruta para servir una imagen desde la carpeta de uploads"""
    return image_controller.serve_image(filename)

@image_bp.route('/delete/<filename>')
def delete_file(filename):
    """Ruta para eliminar una imagen"""
    response, status_code = image_controller.delete_image(filename)
    return jsonify(response), status_code
