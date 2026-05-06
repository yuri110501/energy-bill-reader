import os
import pprint
from dotenv import load_dotenv

load_dotenv()

from ocr_utils import extract_text
from text_utils import preprocess_text, extract_bill_data, validate_cpf_cnpj
from refinement_utils import refine_data_local, replace_null_with_none

def test_pipeline(pdf_path):
    print(f"Processando {pdf_path}...")
    
    # 1. OCR
    extracted_text = extract_text(pdf_path)
    processed_text = preprocess_text(extracted_text)
    
    # 2. Salva o texto bruto para análise
    with open("raw_ocr_text.txt", "w", encoding="utf-8") as f:
        f.write(extracted_text)
    
    # Regex Extraction
    bill_data_raw = extract_bill_data(extracted_text)
    bill_data_processed = extract_bill_data(processed_text)
    
    bill_data = {
        key: bill_data_raw.get(key) or bill_data_processed.get(key)
        for key in bill_data_raw
    }

    print("\n--- Dados Extraidos via Regex ---")
    pprint.pprint(bill_data)
    
    # 3. Refinamento (IA / Fallback) - DESATIVADO PARA TESTE DE REGEX
    refined_data = refine_data_local(bill_data, extracted_text, processed_text)
    
    # Validando CPF/CNPJ nos dados do Regex
    if not validate_cpf_cnpj(refined_data.get("cpf_cnpj_titular", "")):
        refined_data["cpf_cnpj_titular"] = "CPF/CNPJ inválido/não encontrado"

    final_data = replace_null_with_none(refined_data)

    print("\n--- Dados Finais (Com Refinamento) ---")
    pprint.pprint(final_data)

if __name__ == "__main__":
    files = [
        r"Contas\TOYOLEX IMB MÊS 02.pdf",
        r"Contas\TOYOLEX IMBI CELPE MÊS 01.pdf",
        r"Contas\toyolex imbiribeira agosto.pdf"
    ]
    for pdf in files:
        test_pipeline(pdf)
        print("-" * 50)
