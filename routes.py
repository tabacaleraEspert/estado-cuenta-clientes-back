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
from jsonSaldoUltimos30DiasAPDF import procesar_json_a_pdf
import xlsxwriter
import io
import shutil  # Agregar esta importación al inicio del archivo





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
# @uploads_bp.route("/comprobantes", methods=["GET"])
# def get_comprobantes():
#     try:
#         db = next(get_db())

#         razon_social_query = comprobantes_cargados_hoy_razon_social()
#         result = db.execute(razon_social_query).fetchall()

#         print(result)

#         return jsonify({"result": [dict(row._mapping) for row in result]})

#     except Exception as e:
#         return f"Error al conectar con la base de datos: {str(e)}", 500
    
    
# 📌 Ruta para obtener comprobantes cargados hoy ESTE ES EL QUE VAA
@uploads_bp.route("/comprobantes", methods=["GET"])
def get_comprobantes():
    try:
        db = next(get_db())

        razon_social_query = comprobantes_cargados_hoy_razon_social()
        result = db.execute(razon_social_query).fetchall()

        razones_sociales = [row.RazonSocial for row in result]
        emails = [row.email for row in result]
        vendedores = [row.Vendedor for row in result]
        codigos = [row.CodigoCliente for row in result]

        if not razones_sociales:
            return "No se encontraron razones sociales con comprobantes cargados hoy.", 404

        return jsonify({"razonesSociales": razones_sociales, "emails": emails, "vendedores": vendedores, "codigos": codigos})

    except Exception as e:
        return f"Error al conectar con la base de datos: {str(e)}", 500
    
@uploads_bp.route("/saldo-acumulado", methods=["GET"])
def get_saldo_acumulado():
    try:
        logger.info("📌 Iniciando consulta de saldo acumulado...")

        db = next(get_db())

        # 📌 Obtener el parámetro clienteCod desde la URL
        cliente_cod = request.args.get("clienteCod")
        if not cliente_cod:
            logger.warning("⚠️ No se proporcionó clienteCod en la solicitud.")
            return jsonify({"error": "Se requiere el parámetro clienteCod"}), 400

        # 📌 Ejecutar la consulta en la vista de Bejerman con filtro por clienteCod
        query = text("SELECT * FROM _DL_PBI_EstadoCtaCte_SaldoAcum WHERE clienteCod = :cliente_cod")
        result = db.execute(query, {"cliente_cod": cliente_cod}).fetchall()

        if not result:
            logger.warning(f"⚠️ No se encontraron registros para ClienteCod: {cliente_cod}")
            return jsonify({"message": "No se encontraron datos para el cliente"}), 404

        # 📌 Convertir cada fila en un diccionario
        datos = [dict(row._mapping) for row in result]  # ✅ Convierte Row en diccionario

        logger.info(f"✅ Se encontraron {len(datos)} registros para ClienteCod: {cliente_cod}")
        return jsonify(datos)

    except Exception as e:
        logger.error(f"❌ Error al obtener saldo acumulado: {str(e)}")
        return jsonify({"error": f"Error al obtener saldo acumulado: {str(e)}"}), 500



@uploads_bp.route("/saldo-acumulado-excel", methods=["GET"])
def get_saldo_acumulado_excel():
    try:
        logger.info("📌 Iniciando generación de Excel para saldo acumulado...")

        db = next(get_db())

        # 📌 Obtener el parámetro clienteCod desde la URL
        cliente_cod = request.args.get("clienteCod")
        if not cliente_cod:
            logger.warning("⚠️ No se proporcionó clienteCod en la solicitud.")
            return jsonify({"error": "Se requiere el parámetro clienteCod"}), 400

        # 📌 Ejecutar la consulta en la vista de Bejerman con filtro por clienteCod
        query = text("SELECT * FROM _DL_PBI_EstadoCtaCte_SaldoAcum WHERE clienteCod = :cliente_cod")
        result = db.execute(query, {"cliente_cod": cliente_cod})

        rows = result.fetchall()
        if not rows:
            logger.warning(f"⚠️ No se encontraron registros para ClienteCod: {cliente_cod}")
            return jsonify({"message": "No se encontraron datos para el cliente"}), 404

        # 📌 Obtener nombres de columnas desde `cursor.description`
        column_names = [col[0] for col in result.cursor.description]

        # 📌 Convertir filas en listas de valores
        data = [list(row) for row in rows]  

        # 📌 Crear un archivo Excel en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # 📌 Escribir encabezados
        for col_num, column_name in enumerate(column_names):
            worksheet.write(0, col_num, column_name)

        # 📌 Escribir los datos
        for row_num, row_data in enumerate(data, start=1):
            for col_num, cell_value in enumerate(row_data):
                worksheet.write(row_num, col_num, cell_value)

        # 📌 Cerrar el workbook
        workbook.close()
        output.seek(0)

        # 📌 Devolver el archivo como una descarga
        logger.info("✅ Excel generado con éxito, enviando archivo...")
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True, download_name=f"SaldoAcumulado_{cliente_cod}.xlsx")

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error al generar Excel: {str(e)}\n{error_trace}")
        return jsonify({"error": f"Error al generar Excel: {str(e)}"}), 500
    
@uploads_bp.route("/comprobantes-con-saldo", methods=["POST"])
def get_comprobantes_con_saldo():
    try:
        db = next(get_db())
        data = request.get_json()
        codigos = data.get("codigos", [])

        if not codigos:
            return jsonify({"error": "No se proporcionaron códigos de clientes"}), 400

        pdf_directory = "./pdfs"

        # 📌 Limpiar la carpeta antes de comenzar
        if os.path.exists(pdf_directory):
            shutil.rmtree(pdf_directory)
        os.makedirs(pdf_directory, exist_ok=True)

        saldos = {}
        for codigo in codigos:
            query = text("""
                SELECT * 
                FROM _DL_PBI_EstadoCtaCte_SaldoAcum 
                WHERE clienteCod = :cliente_cod 
                AND Femision >= DATEADD(DAY, -30, GETDATE())  -- Solo registros de los últimos 30 días
            """)
            
            saldo_result = db.execute(query, {"cliente_cod": codigo}).fetchall()
            saldos[codigo] = [dict(row._mapping) for row in saldo_result] if saldo_result else []

        pdf_files = procesar_json_a_pdf(saldos, pdf_directory)

        zip_filename = os.path.join(pdf_directory, "comprobantes_con_saldo.zip")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for pdf_file in pdf_files:
                zipf.write(pdf_file, os.path.basename(pdf_file))

        response = send_file(zip_filename, as_attachment=True, download_name="comprobantes_con_saldo.zip")

        # 📌 Eliminar la carpeta después de completar la generación
        shutil.rmtree(pdf_directory)

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500
