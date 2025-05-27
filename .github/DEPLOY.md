# Guía de Despliegue para PITON

Esta guía detalla los pasos para desplegar el Sistema de Gestión de Imágenes PITON en diferentes entornos.

## Requisitos Previos

- Python 3.8+ o PyPy 3.8+
- Nginx (para producción)
- Debian/Ubuntu (recomendado para producción)
- Librerías del sistema: `libmagic1`

## Despliegue en Desarrollo

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask.git
   cd sistema-imagenes-flask
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con los valores apropiados
   ```

5. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

## Despliegue en Producción (Debian/Ubuntu)

### 1. Preparación del Servidor

```bash
# Actualizar repositorios
sudo apt update
sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv nginx supervisor libmagic1
```

### 2. Configuración del Proyecto

```bash
# Crear directorio para la aplicación
sudo mkdir -p /var/www/piton
sudo chown $USER:$USER /var/www/piton

# Clonar el código al servidor
git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask /var/www/piton

# Crear entorno virtual
cd /var/www/piton
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn
```

### 3. Configuración de Gunicorn

Crea un archivo `gunicorn_config.py` en la raíz del proyecto:

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 3  # (2 x núcleos) + 1
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
    #server_name tudominio.com;  # Cambia por tu dominio
    server_name localhost;

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

    client_max_body_size 32M;  # Permitir subidas grandes
}
```

Habilita el sitio y reinicia Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/piton /etc/nginx/sites-enabled/
sudo nginx -t  # Verifica la configuración
sudo systemctl restart nginx
```

### 6. Configuración de HTTPS (Opcional pero recomendado)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tudominio.com
```

## Solución de Problemas Comunes

1. **Error con python-magic**
   - En Windows: Asegúrate de instalar `python-magic-bin`
   - En Linux: Verifica que `libmagic1` esté instalado

2. **Problemas de permisos**
   ```bash
   sudo chown -R www-data:www-data /var/www/piton
   sudo chmod -R 755 /var/www/piton
   sudo chmod -R 775 /var/www/piton/uploads
   ```

3. **Error 502 Bad Gateway**
   - Verifica los logs de Gunicorn y Supervisor
   - Asegúrate de que la aplicación se esté ejecutando correctamente

## Actualización de la Aplicación

Para actualizar la aplicación a una nueva versión:

```bash
cd /var/www/piton
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart piton
```
