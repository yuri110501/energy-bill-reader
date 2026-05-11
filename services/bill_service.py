"""
bill_service.py
---------------
Camada de Orquestração (Service).
Coordena o fluxo: Ingestão (OCR+Tabelas) → Extração Estruturada → [IA opcional] → Persistência.

A IA só é acionada quando o score de confiança da extração estruturada for < 0.5,
reduzindo o consumo de tokens ao mínimo necessário.
"""

import os
from typing import Dict, Any, Tuple

from infrastructure.ocr import extract_structured
from core.extraction import extract_bill_data, preprocess_text
from core.refinement import refine_data
from infrastructure.repository import BillRepository

# Threshold abaixo do qual a IA é acionada como fallback
AI_CONFIDENCE_THRESHOLD = float(os.environ.get("AI_CONFIDENCE_THRESHOLD", "0.5"))


class BillService:
    """
    Serviço principal para processamento de faturas de energia.
    """

    @staticmethod
    def process_file(file_path: str) -> Tuple[Dict[str, Any], str]:
        """
        Processa uma única fatura e a salva nos repositórios configurados.

        Fluxo:
          1. OCR + extração de tabelas (pdfplumber ou Tesseract)
          2. Extração estruturada via tabelas + regex direcionado
          3. IA (Gemini) apenas se confiança < threshold configurável
          4. Persistência (JSON + CSV)

        Args:
            file_path: Caminho absoluto para o arquivo (PDF/Imagem).

        Returns:
            Tupla (dados_processados: dict, caminho_json: str).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        filename = os.path.basename(file_path)
        print(f"\n--- Iniciando processamento: {filename} ---")

        # 1. Extração de texto + tabelas estruturadas
        raw_text, tables = extract_structured(file_path)
        if not raw_text.strip():
            raise ValueError(f"Não foi possível extrair texto de {filename}.")

        # 2. Extração estruturada (tabelas + regex direcionado)
        initial_data, confidence = extract_bill_data(raw_text, tables)

        # 3. Refinamento por IA — apenas se a extração estruturada for insuficiente
        if confidence < AI_CONFIDENCE_THRESHOLD:
            print(
                f"DEBUG (service): Confiança {confidence:.2f} < {AI_CONFIDENCE_THRESHOLD} "
                f"-> acionando IA para completar campos ausentes."
            )
            processed_text = preprocess_text(raw_text)
            refined_model = refine_data(initial_data, raw_text, processed_text)
            final_dict = refined_model.to_flat_dict()
        else:
            print(
                f"DEBUG (service): Confiança {confidence:.2f} >= {AI_CONFIDENCE_THRESHOLD} "
                f"-> extração local suficiente, IA não acionada. [OK]"
            )
            # Converte para BillData para garantir consistência do schema
            from core.models import BillData
            final_dict = BillData.from_raw_dict(initial_data).to_flat_dict()

        # 4. Persistência
        json_path = BillRepository.save_all(final_dict, filename)

        return final_dict, json_path

    @staticmethod
    def get_all_bills() -> list[Dict[str, Any]]:
        """Retorna todas as faturas já processadas."""
        return BillRepository.get_all_from_csv()
