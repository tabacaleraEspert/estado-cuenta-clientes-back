from flask import Blueprint, request, jsonify, send_file
import os
import json
import subprocess
from werkzeug.utils import secure_filename
from sqlalchemy.sql import text
from database import get_db
from queries import comprobantes_cargados_hoy_razon_social
from procesador import procesar_resultados
from generar_pdf import generar_pdf
import zipfile
import logging
import traceback
from excelSaldoUltimos30DiasAPDF import procesar_excel_a_pdf  # 📌 Importamos la función directamente

# 📌 Configurar logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# 📌 Definir un Blueprint
uploads_bp = Blueprint("uploads", __name__)

# Directorios de trabajo
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
PDF_FOLDER = os.path.join(os.getcwd(), "pdfs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# Configuración
ALLOWED_EXTENSIONS = {"xlsx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# 📌 Función para generar PDFs sin usar subprocess
def generar_pdf_con_python(excel_file_path, output_dir, razones_sociales):
    try:
        # 📌 Ejecutar la función directamente en lugar de `subprocess.run()`
        archivos_pdf = procesar_excel_a_pdf(excel_file_path, output_dir, razones_sociales)

        if not archivos_pdf:
            raise Exception("No se generaron archivos PDF.")

        return archivos_pdf

    except Exception as e:
        print(f"❌ Error en la generación de PDFs: {str(e)}")
        raise Exception(f"Error en la generación de PDFs: {str(e)}")
    
# 📌 Ruta para subir archivos y generar ZIP con PDFs con logs detallados
@uploads_bp.route("/upload", methods=["POST"])
def upload_file():
    try:
        logger.info("📌 Iniciando proceso de subida de archivo...")

        # 📌 Verificar si se recibió un archivo
        if "file" not in request.files:
            logger.error("❌ No se recibió ningún archivo en la solicitud.")
            return jsonify({"error": "No se recibió ningún archivo."}), 400

        file = request.files["file"]
        if file.filename == "" or not allowed_file(file.filename):
            logger.error(f"❌ Archivo no permitido o sin nombre: {file.filename}")
            return jsonify({"error": "Archivo no permitido."}), 400

        # 📌 Guardar archivo en la carpeta de uploads
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        logger.info(f"📂 Archivo guardado en: {file_path}")

        # 📌 Obtener razones sociales
        razones_sociales = request.form.get("razonesSociales", "[]")
        try:
            razones_sociales = json.loads(razones_sociales)
            logger.info(f"📌 Razones sociales recibidas: {razones_sociales}")
        except json.JSONDecodeError:
            logger.error("❌ Error al decodificar razones sociales.")
            return jsonify({"error": "Formato inválido en razonesSociales."}), 400

        # 📌 Ejecutar el script de generación de PDFs
        logger.info("🚀 Ejecutando generación de PDFs...")
        archivos_pdf = generar_pdf_con_python(file_path, PDF_FOLDER, razones_sociales)
        logger.info(f"📂 Archivos PDF generados: {archivos_pdf}")

        if not archivos_pdf:
            logger.error("❌ No se generaron archivos PDF.")
            return jsonify({"error": "No se generaron archivos PDF."}), 500

        # 📌 Crear ZIP con los PDFs generados
        zip_file_path = os.path.join(PDF_FOLDER, "reportes.zip")
        logger.info(f"📌 Creando ZIP en {zip_file_path}")
        with zipfile.ZipFile(zip_file_path, "w") as zipf:
            for pdf_file in archivos_pdf:
                zipf.write(pdf_file, os.path.basename(pdf_file))  # ✅ Solo guarda el nombre del archivo


        logger.info("🎉 ZIP generado exitosamente, enviando archivo al cliente...")
        return send_file(zip_file_path, as_attachment=True)

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error en la generación del ZIP: {str(e)}\n{error_trace}")
        return jsonify({"error": f"Error al generar el ZIP: {str(e)}"}), 500
# 📌 Ruta para obtener comprobantes cargados hoy
@uploads_bp.route("/comprobantes", methods=["GET"])
def get_comprobantes():
    try:
        db = next(get_db())

        razon_social_query = comprobantes_cargados_hoy_razon_social()
        result = db.execute(razon_social_query).fetchall()

        razones_sociales = [row.RazonSocial for row in result]
        emails = [row.email for row in result]
        vendedores = [row.Vendedor for row in result]

        if not razones_sociales:
            return "No se encontraron razones sociales con comprobantes cargados hoy.", 404

        return jsonify({"razonesSociales": razones_sociales, "emails": emails, "vendedores": vendedores})

    except Exception as e:
        return f"Error al conectar con la base de datos: {str(e)}", 500
