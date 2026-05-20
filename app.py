import os
import sys
import json
import shutil
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from services.bill_service import BillService

def process_single_file(file_path: str) -> Dict[str, Any] | None:
    """
    Processa um único arquivo de fatura de energia de forma isolada.
    
    O tratamento de exceções é feito aqui para garantir que falhas em faturas
    individuais (por exemplo, PDF corrompido ou erro de OCR) não interrompam
    o processamento em lote dos demais documentos.
    """
    print(f"INFO: Processando arquivo: {os.path.basename(file_path)}", flush=True)
    try:
        # A Camada de Serviço orquestra o fluxo de extração determinística e IA fallback
        final_data, _ = BillService.process_file(file_path)
        final_data["_file_name"] = os.path.basename(file_path)
        return final_data
    except Exception as e:
        print(f"ERROR: Falha ao processar {file_path}: {e}", file=sys.stderr, flush=True)
        return None

def scan_pdf_files(folder_path: str) -> List[str]:
    """
    Realiza uma varredura recursiva na pasta de entrada procurando por arquivos PDF.
    
    Apenas arquivos com extensão .pdf (case-insensitive) são selecionados, conforme
    a especificação de ignorar outros formatos de imagem ou arquivos de sistema.
    """
    pdf_files: List[str] = []
    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, filename))
    return pdf_files

def run_batch_processing(folder_path: str, output_file: str = "batch_results.txt") -> None:
    """
    Executa o pipeline de dados em lote para todas as faturas encontradas.
    
    A gravação é feita linha a linha (JSON Lines) para garantir persistência incremental,
    evitando perda de dados se o processo for interrompido e otimizando o uso de memória.
    """
    if not os.path.isdir(folder_path):
        print(f"ERROR: O caminho '{folder_path}' não é um diretório válido.", file=sys.stderr)
        sys.exit(1)
        
    pdf_files = scan_pdf_files(folder_path)
    if not pdf_files:
        print(f"WARN: Nenhum arquivo PDF encontrado em '{folder_path}'")
        return
        
    print(f"INFO: Iniciando processamento de {len(pdf_files)} faturas...")
    
    success_count = 0
    error_count = 0
    
    # Pasta de destino para faturas processadas com sucesso
    processed_dir = os.path.join("storage", "processadas")
    os.makedirs(processed_dir, exist_ok=True)
    
    # Abre o arquivo de saída em modo de escrita, garantindo codificação UTF-8
    with open(output_file, "w", encoding="utf-8") as out_file:
        for file_path in pdf_files:
            result = process_single_file(file_path)
            if result:
                # Serialização direta sem escapar caracteres não-ASCII (preserva acentuação)
                line = json.dumps(result, ensure_ascii=False)
                out_file.write(line + "\n")
                out_file.flush()  # Força gravação em disco imediata para tolerância a falhas
                success_count += 1
                
                # Mover faturas processadas com sucesso para a pasta storage/processadas/
                filename = os.path.basename(file_path)
                dest_path = os.path.join(processed_dir, filename)
                
                # Evita colisões de nomes adicionando um timestamp se o arquivo já existir no destino
                if os.path.exists(dest_path):
                    name, ext = os.path.splitext(filename)
                    timestamp = int(time.time())
                    dest_path = os.path.join(processed_dir, f"{name}_{timestamp}{ext}")
                    
                try:
                    # Copia o arquivo processado com sucesso para o storage de destino
                    shutil.copy(file_path, dest_path)
                    print(f"INFO: Arquivo processado copiado para: {dest_path}", flush=True)
                    try:
                        # Remove explicitamente o arquivo original da pasta monitorada
                        os.remove(file_path)
                        print(f"INFO: Arquivo original removido com sucesso de: {file_path}", flush=True)
                    except Exception as rm_err:
                        print(f"ERROR: Falha ao remover o arquivo original {file_path}: {rm_err}", file=sys.stderr, flush=True)
                except Exception as copy_err:
                    print(f"ERROR: Falha ao copiar arquivo {file_path} para {dest_path}: {copy_err}", file=sys.stderr, flush=True)
            else:
                error_count += 1
                
    print(f"\n[SUCESSO]: {success_count} faturas processadas. {error_count} falhas.")
    print(f"Resultados consolidados em: {output_file}")

if __name__ == "__main__":
    # Garante a codificação UTF-8 na saída padrão do console para evitar erros no Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("\nENERGY BILL READER - CLI BATCH PROCESSOR")
        print("-" * 40)
        print("Uso: python app.py <caminho_da_pasta> [arquivo_saida.txt]")
        print("Exemplo: python app.py ./Contas resultados.txt\n")
        sys.exit(1)
        
    input_folder = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else "batch_results.txt"
    
    run_batch_processing(input_folder, output_filename)
