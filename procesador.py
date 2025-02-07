import json
from datetime import datetime

def procesar_resultados(razon_social, data):
    print("Datos a procesar:", json.dumps(data, indent=2)) 
    today = datetime.today()  # Fecha actual

    # Obtener el primer vendedor no vacío
    vendedor = next((item["Vendedor"] for item in data if item.get("Vendedor")), "")

    # 1. Filtrar objetos con "Saldo_Loc" distinto de 0
    filtered_data = [item for item in data if item.get("Saldo_Loc", 0) != 0]

    # 2. Dividir en negativos y positivos
    negatives = [item for item in filtered_data if item["Saldo_Loc"] < 0]
    positives = [item for item in filtered_data if item["Saldo_Loc"] >= 0]

    # 3. Sumarizar los "Total_Loc" negativos como "Crédito a favor"
    credito_a_favor = sum(item["Saldo_Loc"] for item in negatives)

    # 4. Dividir los positivos en vencido y a vencer, y sumarizar
    vencidos = [item for item in positives if datetime.strptime(item["Fecha_vto"], "%Y-%m-%d") < today]
    a_vencer = [item for item in positives if datetime.strptime(item["Fecha_vto"], "%Y-%m-%d") >= today]

    total_vencidos = sum(item["Saldo_Loc"] for item in vencidos)
    total_a_vencer = sum(item["Saldo_Loc"] for item in a_vencer)

    total = round(sum(item["Saldo_Loc"] for item in filtered_data), 2)  # Sumar y redondear a 2 decimales

    # Crear un diccionario con los resultados
    resultados = {
        "Razon Social": razon_social,
        "Crédito a favor (Total_Loc negativos)": credito_a_favor,
        "Total vencidos": total_vencidos,
        "Total a vencer": total_a_vencer,
        "Total global": total,
        "Vendedor": vendedor,
        "Negativos": negatives,
        "Vencidos": vencidos,
        "A Vencer": a_vencer,
    }

    # Escribir los resultados en un archivo JSON
    output_file_path = "resultados.json"
    with open(output_file_path, "w", encoding="utf-8") as json_file:
        json.dump(resultados, json_file, indent=2, ensure_ascii=False)

    print(f"Resultados guardados en el archivo: {output_file_path}")
    return resultados
