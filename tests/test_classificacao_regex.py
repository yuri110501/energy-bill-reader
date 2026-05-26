import os
import re
import pdfplumber
import sys

# Adiciona o diretório raiz ao path para importar as funções do core
sys.path.append(os.getcwd())
from core.extraction import _find

def get_pdf_text(path):
    with pdfplumber.open(path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text

def test_regex_comparison():
    contas_dir = "Contas"
    files = [f for f in os.listdir(contas_dir) if f.lower().endswith(".pdf")]
    
    current_patterns = [
        r"CLASSIFICA[ÇC][ÃA]O\s*\n\s*([^\n]+)",
        r"CLASSIFICA[ÇC][ÃA]O[:\s]+([A-Z0-9][^\n|]+?)(?:\s{2,}|\||\n)"
    ]
    candidate_pattern = r"CLASSIFICAÇÃO:\s*([^\n\\]+)"
    # Otimizado v2: Suporta espaços extras, quebras de linha e torna o : opcional
    optimized_pattern = r"CLASSIFICA[ÇC][ÃA]O[:\s]*\n?\s*([^\n|]+?)(?:\s{2,}|\||\n|$)"
    
    print(f"{'Arquivo':<35} | {'Atual':<20} | {'Candidato':<20} | {'Otimizado V2':<20} | {'Tabelas'}")
    print("-" * 135)
    
    for filename in files:
        path = os.path.join(contas_dir, filename)
        try:
            with pdfplumber.open(path) as pdf:
                text = ""
                tables_content = []
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            for row in table:
                                tables_content.append(" ".join([str(cell) for cell in row if cell]))
            
            # Resultado atual
            current_res = None
            for p in current_patterns:
                res = _find(p, text, re.MULTILINE)
                if res:
                    current_res = res
                    break
            
            # Resultado candidato (usuário)
            candidate_res = _find(candidate_pattern, text)
            
            # Resultado otimizado V2 (no texto)
            optimized_res = _find(optimized_pattern, text)
            
            # Busca em Tabelas (usando o padrão otimizado)
            table_res = None
            all_tables_text = "\n".join(tables_content)
            table_res = _find(optimized_pattern, all_tables_text)
            
            print(f"{filename[:35]:<35} | {str(current_res)[:20]:<20} | {str(candidate_res)[:20]:<20} | {str(optimized_res)[:20]:<20} | {str(table_res)}")
            
        except Exception as e:
            print(f"{filename[:40]:<40} | ERRO: {str(e)[:60]}")

if __name__ == "__main__":
    test_regex_comparison()
