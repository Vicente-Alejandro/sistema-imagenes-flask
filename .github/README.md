# PITON - Sistema de Gestión de Imágenes

Una aplicación web basada en Flask para cargar, visualizar y gestionar imágenes de forma eficiente.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 🌟 Características

- ✅ Carga y visualización de imágenes en una interfaz moderna
- ✅ Conversión automática a formato WebP para optimizar espacio
- ✅ Lazy loading para carga eficiente de imágenes
- ✅ Validación extensa de imágenes para seguridad
- ✅ Arquitectura MVC con principios SOLID

## 🚀 Instalación

1. Clona este repositorio
   ```bash
   git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask.git
   cd sistema-imagenes-flask
   ```

2. Crea un entorno virtual e instala las dependencias
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. En sistemas Windows, asegúrate de instalar python-magic-bin
   ```bash
   pip install python-magic-bin==0.4.14
   ```

4. En sistemas Linux/Debian, instala la dependencia del sistema
   ```bash
   sudo apt-get install libmagic1
   ```

5. Ejecuta la aplicación
   ```bash
   python run.py
   ```

6. Abre tu navegador en `http://localhost:3000`

## 📁 Estructura del Proyecto

El proyecto sigue un patrón de arquitectura MVC con principios SOLID:

```
PITON/
├── app/                      # Paquete principal
│   ├── controllers/          # Controladores (lógica de negocio)
│   ├── models/               # Modelos (datos)
│   ├── services/             # Servicios (lógica de aplicación)
│   ├── routes/               # Rutas y endpoints
│   ├── static/               # Archivos estáticos (CSS, JS)
│   └── templates/            # Plantillas HTML
├── uploads/                  # Carpeta para archivos subidos
└── tests/                    # Pruebas unitarias
```

## 🔧 Configuración para Producción

Consulta el archivo [DEPLOY.md](DEPLOY.md) para instrucciones detalladas sobre cómo desplegar esta aplicación en un entorno de producción.

## 📜 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, siéntete libre de abrir un issue o crear un pull request.

1. Haz un fork del proyecto
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Sube tu rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request
