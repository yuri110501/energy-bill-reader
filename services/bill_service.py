"""
bill_service.py
---------------
Camada de Orquestração (Service). 
Coordena o fluxo de processamento: Ingestão (OCR) -> Extração (Regex) -> Refinamento (IA) -> Persistência.
"""

import os
from typing import Dict, Any, Tuple

from infrastructure.ocr import extract_text
from core.extraction import preprocess_text, extract_bill_data
from core.refinement import refine_data
from infrastructure.repository import BillRepository

class BillService:
    """
    Serviço principal para processamento de faturas de energia.
    """

    @staticmethod
    def process_file(file_path: str) -> Tuple[Dict[str, Any], str]:
        """
        Processa uma única fatura e a salva nos repositórios configurados.
        
        Args:
            file_path: Caminho absoluto para o arquivo (PDF/Imagem).
            
        Returns:
            Tupla (Dados processados em formato dict, Caminho do JSON salvo).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        filename = os.path.basename(file_path)
        print(f"\n--- Iniciando processamento: {filename} ---")

        # 1. OCR (Ingestão)
        raw_text = extract_text(file_path)
        if not raw_text.strip():
            raise ValueError(f"Não foi possível extrair texto de {filename}.")

        # 2. Pré-processamento e Extração inicial (Core Regex)
        processed_text = preprocess_text(raw_text)
        initial_data = extract_bill_data(processed_text)

        # 3. Refinamento (Core IA + Business Rules)
        # Retorna o modelo Pydantic validado
        refined_model = refine_data(initial_data, raw_text, processed_text)
        
        # Converte o modelo de volta para dict flat (usando strings para None) para persistência
        final_dict = refined_model.to_flat_dict()

        # 4. Persistência (Infrastructure)
        json_path = BillRepository.save_all(final_dict, filename)

        return final_dict, json_path

    @staticmethod
    def get_all_bills() -> list[Dict[str, Any]]:
        """Retorna todas as faturas já processadas."""
        return BillRepository.get_all_from_csv()
