# Nombre de tu Proyecto (Ej: Galería de Imágenes Flask)

Descripción breve de tu proyecto...

## Características

*   Modal/lightbox para visualización de imágenes a tamaño completo.
*   Carga diferida (lazy loading) para optimizar rendimiento.
*   Nombres aleatorios generados con UUID para mayor seguridad.
*   Conversión automática a formato WebP para optimizar almacenamiento.
*   Gestión de imágenes con almacenamiento en AWS S3.
*   Sistema de backup de base de datos automatizado con AWS Lambda.

## Requisitos Previos (Desarrollo Local)

*   Python 3.8+
*   pip
*   Virtualenv (recomendado)
*   MariaDB/MySQL (para base de datos local)

## Instalación (Desarrollo Local)

1.  Clona el repositorio:
    ```bash
    git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask.git
    cd sistema-imagenes-flask
    ```
2.  Crea y activa un entorno virtual:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Linux/macOS
    # venv\Scripts\activate    # En Windows
    ```
3.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configura tus variables de entorno. Copia `.env.example` a `.env` y edítalo con tu configuración local:
    ```bash
    cp .env.example .env
    nano .env # o tu editor preferido
    ```
    Asegúrate de configurar las credenciales de la base de datos local y, si es necesario, las de AWS para S3 si `STORAGE_TYPE=s3` y `AWS_CREDENTIALS_SOURCE=env`.

5.  Configura tu base de datos local (MariaDB/MySQL) y crea la base de datos especificada en `.env`.

6.  Aplica las migraciones de la base de datos:
    ```bash
    flask db upgrade
    ```
7.  Ejecuta la aplicación:
    ```bash
    flask run
    ```
    La aplicación estará disponible en `http://127.0.0.1:PUERTO` (el puerto se define en `.env`).

## Despliegue

Para instrucciones detalladas sobre cómo desplegar esta aplicación en un servidor de producción (Debian 12 con Gunicorn y Nginx), por favor consulta la **[Guía de Despliegue](.github/DEPLOY.MD)**.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles (si existe).
