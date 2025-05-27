# Sistema de Gestión de Imágenes PITON

Sistema web para la carga, visualización y gestión de imágenes basado en Flask con arquitectura MVC y principios SOLID.

## Características

- Carga y visualización de imágenes
- Conversión automática a formato WebP para optimizar el almacenamiento
- Lazy loading para cargar imágenes según se necesiten
- Validación extensa de imágenes para seguridad
- Diseño basado en principios SOLID y patrón MVC

## Requisitos

- Python 3.8+ o PyPy 3.8+
- Nginx
- Debian/Ubuntu (para entorno de producción)
- Librerías del sistema: libmagic1

## Estructura del Proyecto

```
PITON/
├── app/                      # Paquete principal
│   ├── __init__.py           # Fábrica de aplicación
│   ├── config.py             # Configuraciones
│   ├── controllers/          # Controladores
│   ├── models/               # Modelos
│   ├── routes/               # Rutas
│   ├── services/             # Servicios
│   ├── static/               # Archivos estáticos
│   ├── templates/            # Plantillas HTML
│   └── image_metadata.json   # Metadatos de imágenes
├── uploads/                  # Directorio de imágenes
├── tests/                    # Pruebas unitarias
├── run.py                    # Script para desarrollo
├── requirements.txt          # Dependencias
└── README.md                 # Este archivo
```

## Guía de Despliegue en Producción

### 1. Preparación del Servidor

```bash
# Actualizar repositorios
sudo apt update
sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv nginx supervisor libmagic1

# Si prefieres usar PyPy:
sudo apt install -y pypy3 pypy3-pip
```

### 2. Configuración del Proyecto

```bash
# Crear directorio para la aplicación
sudo mkdir -p /var/www/piton
sudo chown $USER:$USER /var/www/piton

# Clonar o copiar el código al servidor
# (Ejemplo con git, ajusta según tu método de despliegue)
git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask /var/www/piton
# O copia los archivos por SFTP/SCP

# Crear entorno virtual
cd /var/www/piton
python3 -m venv venv
# O con PyPy:
# pypy3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn  # O uwsgi
```

### 3. Configuración de Gunicorn

Crea un archivo `gunicorn_config.py` en la raíz del proyecto:

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 3  # Número de workers: (2 x núcleos) + 1
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "/var/www/piton/logs/gunicorn-error.log"
accesslog = "/var/www/piton/logs/gunicorn-access.log"
loglevel = "info"
```

Crea directorios para logs:

```bash
mkdir -p /var/www/piton/logs
```

### 4. Configuración de Supervisor

Crea un archivo de configuración para Supervisor:

```bash
sudo nano /etc/supervisor/conf.d/piton.conf
```

Añade este contenido:

```ini
[program:piton]
directory=/var/www/piton
command=/var/www/piton/venv/bin/gunicorn -c gunicorn_config.py "app:create_app()"
autostart=true
autorestart=true
stderr_logfile=/var/www/piton/logs/supervisor-error.log
stdout_logfile=/var/www/piton/logs/supervisor-access.log
user=www-data
environment=FLASK_ENV=production

[supervisord]
loglevel=info
```

Reinicia Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart piton
```

### 5. Configuración de Nginx

Crea un archivo de configuración para Nginx:

```bash
sudo nano /etc/nginx/sites-available/piton
```

Añade este contenido:

```nginx
server {
    listen 80;
    server_name tudominio.com;  # Cambia por tu dominio

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/piton/app/static/;
        expires 30d;
    }

    location /uploads/ {
        alias /var/www/piton/uploads/;
        expires 30d;
    }

    client_max_body_size 16M;  # Permitir subidas de hasta 16MB
}
```

Habilita el sitio y reinicia Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/piton /etc/nginx/sites-enabled/
sudo nginx -t  # Verifica la configuración
sudo systemctl restart nginx
```

### 6. Configuración de Seguridad

#### Permisos de archivos

```bash
# Establecer permisos correctos
sudo chown -R www-data:www-data /var/www/piton
sudo chmod -R 755 /var/www/piton

# Asegurar que los directorios de uploads sean escribibles
sudo chmod -R 775 /var/www/piton/uploads
```

#### Configurar HTTPS con Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tudominio.com
```

### 7. Actualizaciones del Sistema

Para actualizar el sistema:

```bash
# Preparar la actualización
cd /var/www/piton
source venv/bin/activate

# Hacer copia de seguridad
cp -r uploads uploads_backup
cp app/image_metadata.json image_metadata_backup.json

# Actualizar código (depende de tu método de despliegue)
git pull  # O actualiza los archivos manualmente

# Actualizar dependencias si es necesario
pip install -r requirements.txt

# Reiniciar servicios
sudo supervisorctl restart piton
```

## Solución de Problemas

### Verificar logs

```bash
# Logs de Gunicorn
tail -f /var/www/piton/logs/gunicorn-error.log

# Logs de Supervisor
tail -f /var/www/piton/logs/supervisor-error.log

# Logs de Nginx
tail -f /var/log/nginx/error.log
```

### Problemas comunes

1. **Error 502 Bad Gateway**: Verifica que Gunicorn esté funcionando correctamente.
2. **Problemas con python-magic**: Asegúrate de haber instalado `libmagic1`.
3. **Permisos de archivos**: Verifica que www-data tenga permisos de escritura en uploads.

## Notas Importantes

- La aplicación usa la biblioteca `python-magic` que requiere `libmagic1` en sistemas Debian/Ubuntu.
- Para entornos de alta disponibilidad, considera usar balanceadores de carga y múltiples instancias.
- Realiza copias de seguridad regulares del directorio `uploads` y del archivo `app/image_metadata.json`.
