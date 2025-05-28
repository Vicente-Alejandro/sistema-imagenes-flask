"""
Comandos CLI personalizados para la aplicación
"""
import os
import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import User, Role

def register_commands(app):
    """
    Registra comandos CLI personalizados para la aplicación
    
    Args:
        app: La instancia de la aplicación Flask
    """
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)

@click.command('init-db')
@click.option('--drop', is_flag=True, help='Eliminar tablas existentes antes de crear nuevas')
@with_appcontext
def init_db_command(drop):
    """Inicializa la base de datos."""
    if drop:
        click.echo('Eliminando tablas existentes...')
        db.drop_all()
    
    click.echo('Creando tablas...')
    db.create_all()
    
    # Verificar si se necesita migrar datos del sistema basado en archivos
    migrate_existing_data()
    
    click.echo('¡Base de datos inicializada!')

@click.command('create-admin')
@click.option('--name', prompt=True, help='Nombre del administrador')
@click.option('--email', prompt=True, help='Email del administrador')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Contraseña del administrador')
@with_appcontext
def create_admin_command(name, email, password):
    """Crea un usuario administrador."""
    # Verificar si el correo ya existe
    if User.query.filter_by(email=email).first():
        click.echo(f'Error: Ya existe un usuario con el correo {email}')
        return
    
    # Crear el usuario administrador
    admin = User(name=name, email=email, role='ADMINISTRATOR')
    admin.password = password
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'Usuario administrador creado: {name} ({email})')

def migrate_existing_data():
    """Migra los datos existentes del sistema basado en archivos a la base de datos."""
    from app.services.image_service import ImageService
    from app.models.image import Image
    import json
    
    # Verificar si hay un archivo de metadata existente
    metadata_path = os.path.join(current_app.root_path, 'image_metadata.json')
    if not os.path.exists(metadata_path):
        click.echo('No se encontró archivo de metadata para migrar.')
        return
    
    try:
        # Leer el archivo JSON
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Verificar si hay un usuario admin para asociar las imágenes
        admin = User.query.filter_by(role='ADMINISTRATOR').first()
        if not admin:
            # Crear un usuario admin temporal para la migración
            admin = User(
                name='Admin',
                email='admin@example.com',
                role='ADMINISTRATOR'
            )
            admin.password = 'temppassword123'  # Contraseña temporal, debe cambiarse después
            db.session.add(admin)
            db.session.commit()
            click.echo('Se creó un usuario admin temporal para la migración. Email: admin@example.com, Contraseña: temppassword123')
        
        # Migrar cada imagen
        count = 0
        for filename, data in metadata.items():
            # Verificar si la imagen ya existe en la base de datos
            if Image.query.filter_by(filename=filename).first():
                continue
            
            # Crear el objeto Image
            image = Image(
                filename=filename,
                original_filename=data.get('original_filename', filename),
                created_at=data.get('created_at'),
                user_id=admin.id  # Asignar al admin
            )
            
            # Obtener datos adicionales si están disponibles
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                image.file_size = file_size
            
            db.session.add(image)
            count += 1
        
        if count > 0:
            db.session.commit()
            click.echo(f'Se migraron {count} imágenes a la base de datos.')
        else:
            click.echo('No se encontraron imágenes nuevas para migrar.')
            
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error al migrar datos: {str(e)}')
