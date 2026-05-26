import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.getcwd())

from infrastructure.ocr import extract_structured

def inspect_bill(file_path):
    print(f"Extraindo texto de: {file_path}")
    raw_text, tables = extract_structured(file_path)
    
    output_path = os.path.join("scratch", "scratch", f"inspecao_{os.path.basename(file_path).replace('.pdf', '.txt')}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(raw_text)
    
    print(f"Texto extraído salvo em: {output_path}")
    return output_path

if __name__ == "__main__":
    test_file = r"c:\Users\bruno\OneDrive - triOS College\Desktop\Projetos\energy-bill-reader\Contas\2022\TOYOLEX IMBIRIBEIRA MES 7.pdf"
    inspect_bill(test_file)
