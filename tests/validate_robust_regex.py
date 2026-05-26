import os
import re
import pdfplumber
import json

# Versões robustas dos padrões (Melhoria sugerida)
ROBUST_PATTERNS = {
    "geracao_kwh": r"Energia\s+injetada\s+no\s+mes\s+([\d.,]+)",
    "demanda_ativa": r"Demanda\s+Ativa(?:\(?kW\)?|\s+kW)\s+([\d.,]+)",
    "demanda_reativa_excedente": r"Demanda\s+Reativa\s+Exc\w*\.?\s*\(?kVAr\)?\s+([\d.,]+)",
    "consumo_reativo_exc_na_ponta": r"(?:Cons\.?Reat\.?Exc\.?NPonta\s+kVARh|Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\))\s+([\d.,]+)",
    "consumo_reativo_exc_fora_ponta": r"(?:Cons\.?Reat\s*Exc\.?FPonta\s+kVARh|Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\))\s+([\d.,]+)",
    "demanda_ativa_preco_unitario": r"Demanda\s+Ativa(?:\(?kW\)?|\s+kW)\s+[\d.,]+\s+([\d.,]+)",
    "consumo_reativo_exc_preco_unitario": r"(?:Cons\.?Reat\.?Exc\.?[NF]Ponta\s+kVARh|Consumo\s+Reativo\s+Exc\.\s+[NF]\w+\s+Ponta\(kVARh\))\s+[\d.,]+\s+([\d.,]+)"
}

def extract_text(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        return f"Erro: {e}"
    return text

def test_robust_patterns(pdf_dir):
    results = {}
    files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    for file in files:
        print(f"\n--- Analisando: {file} ---")
        path = os.path.join(pdf_dir, file)
        text = extract_text(path)
        
        extracted = {}
        for var, pattern in ROBUST_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted[var] = match.group(1)
            else:
                extracted[var] = "None"
        
        results[file] = extracted
        for k, v in extracted.items():
            print(f"  {k}: {v}")
            
    return results

if __name__ == "__main__":
    pdf_folder = "Contas"
    if not os.path.exists(pdf_folder):
        pdf_folder = "../Contas"
    test_robust_patterns(pdf_folder)
