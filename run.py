from app import create_app
from app.config import get_config, HOST, PORT
import os

# Obtener la configuración adecuada para el entorno actual
config = get_config()

# Crear la aplicación con la configuración
app = create_app(config)

if __name__ == '__main__':
    # Iniciar la aplicación con la configuración
    app.run(debug=config.DEBUG, host=HOST, port=PORT)
    
    # Mostrar información sobre la configuración actual
    env = os.environ.get('FLASK_ENV', 'development').upper()
    print(f"Aplicación iniciada en modo {env} con DEBUG={config.DEBUG}")
    print(f"Ejecutándose en {HOST}:{PORT}")
