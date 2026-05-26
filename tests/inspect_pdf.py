import pdfplumber
import sys
import os

def inspect_pdf(pdf_path):
    # Gera o nome do arquivo de saída .txt baseado no nome do PDF
    base_name = os.path.basename(pdf_path)
    output_path = os.path.join("scratch", f"inspecao_{os.path.splitext(base_name)[0]}.txt")

    output_content = []
    output_content.append(f"{'='*60}")
    output_content.append(f"🔍 INSPEÇÃO TÉCNICA: {pdf_path}")
    output_content.append(f"{'='*60}\n")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                output_content.append(f"--- PÁGINA {i+1} ---")
                
                # Extração de Texto com preservação de layout
                output_content.append("\n[TEXTO BRUTO (Layout-aware)]")
                text = page.extract_text(layout=True)
                output_content.append(text if text else "Nenhum texto detectado.")
                
                # Extração de Tabelas
                output_content.append("\n[TABELAS DETECTADAS]")
                tables = page.extract_tables()
                if tables:
                    for j, table in enumerate(tables):
                        output_content.append(f"\nTabela {j+1}:")
                        for row in table:
                            output_content.append(f"  {row}")
                else:
                    output_content.append("Nenhuma tabela estruturada detectada.")
                
                output_content.append(f"\n{'-'*40}\n")
        
        # Salva o conteúdo no arquivo .txt
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_content))
            
        print(f"DONE: Inspeção concluída com sucesso!")
        print(f"File: Resultado salvo em: {output_path}")

    except Exception as e:
        print(f"ERROR: Erro ao ler PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scratch/inspect_pdf.py <caminho_do_pdf>")
    else:
        # Garante que o diretório scratch existe
        if not os.path.exists("scratch"):
            os.makedirs("scratch")
        inspect_pdf(sys.argv[1])
