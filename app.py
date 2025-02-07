from flask import Flask
from flask_cors import CORS
import os
from routes import uploads_bp  # Importamos el Blueprint correctamente

app = Flask(__name__)

# 🔹 Azure asigna dinámicamente un puerto, si no, usa 5001 por defecto
port = int(os.getenv("PORT", 5001))

# Configurar CORS para permitir solicitudes desde el frontend
# allowed_origins = ["https://jolly-flower-07b4b210f.4.azurestaticapps.net", "http://localhost:5173"]
# CORS(app, origins=allowed_origins, methods=["GET", "POST", "PUT", "DELETE"], supports_credentials=True)

CORS(app, resources={r"/*": {"origins": "*"}})


# 📌 Registrar el Blueprint `uploads_bp`
app.register_blueprint(uploads_bp, url_prefix="/api")  # Prefijo opcional

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
