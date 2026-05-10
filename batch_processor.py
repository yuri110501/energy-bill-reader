import os
import json
import glob
from dotenv import load_dotenv

load_dotenv()

from services.bill_service import BillService

def process_file(file_path):
    """
    Processa um único arquivo através do pipeline completo da camada de serviço.
    """
    print(f"DEBUG (batch): Processando {file_path}...")
    try:
        # A camada de serviço retorna um dicionário validado e salva no repository
        final_data, _ = BillService.process_file(file_path)
        final_data["_file_name"] = os.path.basename(file_path)
        return final_data
    except Exception as e:
        print(f"ERROR (batch): Falha ao processar {file_path}: {e}")
        return None

def run_batch(folder_path, output_file="batch_results.txt"):
    """
    Lê todos os arquivos da pasta e salva os JSONs em um único documento TXT.
    """
    if not os.path.isdir(folder_path):
        print(f"ERROR: O caminho '{folder_path}' não é um diretório válido.")
        return

    # Extensões suportadas
    extensions = ["*.pdf", "*.jpg", "*.jpeg", "*.png"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    if not files:
        print(f"WARN: Nenhum arquivo compatível encontrado em {folder_path}")
        return

    print(f"INFO: Iniciando processamento de {len(files)} arquivos...")
    
    # Processa um por vez e escreve imediatamente no arquivo (melhor para debug em lotes grandes)
    with open(output_file, "w", encoding="utf-8") as out:
        success_count = 0
        for f in files:
            res = process_file(f)
            if res:
                line = json.dumps(res, ensure_ascii=False)
                out.write(line + "\n")
                out.flush()  # Garante que seja salvo no disco em tempo real
                success_count += 1
                
        print(f"\n[SUCESSO]: {success_count} arquivos processados com exito.")
        print(f"[Resultados] consolidados em: {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n🚀 BATCH PROCESSOR - Energy Bill Reader")
        print("-" * 40)
        print("Uso: python batch_processor.py <caminho_da_pasta> [arquivo_saida.txt]")
        print("Exemplo: python batch_processor.py ./Contas resultados.txt\n")
    else:
        folder = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "batch_results.txt"
        run_batch(folder, output)

