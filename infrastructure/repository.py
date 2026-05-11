"""
repository.py
-------------
Camada de persistência de dados. Abstrai a lógica de salvamento (JSON, CSV, e futuro MongoDB).
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List

STORAGE_DIR = os.environ.get("LOCAL_STORAGE", "storage")
JSON_DIR = os.path.join(STORAGE_DIR, "json")
CSV_PATH = os.path.join(STORAGE_DIR, "bills_data.csv")

# Colunas padrão para o CSV baseadas no modelo BillData
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
    "consumo_total_kwh",
    "leitura_atual",
    "leitura_anterior",
    "bandeira_tarifaria",
    "tipo_fornecimento",
    "classe_consumidor",
    "tarifa_rs_kwh",
]

class BillRepository:
    """
    Repositório para gerenciar a persistência das faturas.
    """
    
    @staticmethod
    def save_to_json(bill_data: Dict[str, Any], original_filename: str) -> str:
        """Salva os dados em formato JSON."""
        os.makedirs(JSON_DIR, exist_ok=True)

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

        print(f"DEBUG (repository): JSON salvo em {json_path}")
        return json_path

    @staticmethod
    def append_to_csv(bill_data: Dict[str, Any], original_filename: str = "desconhecido") -> None:
        """Acumula os dados em um CSV único, evitando duplicatas."""
        os.makedirs(STORAGE_DIR, exist_ok=True)
        file_exists = os.path.exists(CSV_PATH)

        # Verificação de duplicidade por número da fatura ou arquivo_origem
        is_duplicate = False
        if file_exists:
            numero_fatura = bill_data.get("numero_fatura", "None")
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for existing_row in reader:
                    # Se tiver numero_fatura válido e for igual, é duplicata
                    if numero_fatura != "None" and existing_row.get("numero_fatura") == numero_fatura:
                        is_duplicate = True
                        break
                    # Alternativamente, se o arquivo tiver o mesmo nome
                    if existing_row.get("arquivo_origem") == original_filename:
                        is_duplicate = True
                        break

        if is_duplicate:
            print(f"DEBUG (repository): Registro duplicado ignorado para o arquivo {original_filename}")
            return

        row = {
            "arquivo_origem": original_filename,
            "data_processamento": datetime.now().isoformat(),
        }
        
        # Preenche os dados baseados no modelo (usando 'None' se vazio)
        row.update({col: bill_data.get(col, "None") for col in CSV_COLUMNS
                    if col not in ("arquivo_origem", "data_processamento")})

        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"DEBUG (repository): Linha adicionada ao CSV {CSV_PATH}")

    @staticmethod
    def save_to_mongodb(bill_data: Dict[str, Any], original_filename: str) -> None:
        """
        [FUTURO] Implementação para salvar dados no MongoDB.
        """
        # Exemplo de implementação futura:
        # collection = get_mongo_collection("energy_bills")
        # document = {"arquivo_origem": original_filename, "data_processamento": datetime.utcnow(), **bill_data}
        # collection.insert_one(document)
        print("DEBUG (repository): [STUB] Salvando no MongoDB...")
        pass

    @staticmethod
    def save_all(bill_data: Dict[str, Any], original_filename: str) -> str:
        """Salva a fatura em todos os locais configurados e retorna o caminho do JSON."""
        json_path = BillRepository.save_to_json(bill_data, original_filename)
        BillRepository.append_to_csv(bill_data, original_filename)
        # BillRepository.save_to_mongodb(bill_data, original_filename)
        return json_path

    @staticmethod
    def get_all_from_csv() -> List[Dict[str, Any]]:
        """Carrega todas as contas do CSV para análise."""
        if not os.path.exists(CSV_PATH):
            return []
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
