import os
import sys
import time
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Importa a lógica de processamento em lote do app.py
from app import run_batch_processing

class BatchTriggerHandler(FileSystemEventHandler):
    """
    Handler que intercepta novos arquivos em qualquer nível do diretório
    e dispara o processamento em lote na raiz monitorada.
    """
    
    def __init__(self, watch_dir: str):
        super().__init__()
        self.watch_dir = watch_dir
        self.is_processing = False  # Flag para evitar loops/gatilhos concorrentes durante o lote

    def on_created(self, event):
        # REGRA 1: Novo diretório em qualquer nível → disparar batch
        if event.is_directory:
            print(f"\n[WATCHER] Novo diretório detectado: {event.src_path}")
    
        # REGRA 2: Novo PDF APENAS na raiz do WATCH_DIR → disparar batch
        elif event.src_path.lower().endswith(".pdf"):
            parent_dir = os.path.dirname(os.path.abspath(event.src_path))
            watch_dir_abs = os.path.abspath(self.watch_dir)
            if parent_dir != watch_dir_abs:
                return  # PDF em subpasta → ignorar silenciosamente
            print(f"\n[WATCHER] Novo PDF detectado na raiz: {event.src_path}")
    
        # REGRA 3: Qualquer outro tipo de arquivo → ignorar
        else:
            return        
        print(f"\n[WATCHER] Gatilho ativado por novo arquivo: {event.src_path}")
        
        # Garante que o arquivo que disparou o evento foi completamente gravado/salvo no disco
        file_ready = False
        retries = 5
        while retries > 0:
            try:
                # Tenta abrir o arquivo em modo append para certificar que o SO liberou a escrita
                with open(event.src_path, "a+"):
                    file_ready = True
                break
            except IOError:
                time.sleep(1)
                retries -= 1
                
        if file_ready:
            self.is_processing = True
            try:
                print(f"[WATCHER] Iniciando varredura em lote na pasta raiz: {self.watch_dir}")
                # Executa o processamento em lote da pasta raiz (os arquivos de sucesso serão movidos para storage/processadas/)
                run_batch_processing(self.watch_dir, "batch_results.txt")
            finally:
                self.is_processing = False
        else:
            print(f"[WATCHER] ERROR: Não foi possível acessar o arquivo {event.src_path} (gravação incompleta).")

if __name__ == "__main__":
    # Garante a codificação UTF-8 na saída padrão do console para evitar erros de encode no Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # Define o diretório a ser monitorado a partir do .env ou usa 'Contas' como fallback
    watch_dir = os.environ.get("WATCH_DIR", "Contas")
    
    if not os.path.exists(watch_dir):
        os.makedirs(watch_dir, exist_ok=True)
        
    event_handler = BatchTriggerHandler(watch_dir)
    observer = Observer()
    
    # Habilita o monitoramento recursivo (recursive=True) para ler subpastas
    observer.schedule(event_handler, path=watch_dir, recursive=True)
    
    print(f"[*] Monitorando RECURSIVAMENTE a pasta '{watch_dir}'...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
