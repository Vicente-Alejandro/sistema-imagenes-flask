# Guía de Despliegue: Aplicación Flask en Debian 12

Esta guía detalla los pasos para desplegar la aplicación de galería de imágenes Flask en un servidor Debian 12 utilizando Gunicorn y Nginx.

## 1. Prerrequisitos

*   Servidor Debian 12.
*   Acceso SSH con privilegios sudo.
*   Un nombre de dominio (opcional, pero recomendado para SSL).
*   Credenciales de AWS S3 y RDS (si se utilizan).

## 2. Preparación del Servidor

Actualiza el sistema e instala las dependencias esenciales:

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv nginx mariadb-server libmariadb-dev libmagic-dev build-essential libffi-dev python3-dev git

# Instalar Certbot para SSL (opcional)
sudo apt install -y certbot python3-certbot-nginx
```

## 3. Configuración de la Base de Datos (MariaDB/MySQL)

```bash
# Iniciar y asegurar la instalación de MariaDB
sudo systemctl start mariadb
sudo mysql_secure_installation
# Sigue las instrucciones. Es recomendable establecer una contraseña root segura.
```

Crea la base de datos y el usuario para la aplicación:
```bash
sudo mysql -u root -p
```

En el prompt de MariaDB:
```sql
CREATE DATABASE piton CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'TuContraseñaSeguraParaAdmin';
GRANT ALL PRIVILEGES ON piton.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```
**Nota:** Reemplaza `TuContraseñaSeguraParaAdmin` con una contraseña fuerte.

## 4. Configuración del Usuario para la Aplicación

Crea un usuario dedicado para ejecutar la aplicación:
```bash
sudo useradd -m -s /bin/bash piton_app
# Opcional: Establecer contraseña para el usuario
# sudo passwd piton_app
```

## 5. Despliegue de la Aplicación

Cambia al nuevo usuario y clona/sube tu aplicación:
```bash
sudo su - piton_app

# Clonar el repositorio (reemplaza con tu URL de repositorio)
git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask.git /home/piton_app/app
cd /home/piton_app/app

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias (asegúrate que requirements.txt esté actualizado)
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn # Servidor WSGI para producción
```

## 6. Configuración de la Aplicación (Archivo `.env`)

Crea y configura el archivo `.env` en el directorio raíz de la aplicación (`/home/piton_app/app/.env`):
```bash
nano /home/piton_app/app/.env
```
Contenido del archivo `.env` para producción:
```env
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=GENERAR_UNA_CLAVE_SECRETA_MUY_LARGA_Y_ALEATORIA
DEBUG=false
PORT=80 # Aunque Gunicorn usará un socket, Nginx escuchará en el 80

# Configuración de la Base de Datos
DB_CONNECTION=mysql
DB_DRIVER=mysqlclient # Asegúrate que mysqlclient esté en requirements.txt
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=piton
DB_USERNAME=admin
DB_PASSWORD=TuContraseñaSeguraParaAdmin # La misma que creaste antes
DB_USE_SSL=false # O true si configuraste SSL para MariaDB

# Configuración de Almacenamiento (S3 o local)
STORAGE_TYPE=s3 # o 'local'
AWS_CREDENTIALS_SOURCE=database # o 'env'

# Si AWS_CREDENTIALS_SOURCE=env o para inicialización desde .env
S3_BUCKET_NAME=tu-bucket-s3
S3_BUCKET_URL=https://tu-bucket-s3.s3.tu-region.amazonaws.com
S3_REGION=tu-region
# S3_ACCESS_KEY=TU_ACCESS_KEY (Solo si AWS_CREDENTIALS_SOURCE=env)
# S3_SECRET_KEY=TU_SECRET_KEY (Solo si AWS_CREDENTIALS_SOURCE=env)

# Otros...
APP_NAME="Galería de Imágenes"
MAX_CONTENT_LENGTH=16777216 # 16MB
```
**Importante:** Genera una `SECRET_KEY` única y segura. Puedes usar `python -c 'import secrets; print(secrets.token_hex(32))'`.

## 7. Migraciones de Base de Datos

Aplica las migraciones de la base de datos:
```bash
# Asegúrate de estar en /home/piton_app/app y con el venv activado
flask db upgrade
```
Si es la primera vez y necesitas inicializar datos (ej. credenciales AWS en DB):
```bash
# flask init-db # (Si tienes un comando para esto)
```

## 8. Configuración de Gunicorn

### 8.1. Crear archivo `wsgi.py`

En el directorio raíz de tu aplicación (`/home/piton_app/app/wsgi.py`), crea este archivo si no existe:
```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Esto es para desarrollo, Gunicorn no lo usará directamente
    app.run()
```

### 8.2. Crear Servicio Systemd para Gunicorn

Sal del shell del usuario `piton_app` (escribe `exit`) para volver a tu usuario con sudo.
Crea un archivo de servicio systemd para Gunicorn:
```bash
sudo nano /etc/systemd/system/piton.service
```
Pega el siguiente contenido:
```ini
[Unit]
Description=Gunicorn instance to serve PITON Flask app
After=network.target

[Service]
User=piton_app
Group=www-data # O el grupo de piton_app si no usas www-data para Nginx
WorkingDirectory=/home/piton_app/app
Environment="PATH=/home/piton_app/app/venv/bin"
EnvironmentFile=/home/piton_app/app/.env # Carga las variables de entorno
ExecStart=/home/piton_app/app/venv/bin/gunicorn --workers 3 --bind unix:/home/piton_app/app/piton.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

### 8.3. Iniciar y Habilitar Gunicorn

```bash
sudo systemctl daemon-reload
sudo systemctl start piton
sudo systemctl enable piton # Para que inicie automáticamente con el sistema
```
Verifica el estado:
```bash
sudo systemctl status piton
# Deberías ver "active (running)"
# También verifica que el socket se haya creado:
ls -la /home/piton_app/app/piton.sock
```

## 9. Configuración de Nginx como Proxy Inverso

Crea un archivo de configuración para tu sitio en Nginx:
```bash
sudo nano /etc/nginx/sites-available/piton
```
Pega la siguiente configuración (reemplaza `tu-dominio.com` con tu dominio o IP):
```nginx
server {
    listen 80; # Escucha en el puerto 80 para HTTP
    # Si es el único sitio o el principal, puedes añadir default_server
    # listen 80 default_server;

    server_name tu-dominio.com www.tu-dominio.com; # Reemplaza con tu dominio

    location /static {
        alias /home/piton_app/app/app/static; # Ruta a tus archivos estáticos
        expires 30d;
    }

    location /uploads { # Si tienes una carpeta de uploads local servida por Nginx
        alias /home/piton_app/app/app/uploads; # Ruta a tus uploads
        expires 30d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/piton_app/app/piton.sock;
    }
}
```

Habilita el sitio creando un enlace simbólico y prueba la configuración de Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/piton /etc/nginx/sites-enabled/
sudo nginx -t
```
Si la prueba es exitosa (`syntax is ok`, `test is successful`), reinicia Nginx:
```bash
sudo systemctl restart nginx
```

## 10. Configuración de Firewall (UFW)

Si tienes UFW habilitado, permite el tráfico HTTP y HTTPS:
```bash
sudo ufw allow 'Nginx Full' # Permite tráfico en puerto 80 y 443
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

## 11. Configuración de SSL con Certbot (Opcional pero Recomendado)

Si tienes un nombre de dominio, puedes configurar SSL fácilmente:
```bash
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
# Sigue las instrucciones. Certbot modificará tu archivo de Nginx para HTTPS.
```
Esto también configurará la renovación automática.

## 12. Troubleshooting: "Página por defecto de Nginx"

Si después de configurar Nginx sigues viendo la página de bienvenida de Nginx en lugar de tu aplicación, sigue estos pasos:

### 12.1. Verificar Gunicorn
Asegúrate que Gunicorn esté corriendo y el socket exista:
```bash
sudo systemctl status piton
# Debería estar "active (running)"

ls -la /home/piton_app/app/piton.sock
# Deberías ver el archivo del socket.
```
Si Gunicorn no está corriendo, revisa sus logs:
```bash
sudo journalctl -u piton -n 50 --no-pager
```
Intenta iniciar Gunicorn manualmente para ver errores detallados:
```bash
sudo su - piton_app
cd /home/piton_app/app
source venv/bin/activate
gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:app
# Intenta acceder a http://TU_IP_DEL_SERVIDOR:8000 desde tu navegador.
# Presiona CTRL+C para detenerlo. Luego sal del usuario piton_app (`exit`).
```

### 12.2. Verificar Configuración de Nginx
Revisa la sintaxis de Nginx:
```bash
sudo nginx -t
```
Asegúrate que tu archivo de configuración del sitio (`/etc/nginx/sites-enabled/piton`) esté correcto y que la directiva `proxy_pass` apunte al socket correcto.

### 12.3. Deshabilitar el Sitio por Defecto de Nginx
A veces, la configuración por defecto de Nginx interfiere.
```bash
# Verifica si el sitio por defecto está habilitado
ls -l /etc/nginx/sites-enabled/default

# Si existe, elimínalo (es un symlink)
sudo rm /etc/nginx/sites-enabled/default
```
Si quieres que tu sitio sea el predeterminado, añade `default_server` a la directiva `listen` en tu archivo `/etc/nginx/sites-available/piton`:
```nginx
server {
    listen 80 default_server;
    # ... resto de la configuración
}
```

### 12.4. Verificar `nginx.conf`
Asegúrate que el archivo principal de Nginx (`/etc/nginx/nginx.conf`) incluya los sitios habilitados. Debería tener una línea como:
```nginx
include /etc/nginx/sites-enabled/*;
```
dentro del bloque `http { ... }`.

### 12.5. Permisos
Asegúrate que el usuario `www-data` (o el usuario con el que corre Nginx) tenga permisos para acceder al socket de Gunicorn. El `-m 007` en el `ExecStart` de Gunicorn debería permitir esto, pero verifica los permisos del directorio `/home/piton_app/app`.

### 12.6. Reiniciar Servicios
Después de cualquier cambio en la configuración de Gunicorn o Nginx:
```bash
sudo systemctl daemon-reload # Si cambiaste archivos .service
sudo systemctl restart piton
sudo systemctl restart nginx
```

## 13. Verificación Final y Monitoreo

*   Accede a tu aplicación a través de `http://tu-dominio.com` (o `https://` si configuraste SSL).
*   Revisa los logs de Gunicorn: `sudo journalctl -u piton -f`
*   Revisa los logs de Nginx:
    *   `sudo tail -f /var/log/nginx/access.log`
    *   `sudo tail -f /var/log/nginx/error.log`

## 14. (Opcional) Configurar Tarea Cron para Backup Lambda en el Servidor

Si deseas invocar tu función Lambda de backup de base de datos desde el servidor Debian usando un cron job:

1.  **Instalar AWS CLI**:
    ```bash
    sudo apt install awscli -y
    ```
2.  **Configurar AWS CLI**:
    ```bash
    aws configure
    # Ingresa tu AWS Access Key ID, Secret Access Key, Default region name, y Default output format.
    # Es recomendable crear un usuario IAM con permisos mínimos solo para invocar la Lambda.
    ```
3.  **Crear el Cron Job**:
    ```bash
    sudo crontab -e
    ```
    Añade una línea para ejecutar la Lambda. Por ejemplo, todos los días a las 23:59:
    ```cron
    59 23 * * * /usr/bin/aws lambda invoke --function-name NOMBRE_DE_TU_FUNCION_LAMBDA --cli-binary-format raw-in-base64-out --payload '{}' /tmp/lambda_backup_output.txt > /tmp/lambda_backup_cron.log 2>&1
    ```
    Reemplaza `NOMBRE_DE_TU_FUNCION_LAMBDA` con el nombre real de tu función Lambda. El output se guardará en `/tmp/lambda_backup_output.txt` y los logs del cron en `/tmp/lambda_backup_cron.log`.

---

¡Tu aplicación debería estar ahora desplegada y funcionando!

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
