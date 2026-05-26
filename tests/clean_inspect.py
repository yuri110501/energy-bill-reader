import pdfplumber
import sys
import re

def inspect_clean(path):
    with pdfplumber.open(path) as pdf:
        text = ""
        for page in pdf.pages:
            # Tenta extrair palavras para reconstruir a ordem
            words = page.extract_words()
            page_text = " ".join([w['text'] for w in words])
            text += page_text + "\n"
        
        print("--- TEXTO RECONSTRUÍDO ---")
        print(text)
        
        # Testando o Regex do usuário no texto limpo
        pattern = r"(?:CÓDIGO\s+DO\s+CLIENTE)\D*(\d{10})|(\d{10})\D*CÓDIGO\s+DO\s+CLIENTE"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"\n[SUCESSO] Encontrado: {match.group(1) or match.group(2)}")
        else:
            print("\n[FALHA] Regex não encontrou nada no texto reconstruído.")

if __name__ == "__main__":
    inspect_clean(sys.argv[1])
