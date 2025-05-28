"""
Filtros y funciones globales para plantillas Jinja2
"""
from datetime import datetime
import os

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """
    Formatea una fecha en un formato más legible
    
    Args:
        value: La fecha a formatear
        format: El formato de salida (predeterminado: '%d/%m/%Y %H:%M')
        
    Returns:
        str: La fecha formateada
    """
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    
    if value is None:
        return ''
        
    return value.strftime(format)

def format_filesize(bytes, suffix='B'):
    """
    Formatea un tamaño de archivo a un formato legible por humanos
    
    Args:
        bytes: El tamaño en bytes
        suffix: El sufijo a utilizar (predeterminado: 'B')
        
    Returns:
        str: El tamaño formateado
    """
    if bytes is None:
        return '0 B'
    
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(bytes) < 1024.0:
            return f"{bytes:.1f} {unit}{suffix}"
        bytes /= 1024.0
    
    return f"{bytes:.1f} Y{suffix}"

def init_template_filters(app):
    """
    Registra filtros y funciones globales para plantillas Jinja2
    
    Args:
        app: La instancia de la aplicación Flask
    """
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['filesize'] = format_filesize
    
    # Funciones globales para acceder a los roles de usuario
    from app.models.user import Role
    app.jinja_env.globals.update(Role=Role)
