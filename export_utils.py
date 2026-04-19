"""
export_utils.py
---------------
Salva cada conta extraída como JSON individual e acumula os dados em um
CSV para análise posterior (pandas, Power BI, Excel, etc.).
"""

import os
import json
import csv
from datetime import datetime

STORAGE_DIR = os.environ.get("LOCAL_STORAGE", "storage")
JSON_DIR = os.path.join(STORAGE_DIR, "json")
CSV_PATH = os.path.join(STORAGE_DIR, "bills_data.csv")

# Colunas do CSV — mesmas que os campos de BILL_FIELDS + metadados
CSV_COLUMNS = [
    "arquivo_origem",
    "data_processamento",
    "distribuidora",
    "cpf_cnpj_titular",
    "endereco_titular",
    "numero_instalacao",
    "numero_fatura",
    "mes_referencia",
    "data_vencimento",
    "valor_total",
    "consumo_kwh",
    "leitura_atual",
    "leitura_anterior",
    "bandeira_tarifaria",
    "tipo_fornecimento",
    "classe_consumidor",
    "tarifa_rs_kwh",
]


def save_to_json(bill_data: dict, original_filename: str) -> str:
    """
    Salva o dicionário de dados da conta em um arquivo JSON individual.

    Args:
        bill_data: Dados extraídos e refinados da conta.
        original_filename: Nome do arquivo de origem (para nomear o JSON).

    Returns:
        Caminho do arquivo JSON salvo.
    """
    os.makedirs(JSON_DIR, exist_ok=True)

    # Usa o nome original sem extensão + timestamp para evitar colisões
    base_name = os.path.splitext(original_filename)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{base_name}_{timestamp}.json"
    json_path = os.path.join(JSON_DIR, json_filename)

    output = {
        "arquivo_origem": original_filename,
        "data_processamento": datetime.now().isoformat(),
        "dados": bill_data,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"DEBUG (export_utils): JSON salvo em {json_path}")
    return json_path


def append_to_csv(bill_data: dict, original_filename: str = "desconhecido") -> None:
    """
    Acumula os dados da conta em um CSV único (cria o arquivo se não existir).
    Cada chamada adiciona uma linha ao CSV.

    Args:
        bill_data: Dados extraídos e refinados da conta.
        original_filename: Nome do arquivo de origem.
    """
    os.makedirs(STORAGE_DIR, exist_ok=True)

    file_exists = os.path.exists(CSV_PATH)

    row = {
        "arquivo_origem": original_filename,
        "data_processamento": datetime.now().isoformat(),
    }
    row.update({col: bill_data.get(col, "None") for col in CSV_COLUMNS
                if col not in ("arquivo_origem", "data_processamento")})

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(f"DEBUG (export_utils): Linha adicionada ao CSV {CSV_PATH}")


def load_all_bills() -> list[dict]:
    """
    Carrega todas as contas do CSV como lista de dicionários.
    Útil para análise direta em Python sem pandas.

    Returns:
        Lista de dicts com os dados de todas as contas processadas.
    """
    if not os.path.exists(CSV_PATH):
        return []

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)
