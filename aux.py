import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def procesar_json_a_pdf(datos_json, pdf_directory):
    """
    Procesa datos en formato JSON y genera PDFs en el directorio especificado.
    
    Parámetros:
    - datos_json (dict): Diccionario con los datos del estado de cuenta por cliente.
    - pdf_directory (str): Directorio donde se guardarán los PDFs.

    Retorna:
    - Lista de rutas de los PDFs generados.
    """

    if not datos_json:
        raise ValueError("❌ No se recibieron datos JSON para procesar.")

    os.makedirs(pdf_directory, exist_ok=True)

    def format_money(val):
        """Convierte números en formato monetario con puntos y comas, asegurando dos decimales"""
        try:
            num = round(float(val), 2)  
            return f"{num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "0,00"  

    def replace_comprobante(value):
        """Reemplaza tipos de comprobante con nombres más cortos"""
        value = str(value).strip()
        replacements = {
            "FC A": "FC", "XFC X": "FC",
            "RC R": "RC", "XRC": "RC",
            "NC A": "NC", "XNC X": "NC",
            "NDA A": "ND", "XND X": "ND"
        }
        for key, new_value in replacements.items():
            if value.startswith(key):
                return new_value + value[len(key):]
        return value

    pdf_files = []

    for cliente_cod, registros in datos_json.items():
        if not registros:
            continue  # 🔹 Si no hay datos para el cliente, salta al siguiente

        df = pd.DataFrame(registros)  # Convertir la lista de registros en un DataFrame

        df["ComprobanteNro"] = df["ComprobanteNro"].astype(str).apply(replace_comprobante)
        df = df.sort_values(by=["Femision"])

        # 📌 Verificar si las columnas necesarias existen
        required_columns = ["Femision", "ComprobanteNro", "FechaVto", "CondVta", "Debe_Loc", "Haber_Loc", "SaldoAcum_Loc"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ ERROR: Las siguientes columnas faltan en los datos: {missing_columns}")
            continue  

        # 📌 Mapear nombres de columnas para el PDF
        column_mappings = {
            "Femision": "Fecha",
            "ComprobanteNro": "Comprobante Nro",
            "FechaVto": "Vto.",
            "CondVta": "Cond. Venta",
            "Debe_Loc": "Debe",
            "Haber_Loc": "Haber",
            "SaldoAcum_Loc": "Saldo"
        }
        new_header = [column_mappings[col] for col in required_columns]
        def prepare_data_rows(df_source):
            """Formatea las filas con formato monetario y convierte fechas a dd/mm/aaaa"""
            
            # 📌 Convertir las columnas de fecha al formato dd/mm/aaaa
            date_columns = ["Femision", "FechaVto"]
            for col in date_columns:
                if col in df_source.columns:
                    df_source[col] = pd.to_datetime(df_source[col], errors='coerce').dt.strftime("%d/%m/%Y")

            # 📌 Convertir las columnas numéricas a formato decimal
            for col in ["Debe_Loc", "Haber_Loc", "SaldoAcum_Loc"]:
                df_source[col] = pd.to_numeric(df_source[col], errors="coerce")

            data_rows = df_source[required_columns].values.tolist()

            for row in data_rows:
                for i in [4, 5, 6]:  # Índices de las columnas Debe, Haber, Saldo
                    if i == 6 and (row[i] == 0 or pd.isna(row[i])):  
                        row[i] = "0,00"  # 🔹 Mantiene "0,00" en la columna 6 cuando es 0 o NaN
                    else:
                        row[i] = format_money(row[i]) if row[i] and not pd.isna(row[i]) else ""

            return data_rows

        data_rows = prepare_data_rows(df)

        # 📌 Generar PDF
        razon_social = registros[0]["RazonSocial"] if registros else f"Cliente_{cliente_cod}"
        sanitized_razon = razon_social.replace("/", "_").replace("\\", "_").replace(" ", "_")
        pdf_file = os.path.join(pdf_directory, f"{sanitized_razon}.pdf")
        pdf_files.append(pdf_file)

        # Crear encabezados
        styles = getSampleStyleSheet()
        p_date = Paragraph(datetime.today().strftime("%d/%m/%Y"), styles["Normal"])
        p_title = Paragraph(f"Estado de Cuenta - {razon_social}", styles["Title"])

        # Crear tabla de encabezado
        header_table_data = [new_header]
        header_table = Table(header_table_data, colWidths=[80] * len(new_header))
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]))

        # Crear tabla de datos
        data_table = Table(data_rows, colWidths=[80] * len(new_header))
        data_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
    # 📌 Resaltar el último valor de la columna "Saldo"
        if data_rows:
            last_row_index = len(data_rows) - 1  # Índice de la última fila
            saldo_column_index = new_header.index("Saldo")  # Posición de la columna Saldo

            data_table.setStyle(TableStyle([
                ('BOX', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), 2, colors.red),  # Marco rojo
                ('BACKGROUND', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), colors.yellow),  # Fondo amarillo
                ('FONTNAME', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), 'Helvetica-Bold'),  # Texto en negrita
                ('TEXTCOLOR', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), colors.black),  # Texto en negro
            ]))

        # Crear documento PDF
        doc = SimpleDocTemplate(pdf_file, pagesize=landscape(letter))
        elements = [p_date, Spacer(1, 12), p_title, Spacer(1, 12), header_table, Spacer(1, 12), data_table]
        doc.build(elements)

        print(f"✅ PDF generado: {pdf_file}")

    print("🎉 Proceso finalizado. PDFs generados correctamente.")
    return pdf_files  





