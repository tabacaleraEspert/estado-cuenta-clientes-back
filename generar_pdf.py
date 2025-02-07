from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

def format_money(value):
    """Formatea un número como moneda con separadores de miles y dos decimales"""
    try:
        value = float(value)  # Asegurar que el valor es numérico
        return f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return ""  # Retorna un valor por defecto si el dato no es numérico
    
def generar_pdf(datos, nombre_archivo):
    # Crear el PDF
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    width, height = letter

    # Título principal
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "Estado de Cuenta")
    y_position = height - 70

    # Sección de Negativos
    if "Negativos" in datos and datos["Negativos"]:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y_position, "1- CRÉDITO A FAVOR:")
        y_position -= 20

        # Encabezado de tabla
        c.setFont("Helvetica", 10)
        encabezado = "Emisión      Comprobante     Vto      Mora      Condición de Venta       Total $       Saldo $"
        c.drawString(30, y_position, encabezado)
        y_position -= 10
        c.line(30, y_position, width - 30, y_position)  # Línea separadora
        y_position -= 15

        for item in datos["Negativos"]:
            fecha = item["Fecha"][:10]  # Formatear fecha YYYY-MM-DD
            comp_nro = item.get("Comp_Nro", "")
            tipo = item.get("Comp_tipo", "")
            vto = item["Fecha_vto"][:10]
            cond_venta = item.get("CondVta", "")
            total_loc = format_money(item["Total_Loc"])
            saldo_loc = format_money(item["Saldo_Loc"])

            # Agregar datos a la tabla
            texto = f"{fecha}  {tipo} {comp_nro} {vto}  {cond_venta} {total_loc:>15} {saldo_loc:>15}"
            for line in simpleSplit(texto, "Helvetica", 10, width - 60):
                c.drawString(30, y_position, line)
                y_position -= 15

        c.line(30, y_position, width - 30, y_position)  # Línea separadora
        y_position -= 15

        # Total crédito a favor
        credito_a_favor = format_money(datos["Crédito a favor (Total_Loc negativos)"])
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 30, y_position, f"Total 1- CRÉDITO A FAVOR: {credito_a_favor}")
        y_position -= 25

    # Sección de Vencidos
    if "Vencidos" in datos and datos["Vencidos"]:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y_position, "2- VENCIDOS:")
        y_position -= 20

        for item in datos["Vencidos"]:
            fecha = item["Fecha"][:10]
            comp_nro = item.get("Comp_Nro", "")
            tipo = item.get("Comp_tipo", "")
            vto = item["Fecha_vto"][:10]
            cond_venta = item.get("CondVta", "")
            total_loc = format_money(["Total_Loc"])
            saldo_loc = format_money(item["Saldo_Loc"])

            texto = f"{fecha}  {tipo} {comp_nro} {vto}  {cond_venta} {total_loc:>15} {saldo_loc:>15}"
            for line in simpleSplit(texto, "Helvetica", 10, width - 60):
                c.drawString(30, y_position, line)
                y_position -= 15

        c.line(30, y_position, width - 30, y_position)
        y_position -= 15

        total_vencidos = format_money(datos["Total vencidos"])
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 30, y_position, f"Total 2- VENCIDO: {total_vencidos}")
        y_position -= 25

    # Total general
    total_global = format_money(datos["Total global"])
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y_position, f"Total {datos['Razon Social']}: {total_global}")

    # Finalizar PDF
    c.save()
    print(f"PDF generado correctamente: {nombre_archivo}")

# 📌 Ejemplo de uso con los datos de prueba
datos_prueba = {
    "Razon Social": "VIGLIETTI CARLOS JAVIER",
    "Crédito a favor (Total_Loc negativos)": -1846000,
    "Total vencidos": 4165000,
    "Total a vencer": 0,
    "Total global": 2319000,
    "Negativos": [
        {
            "Fecha": "2025-01-17T00:00:00.000Z",
            "Fecha_vto": "2025-01-17T00:00:00.000Z",
            "Comp_Nro": "00125077",
            "Comp_tipo": "RC",
            "CondVta": "6 Días",
            "Total_Loc": -1930000,
            "Saldo_Loc": -1846000,
        }
    ],
    "Vencidos": [
        {
            "Fecha": "2025-01-21T00:00:00.000Z",
            "Fecha_vto": "2025-01-21T00:00:00.000Z",
            "Comp_Nro": "00045152",
            "Comp_tipo": "XFC",
            "CondVta": "6 Días",
            "Total_Loc": 824000,
            "Saldo_Loc": 824000,
        }
    ],
}

# 📌 Generar PDF de prueba
generar_pdf(datos_prueba, "estado_cuenta.pdf")
