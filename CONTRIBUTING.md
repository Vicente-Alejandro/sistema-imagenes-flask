# Guía de Contribución

¡Gracias por tu interés en contribuir al Sistema de Gestión de Imágenes PITON! Este documento proporciona las directrices para contribuir al proyecto.

## Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo puedo contribuir?](#cómo-puedo-contribuir)
  - [Reportar Bugs](#reportar-bugs)
  - [Sugerir Mejoras](#sugerir-mejoras)
  - [Pull Requests](#pull-requests)
- [Estándares de Codificación](#estándares-de-codificación)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Configuración del Entorno](#configuración-del-entorno)

## Código de Conducta

Este proyecto y todos sus participantes están regidos por un Código de Conducta que promueve un entorno respetuoso y constructivo. Al participar, se espera que respetes este código.

## ¿Cómo puedo contribuir?

### Reportar Bugs

Si encuentras un bug, por favor crea un issue siguiendo estos pasos:

1. **Verifica** que el bug no ha sido reportado ya consultando los [issues existentes](../../issues)
2. **Crea un nuevo issue** que incluya:
   - **Título claro y descriptivo**
   - **Pasos detallados para reproducir el problema**
   - **Comportamiento esperado vs. comportamiento actual**
   - **Capturas de pantalla** si corresponde
   - **Versiones** del sistema operativo, navegador y Python

### Sugerir Mejoras

Las sugerencias de funcionalidades son bienvenidas. Para proponer una mejora:

1. **Verifica** que no existe una sugerencia similar consultando los [issues existentes](../../issues)
2. **Crea un nuevo issue** con:
   - **Título claro y descriptivo**
   - **Descripción detallada** de la funcionalidad
   - **Justificación** de por qué sería beneficiosa
   - **Implementación propuesta** (opcional)

### Pull Requests

Nos encantaría recibir tus contribuciones a través de Pull Requests. Para enviar un PR:

1. **Fork** del repositorio
2. **Crea una rama** para tu funcionalidad (`git checkout -b feature/amazing-feature`)
3. **Codifica** tu funcionalidad o corrección
4. **Asegúrate** de que todos los tests pasan
5. **Documenta** los cambios en el código y actualiza README.md si es necesario
6. **Envía** tu Pull Request con una descripción detallada

## Estándares de Codificación

Para mantener la coherencia en el código:

- Sigue [PEP 8](https://www.python.org/dev/peps/pep-0008/) para Python
- Utiliza [Black](https://black.readthedocs.io/) para formatear el código
- Escribe comentarios y docstrings en español
- Nombra variables y funciones en español utilizando snake_case
- Nombra clases utilizando PascalCase

### Ejemplo de docstring:

```python
def validar_imagen(ruta_archivo):
    """
    Valida si un archivo es una imagen válida.
    
    Args:
        ruta_archivo (str): Ruta al archivo a validar
        
    Returns:
        bool: True si es una imagen válida, False en caso contrario
        
    Raises:
        FileNotFoundError: Si el archivo no existe
    """
```

## Proceso de Desarrollo

1. **Crea un issue** para la funcionalidad que deseas implementar
2. **Espera comentarios** del equipo de mantenimiento
3. **Implementa** la funcionalidad en tu fork
4. **Envía** un Pull Request
5. **Revisa** los comentarios y realiza los cambios solicitados
6. **Fusión** del PR cuando esté aprobado

## Configuración del Entorno

Para configurar tu entorno de desarrollo:

1. **Clona** el repositorio
   ```bash
   git clone https://github.com/Vicente-Alejandro/sistema-imagenes-flask.git
   cd sistema-imagenes-flask
   ```

2. **Crea un entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Dependencias para desarrollo
   ```

4. **Configura las variables de entorno**
   ```bash
   cp .env.example .env
   # Edita .env con los valores apropiados
   ```

5. **Ejecuta los tests**
   ```bash
   pytest
   ```

---

¡Gracias por contribuir a PITON! Tu ayuda es muy apreciada.
