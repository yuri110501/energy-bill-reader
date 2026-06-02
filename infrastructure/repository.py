"""
repository.py
-------------
Camada de persistência de dados. Abstrai a lógica de salvamento (JSON, CSV, e futuro MongoDB).
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.models import BillData

STORAGE_DIR = os.environ.get("LOCAL_STORAGE", "storage")
JSON_DIR = os.path.join(STORAGE_DIR, "json")
CSV_PATH = os.path.join(STORAGE_DIR, "bills_data.csv")

# Colunas dinâmicas baseadas no modelo BillData + metadados de auditoria
# Isso garante que a ordem do CSV seja SEMPRE a mesma do JSON definido no modelo.
def get_csv_columns() -> List[str]:
    audit_fields = ["arquivo_origem", "data_processamento"]
    model_fields = list(BillData.model_fields.keys())
    
    # 1. Identifica a nomenclatura usada no modelo (ID_sof ou id_sof)
    sof_field = "ID_sof" if "ID_sof" in model_fields else "id_sof"
    
    # 2. Se o campo existir, remove da lista de modelos e posiciona no início absoluto do retorno
    if sof_field in model_fields:
        model_fields.remove(sof_field)
        return [sof_field] + audit_fields + model_fields
        
    return audit_fields + model_fields


class BillRepository:
    """
    Repositório para gerenciar a persistência das faturas.
    """
    
    @staticmethod
    def save_to_json(bill_data: Dict[str, Any], original_filename: str, processed_pdf_path: Optional[str] = None) -> str:
        """Salva os dados em formato JSON."""
        os.makedirs(JSON_DIR, exist_ok=True)

        base_name = os.path.splitext(original_filename)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"{base_name}_{timestamp}.json"
        json_path = os.path.join(JSON_DIR, json_filename)

        output = {
            "arquivo_origem": original_filename,
            "processed_pdf_path": processed_pdf_path if processed_pdf_path is not None else "None",
            "data_processamento": datetime.now().isoformat(),
            "dados": bill_data,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"DEBUG (repository): JSON salvo em {json_path}")
        return json_path

    @staticmethod
    def append_to_csv(bill_data: Dict[str, Any], original_filename: str = "desconhecido") -> None:
        """
        Acumula os dados em um CSV único. 
        Filtro de duplicidade removido para permitir histórico de extrações.
        """
        os.makedirs(STORAGE_DIR, exist_ok=True)
        file_exists = os.path.exists(CSV_PATH)
        columns = get_csv_columns()

        # Monta a linha para o CSV
        row = {
            "arquivo_origem": original_filename,
            "data_processamento": datetime.now().isoformat(),
        }
        
        # Preenche os dados baseados no dicionário recebido (que segue o modelo BillData)
        for col in BillData.model_fields.keys():
            val = bill_data.get(col)
            row[col] = val if val is not None else "None"

        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"DEBUG (repository): Linha adicionada ao CSV {CSV_PATH}")

    @staticmethod
    def save_all(bill_data: Dict[str, Any], original_filename: str, processed_pdf_path: Optional[str] = None) -> str:
        """Salva a fatura em todos os locais configurados."""
        json_path = BillRepository.save_to_json(bill_data, original_filename, processed_pdf_path=processed_pdf_path)
        BillRepository.append_to_csv(bill_data, original_filename)
        return json_path

    @staticmethod
    def get_all_from_csv() -> List[Dict[str, Any]]:
        """Carrega todas as contas do CSV para análise."""
        if not os.path.exists(CSV_PATH):
            return []
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
