import os
import pprint
from dotenv import load_dotenv

load_dotenv()

from infrastructure.ocr import extract_text
from core.extraction import preprocess_text, extract_bill_data
from core.refinement import refine_data
from utils.validators import validate_cpf_cnpj

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
    
    # 3. Refinamento (IA / Fallback)
    refined_model = refine_data(bill_data, extracted_text, processed_text)
    
    # Converte de volta para dicionário para exibição e validação do CPF
    refined_data = refined_model.to_flat_dict()
    
    if not validate_cpf_cnpj(refined_data.get("cpf_cnpj_titular", "")):
        refined_data["cpf_cnpj_titular"] = "CPF/CNPJ inválido/não encontrado"

    print("\n--- Dados Finais (Com Refinamento) ---")
    pprint.pprint(refined_data)

if __name__ == "__main__":
    files = [
        r"Contas\TOYOLEX IMB MÊS 02.pdf",
        r"Contas\TOYOLEX IMBI CELPE MÊS 01.pdf",
        r"Contas\toyolex imbiribeira agosto.pdf"
    ]
    for pdf in files:
        if os.path.exists(pdf):
            test_pipeline(pdf)
            print("-" * 50)
        else:
            print(f"Arquivo não encontrado: {pdf}")

