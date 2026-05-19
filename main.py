# Clase en vídeo: https://youtu.be/_y9qQZXE24A

### Hola Mundo ###

# Documentación oficial: https://fastapi.tiangolo.com/es/

# Instala FastAPI: pip install "fastapi[all]"

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Inicia el server: uvicorn main:app --reload
# Detener el server: CTRL+C

# Documentación con Swagger: http://127.0.0.1:8000/docs
# Documentación con Redocly: http://127.0.0.1:8000/redoc

"""
Iniciar entorno virtual
python -m venv venv

Activar entorno virtual
.\venv\Scripts\Activate.ps1

Desactivar entorno virtual
.\venv\Scripts\Deactivate.ps1

"""

