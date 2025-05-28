# Guía de Despliegue

Esta guía detalla los pasos para desplegar el Sistema de Gestión de Imágenes en windows y linux.

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
   
   # Si usarás Amazon S3, instala boto3
   pip install boto3
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con los valores apropiados
   ```

   Configura el tipo de almacenamiento en el archivo `.env`:
   ```ini
   # Para almacenamiento local (predeterminado)
   STORAGE_TYPE=local
   
   # Para almacenamiento en Amazon S3
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=tu-bucket-name
   S3_BUCKET_URL=https://tu-bucket-name.s3.amazonaws.com
   S3_ACCESS_KEY=tu-access-key
   S3_SECRET_KEY=tu-secret-key
   S3_REGION=us-east-1
   ```

5. **Inicializar la base de datos**
   ```bash

   # Crear la base de datos
   mysql -u root -p
   CREATE DATABASE $database_name$;
   
   # Inicializar la base de datos con Flask-Migrate
   flask db init
   
   # Generar la migración inicial
   flask db migrate -m "initial migration"
   
   # Aplicar la migración
   flask db upgrade
   ```

6. **Ejecutar la aplicación**
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
sudo mkdir -p /var/www/python
sudo chown $USER:$USER /var/www/python

# Clonar el código al servidor
git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask /var/www/python

# Crear entorno virtual
cd /var/www/python
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn

# Para S3 (si se va a utilizar)
pip install boto3

# Configurar la base de datos
flask db init
flask db migrate -m "initial migration"
flask db upgrade
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
errorlog = "/var/www/python/logs/gunicorn-error.log"
accesslog = "/var/www/python/logs/gunicorn-access.log"
loglevel = "info"
```

Crea directorios para logs:

```bash
mkdir -p /var/www/python/logs
```

### 4. Configuración de Supervisor

Crea un archivo de configuración para Supervisor:

```bash
sudo nano /etc/supervisor/conf.d/python.conf
```

Añade este contenido:

```ini
[program:python]
directory=/var/www/python
command=/var/www/python/venv/bin/gunicorn -c gunicorn_config.py "app:create_app()"
autostart=true
autorestart=true
stderr_logfile=/var/www/python/logs/supervisor-error.log
stdout_logfile=/var/www/python/logs/supervisor-access.log
user=www-data
environment=FLASK_ENV=production

[supervisord]
loglevel=info
```

Reinicia Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart python
```

### 5. Configuración de Nginx

Crea un archivo de configuración para Nginx:

```bash
sudo nano /etc/nginx/sites-available/python
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
        alias /var/www/python/app/static/;
        expires 30d;
    }

    location /uploads/ {
        alias /var/www/python/uploads/;
        expires 30d;
    }

    client_max_body_size 32M;  # Permitir subidas grandes
}
```

Habilita el sitio y reinicia Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/python /etc/nginx/sites-enabled/
sudo nginx -t  # Verifica la configuración
sudo systemctl restart nginx
```

### 6. Configuración de HTTPS (Opcional pero recomendado)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tudominio.com
```

## Configuración del Almacenamiento Dual

El sistema soporta dos tipos de almacenamiento para las imágenes:

### 1. Almacenamiento Local (predeterminado)

Las imágenes se guardan en el directorio `uploads/` dentro del proyecto.

- Asegúrate de que este directorio tenga permisos de escritura adecuados:
  ```bash
  # En entorno de producción (Linux)
  sudo chown -R www-data:www-data /var/www/python/uploads
  sudo chmod -R 775 /var/www/python/uploads
  ```

### 2. Almacenamiento en Amazon S3

Para utilizar Amazon S3, debes configurar lo siguiente:

1. **Crear un bucket de S3**:
   - Inicia sesión en la consola de AWS
   - Crea un nuevo bucket de S3
   - Configura el bucket para permitir acceso público (para servir imágenes)
   - Configura la política CORS para permitir solicitudes desde tu dominio

2. **Configurar IAM**:
   - Crea un usuario IAM con acceso programático
   - Adjunta la política `AmazonS3FullAccess` o crea una política personalizada
   - Guarda el Access Key y Secret Key generados

3. **Configurar variables de entorno**:
   ```ini
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=tu-bucket-name
   S3_BUCKET_URL=https://tu-bucket-name.s3.amazonaws.com
   S3_ACCESS_KEY=tu-access-key
   S3_SECRET_KEY=tu-secret-key
   S3_REGION=us-east-1
   ```

4. **Configurar política CORS de S3**:
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET"],
       "AllowedOrigins": ["*"],
       "ExposeHeaders": []
     }
   ]
   ```

## Solución de Problemas Comunes

1. **Error con python-magic**
   - En Windows: Asegúrate de instalar `python-magic-bin`
   - En Linux: Verifica que `libmagic1` esté instalado

2. **Problemas de permisos**
   ```bash
   sudo chown -R www-data:www-data /var/www/python
   sudo chmod -R 755 /var/www/python
   sudo chmod -R 775 /var/www/python/uploads
   ```

3. **Error 502 Bad Gateway**
   - Verifica los logs de Gunicorn y Supervisor
   - Asegúrate de que la aplicación se esté ejecutando correctamente

4. **Problemas con S3**
   - Verifica las credenciales de AWS en el archivo `.env`
   - Asegúrate de que el bucket de S3 tenga la configuración CORS correcta
   - Revisa los permisos del bucket y del usuario IAM
   - Comprueba los logs de la aplicación para errores relacionados con AWS

## Actualización de la Aplicación

Para actualizar la aplicación a una nueva versión:

```bash
cd /var/www/python
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart python
```
