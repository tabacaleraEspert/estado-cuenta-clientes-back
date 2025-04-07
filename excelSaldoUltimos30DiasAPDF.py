import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def procesar_excel_a_pdf(excel_file, pdf_directory, razones_sociales_permitidas):
    """
    Procesa un archivo Excel y genera PDFs en el directorio especificado.
    
    Parámetros:
    - excel_file (str): Ruta al archivo Excel.
    - pdf_directory (str): Directorio donde se guardarán los PDFs.
    - razones_sociales_permitidas (list): Lista de razones sociales a incluir en el PDF.

    Retorna:
    - Lista de rutas de los PDFs generados.
    """
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"❌ Archivo no encontrado: {excel_file}")

    os.makedirs(pdf_directory, exist_ok=True)

    def format_money(val):
        """Convierte números en formato monetario con puntos y comas, asegurando dos decimales"""
        try:
            num = round(float(val), 2)  # 🔹 Asegurar que solo tenga dos decimales
            s = f"{num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            print(f"📌 Valor original: {val} | Convertido: {num} | Formateado: {s}")  # 🔹 Ver valores en la terminal
            
            return s
        except Exception as e:
            print(f"⚠️ Error en format_money() - Valor problemático: {val} | Error: {e}")
            return "0,00"  # 🔹 Devolver un valor seguro en caso de error


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

    df = pd.read_excel(excel_file)

    # Obtener todas las razones sociales del Excel antes de filtrar
    razones_sociales_originales = set(df['RazonSocial'].unique())

    # Filtrar razones sociales permitidas
    df = df[df['RazonSocial'].isin(razones_sociales_permitidas)]

    # Obtener las razones sociales después del filtrado
    razones_sociales_filtradas = set(df['RazonSocial'].unique())
    
    razones_sociales_excluidas = razones_sociales_originales - razones_sociales_filtradas

    # Obtener lista de razones sociales únicas después del filtrado
    razones_sociales = df['RazonSocial'].unique()

    pdf_files = []
    print("📌 Vista previa de la columna 'SaldoAcum_Loc' antes de procesar:")
    print(df["SaldoAcum_Loc"])  # Muestra los primeros 10 valores de la columna


    for razon_social in razones_sociales:
        print(f"\n📌 Procesando razón social: {razon_social}")

        df_filtered = df[df['RazonSocial'] == razon_social].copy()
        print(f"📌 Total registros después de filtrar por '{razon_social}': {len(df_filtered)}")

        df_filtered = df_filtered.sort_values(by=['Femision'])  # Ordenar por fecha

        # 📌 Verificar si las columnas existen antes de seleccionar
        missing_columns = [col for col in ["Femision", "ComprobanteNro", "FechaVto", "CondVta", "Debe_Loc", "Haber_Loc", "SaldoAcum_Loc"] if col not in df_filtered.columns]
        if missing_columns:
            print(f"❌ ERROR: Las siguientes columnas no están en el DataFrame: {missing_columns}")
            continue  # Salta a la siguiente razón social

        # 📌 Definir columnas de interés
        columns_of_interest = ["Femision", "ComprobanteNro", "FechaVto", "CondVta", "Debe_Loc", "Haber_Loc", "SaldoAcum_Loc"]
        df_filtered = df_filtered[columns_of_interest]

        print("\n📌 Vista previa de datos después del filtrado:")
        print(df_filtered.head(5))

        # 📌 Verificar si la columna "SaldoAcum_Loc" tiene valores correctos
        print("\n📌 Vista previa de 'SaldoAcum_Loc' después del filtrado:")
        print(df_filtered["SaldoAcum_Loc"].head(10))

        # 📌 Aplicar reemplazos a la columna "ComprobanteNro"
        df_filtered["ComprobanteNro"] = df_filtered["ComprobanteNro"].astype(str).apply(replace_comprobante)
        print("\n📌 Vista previa de 'ComprobanteNro' después de aplicar reemplazo:")
        print(df_filtered["ComprobanteNro"].head(10))

        # 📌 Separar los datos en dos partes
        mask_part2 = df_filtered["ComprobanteNro"].str.contains("RT R", na=False)
        df_part2 = df_filtered[mask_part2]
        df_part1 = df_filtered[~mask_part2]  # 🔹 Corregido, antes estaba `df_filtered[mask_part2]` dos veces

        print("\n📌 Registros en Parte 1 (Deuda en Cta Cte):", len(df_part1))
        print("📌 Registros en Parte 2 (Remitos pendientes de facturar):", len(df_part2))

        # 📌 Vista previa de "SaldoAcum_Loc" en cada parte
        print("\n📌 'SaldoAcum_Loc' en Parte 1 (Deuda en Cta Cte):")
        print(df_part1["SaldoAcum_Loc"].head(5))

        print("\n📌 'SaldoAcum_Loc' en Parte 2 (Remitos pendientes de facturar):")
        print(df_part2["SaldoAcum_Loc"].head(5))

        
        # df_filtered = df[df['RazonSocial'] == razon_social].copy()
        # df_filtered = df_filtered.sort_values(by=['Femision'])  # Ordenar por fecha

        # # 📌 Definir columnas de interés
        # columns_of_interest = ["Femision", "ComprobanteNro", "FechaVto", "CondVta", "Debe_Loc", "Haber_Loc", "SaldoAcum_Loc"]
        # df_filtered = df_filtered[columns_of_interest]
        
        #   # Aplicar reemplazos
        # df_filtered["ComprobanteNro"] = df_filtered["ComprobanteNro"].astype(str).apply(replace_comprobante)
        
        # # Separar los datos en dos partes
        # mask_part2 = df_filtered["ComprobanteNro"].str.contains("RT R", na=False)
        # df_part2 = df_filtered[mask_part2]
        # df_part1 = df_filtered[mask_part2]

        # 📌 Mapear nombres de columnas
        header_mapping = {
            "Femision": "Fecha",
            "ComprobanteNro": "Comprobante Nro",
            "FechaVto": "Vto.",
            "CondVta": "Cond. Venta",
            "Debe_Loc": "Debe",
            "Haber_Loc": "Haber",
            "SaldoAcum_Loc": "Saldo"
        }
        new_header = [header_mapping[col] for col in columns_of_interest]

        def prepare_data_rows(df_source):
            """Formatea las filas de datos con formato monetario y reemplaza valores nulos o 0"""
            
            # 📌 Convertir las columnas a número (forzando `NaN` en valores no válidos)
            for col in ["Debe_Loc", "Haber_Loc", "SaldoAcum_Loc"]:
                df_source[col] = pd.to_numeric(df_source[col], errors="coerce")  # Convierte a número, `NaN` si falla

            print("\n📌 Vista previa después de convertir columnas a número:")
            print(df_source[["Debe_Loc", "Haber_Loc", "SaldoAcum_Loc"]].head(10))  # Verifica la conversión
            
                # 📌 Extraer parte numérica del comprobante para ordenar
            df_source["ComprobanteNro_Num"] = (
                df_source["ComprobanteNro"]
                .astype(str)
                .str.extract(r"(\d{6,})")[0]
                .astype(float)
            )

            # 📌 Ordenar por fecha y número de comprobante si se pudo extraer
            if df_source["ComprobanteNro_Num"].notna().any():
                df_source = df_source.sort_values(by=["Femision", "ComprobanteNro_Num"])
            else:
                df_source = df_source.sort_values(by=["Femision"])

            data_rows = df_source.values.tolist()

            for row in data_rows:
                for i in [4, 5, 6]:  # Índices de columnas: Debe (4), Haber (5), Saldo (6)
                    try:
                        if pd.isna(row[i]) or float(row[i]) == 0:
                            row[i] = ""  # 🔹 Ahora muestra "0,00" en lugar de vacío
                        else:
                            row[i] = format_money(row[i])
                    except Exception as e:
                        print(f"⚠️ Error en formato de datos: {e} | Valor problemático: {row[i]}")
                        row[i] = "0,00"  # 🔹 Valor por defecto si hay error

            df_source.drop(columns=["ComprobanteNro_Num"], inplace=True)

            return data_rows


        data_rows_part1 = prepare_data_rows(df_part1)
        data_rows_part2 = prepare_data_rows(df_part2)
        
        # 📌 Generar PDF
        sanitized_razon = razon_social.replace("/", "_").replace("\\", "_").replace(" ", "_")
        pdf_file = os.path.join(pdf_directory, f"{sanitized_razon}.pdf")
        pdf_files.append(pdf_file)

        # Encabezado general
        razon_row = [razon_social] + [""] * (len(new_header) - 1)
        global_header_data = [new_header, razon_row]
        

        doc_temp = SimpleDocTemplate(pdf_file, pagesize=landscape(letter))
        num_cols = len(new_header)
        col_width = doc_temp.width / num_cols
        global_header_table = Table(global_header_data, colWidths=[col_width] * num_cols)
        
        header_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('SPAN', (0, 1), (-1, 1)), 
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ])
        global_header_table.setStyle(header_style)

        
        def create_data_table(data_rows):
            """Crea tablas sin líneas de separación"""
            if len(data_rows) == 0:
                return None
            table = Table(data_rows, colWidths=[col_width] * num_cols)
            table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            return table

        table_part1 = create_data_table(data_rows_part1)
        table_part2 = create_data_table(data_rows_part2)

        # Crear títulos
        styles = getSampleStyleSheet()
        p_date = Paragraph(datetime.today().strftime("%d/%m/%Y"), styles["Normal"])
        p_title = Paragraph("Estado cuenta corriente (últimos 30 días)", styles["Title"])
        part1_title = Paragraph("1 Deuda en Cta Cte", styles["Heading2"])
        part2_title = Paragraph("2 Remitos pendientes de facturar - Valor estimado", styles["Heading2"])

        # Generar PDF
        doc = SimpleDocTemplate(pdf_file, pagesize=landscape(letter))
        
        if table_part1 and len(data_rows_part1) > 0:
            last_row_index = len(data_rows_part1) - 1
            saldo_column_index = new_header.index("Saldo")  # Obtiene la posición de la columna Saldo

            table_part1.setStyle(TableStyle([
                ('BOX', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), 2, colors.red),  # Marco rojo
                ('BACKGROUND', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), colors.yellow),  # Fondo amarillo
                ('FONTNAME', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), 'Helvetica-Bold'),  # Texto en negrita
                ('TEXTCOLOR', (saldo_column_index, last_row_index), (saldo_column_index, last_row_index), colors.black),  # Texto en negro
            ]))
        
        elements = [p_date, Spacer(1, 12), p_title, Spacer(1, 12), global_header_table]

        if table_part1:
            elements += [Spacer(1, 24), part1_title, Spacer(1, 12), table_part1]
        if table_part2:
            elements += [Spacer(1, 24), part2_title, Spacer(1, 12), table_part2]

        doc.build(elements)
        # print(f"✅ PDF generado: {pdf_file}")

    print("🎉 Proceso finalizado. PDFs generados correctamente.")
    return pdf_files  # ✅ Ahora devuelve la lista de PDFs generados
