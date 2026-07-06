import os
import sys
import io
import json
import glob
import uuid
import threading
import traceback
from dotenv import load_dotenv

load_dotenv()

from services.bill_service import BillService

# Trava global para garantir que apenas um processo escreva no arquivo de saída
# e atualize o dicionário de jobs de forma segura em cenários de concorrência.
_write_lock = threading.Lock()

# Dicionário de controle de jobs assíncronos (preenchido por run_batch_async)
batch_jobs: dict = {}


def process_file(file_path: str) -> dict | None:
    """
    Processa um único arquivo de fatura de energia de forma isolada.
    Em caso de falha, o erro é logado para stdout/stderr (compatível com Docker)
    em vez de gravado em um arquivo local de debug, que seria perdido em reinicializações do container.
    """
    print(f"DEBUG (batch): Processando {file_path}", flush=True)
    try:
        final_data, _ = BillService.process_file(file_path)
        final_data["_file_name"] = os.path.basename(file_path)
        print(f"DEBUG (batch): Processado com sucesso → {os.path.basename(file_path)}", flush=True)
        return final_data
    except Exception as e:
        err_msg = traceback.format_exc()
        # Logs direcionados para stderr (capturado nativamente pelo Docker e gerenciadores de container)
        print(f"ERROR (batch): Falha ao processar {file_path}: {e}\n{err_msg}", file=sys.stderr, flush=True)
        return None


def run_batch_async(folder_path: str, output_file: str = "batch_results.txt") -> str:
    """Inicia o processamento em lote de forma assíncrona usando uma thread dedicada."""
    job_id = str(uuid.uuid4())

    with _write_lock:
        batch_jobs[job_id] = {
            "status": "running",
            "total": 0,
            "processed": 0,
            "success": 0,
            "errors": 0,
            "output_file": output_file,
            "message": "Buscando arquivos...",
        }

    def target():
        try:
            run_batch(folder_path, output_file, job_id=job_id)
        except Exception as e:
            print(f"ERROR (batch thread): {e}\n{traceback.format_exc()}", file=sys.stderr)
            with _write_lock:
                if job_id in batch_jobs:
                    batch_jobs[job_id]["status"] = "error"
                    batch_jobs[job_id]["message"] = str(e)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return job_id


def run_batch(folder_path: str, output_file: str = "batch_results.txt", job_id: str | None = None) -> None:
    """
    Lê todos os arquivos da pasta e salva os JSONs em um único documento TXT.
    Utiliza trava de escrita para garantir que execuções concorrentes não corrompam o arquivo de saída.
    """
    with _write_lock:
        job = batch_jobs.get(job_id) if job_id else None

    if not os.path.isdir(folder_path):
        msg = f"ERROR: O caminho '{folder_path}' não é um diretório válido."
        print(msg, file=sys.stderr)
        if job:
            with _write_lock:
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
            with _write_lock:
                job["status"] = "error"
                job["message"] = msg
        return

    print(f"INFO: Iniciando processamento de {len(files)} arquivos...")
    if job:
        with _write_lock:
            job["total"] = len(files)
            job["message"] = "Processando arquivos..."

    success_count = 0
    error_count = 0

    # Processa um por vez e escreve imediatamente no arquivo (melhor para debug em lotes grandes)
    with open(output_file, "w", encoding="utf-8") as out:
        for f in files:
            res = process_file(f)
            if job:
                with _write_lock:
                    job["processed"] += 1

            if res:
                line = json.dumps(res, ensure_ascii=False)
                out.write(line + "\n")
                out.flush()  # Garante persistência em disco imediata (tolerância a falhas)
                success_count += 1
                if job:
                    with _write_lock:
                        job["success"] = success_count
            else:
                error_count += 1
                if job:
                    with _write_lock:
                        job["errors"] = error_count

    msg = f"{success_count} arquivos processados com êxito. {error_count} falhas."
    print(f"\n[SUCESSO]: {msg}")
    print(f"[Resultados] consolidados em: {output_file}")

    if job:
        with _write_lock:
            job["status"] = "completed"
            job["message"] = msg


if __name__ == "__main__":
    # Força a saída do console para UTF-8 para evitar erros com caracteres especiais no Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if len(sys.argv) < 2:
        print("\nBATCH PROCESSOR - Energy Bill Reader")
        print("-" * 40)
        print("Uso: python batch_processor.py <caminho_da_pasta> [arquivo_saida.txt]")
        print("Exemplo: python batch_processor.py ./Contas resultados.txt\n")
    else:
        folder = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "batch_results.txt"
        run_batch(folder, output)
