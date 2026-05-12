import os
import json
import glob
from dotenv import load_dotenv

load_dotenv()

from services.bill_service import BillService

def process_file(file_path):
    print(f"DEBUG (batch thread): Antes de processar {file_path}", flush=True)
    try:
        final_data, _ = BillService.process_file(file_path)
        final_data["_file_name"] = os.path.basename(file_path)
        print(f"DEBUG (batch thread): Processou {file_path} com sucesso", flush=True)
        return final_data
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"ERROR (batch): Falha ao processar {file_path}: {e}\n{err_msg}")
        with open("batch_debug_errors.log", "a", encoding="utf-8") as err_log:
            err_log.write(f"Falha em {file_path}:\n{err_msg}\n")
        return None

import uuid
import threading

batch_jobs = {}

def run_batch_async(folder_path, output_file="batch_results.txt"):
    """Inicia o processamento em lote de forma assíncrona usando uma thread."""
    job_id = str(uuid.uuid4())
    batch_jobs[job_id] = {
        "status": "running",
        "total": 0,
        "processed": 0,
        "success": 0,
        "errors": 0,
        "output_file": output_file,
        "message": "Buscando arquivos..."
    }
    
    def target():
        try:
            run_batch(folder_path, output_file, job_id=job_id)
        except Exception as e:
            import traceback
            print(f"ERROR (batch thread): {e}\n{traceback.format_exc()}")
            if job_id in batch_jobs:
                batch_jobs[job_id]["status"] = "error"
                batch_jobs[job_id]["message"] = str(e)
        
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    return job_id

def run_batch(folder_path, output_file="batch_results.txt", job_id=None):
    """
    Lê todos os arquivos da pasta e salva os JSONs em um único documento TXT.
    """
    job = batch_jobs.get(job_id) if job_id else None
    
    if not os.path.isdir(folder_path):
        msg = f"ERROR: O caminho '{folder_path}' não é um diretório válido."
        print(msg)
        if job:
            job["status"] = "error"
            job["message"] = msg
        return

    # Extensões suportadas — busca recursiva em subpastas
    extensions = ["*.pdf", "*.jpg", "*.jpeg", "*.png"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder_path, "**", ext), recursive=True))

    if not files:
        msg = f"WARN: Nenhum arquivo compatível encontrado em {folder_path} (incluindo subpastas)"
        print(msg)
        if job:
            job["status"] = "error"
            job["message"] = msg
        return

    print(f"INFO: Iniciando processamento de {len(files)} arquivos...")
    if job:
        job["total"] = len(files)
        job["message"] = "Processando arquivos..."
    
    # Processa um por vez e escreve imediatamente no arquivo (melhor para debug em lotes grandes)
    with open(output_file, "w", encoding="utf-8") as out:
        success_count = 0
        error_count = 0
        for f in files:
            res = process_file(f)
            if job:
                job["processed"] += 1
                
            if res:
                line = json.dumps(res, ensure_ascii=False)
                out.write(line + "\n")
                out.flush()  # Garante que seja salvo no disco em tempo real
                success_count += 1
                if job:
                    job["success"] = success_count
            else:
                error_count += 1
                if job:
                    job["errors"] = error_count
                
        msg = f"{success_count} arquivos processados com êxito. {error_count} falhas."
        print(f"\n[SUCESSO]: {msg}")
        print(f"[Resultados] consolidados em: {output_file}")
        
        if job:
            job["status"] = "completed"
            job["message"] = msg

if __name__ == "__main__":
    import sys
    import io

    # Força a saída do console para UTF-8 para evitar erros com caracteres especiais no Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("\nBATCH PROCESSOR - Energy Bill Reader")
        print("-" * 40)
        print("Uso: python batch_processor.py <caminho_da_pasta> [arquivo_saida.txt]")
        print("Exemplo: python batch_processor.py ./Contas resultados.txt\n")
    else:
        folder = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "batch_results.txt"
        run_batch(folder, output)

