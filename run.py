from app import create_app
from app.config import DevelopmentConfig
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app(DevelopmentConfig)

HOST = os.environ.get('HOST', '0.0.0.0')
try:
    PORT = int(os.environ.get('PORT', 3000))
except (ValueError, TypeError):
    PORT = 3000

if __name__ == '__main__':
    app.run(debug=True, host=HOST, port=PORT)
