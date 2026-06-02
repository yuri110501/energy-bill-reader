"""
storage.py
----------
Gerencia o armazenamento local dos arquivos de contas de energia.
Unifica storage_utils.py (IO de arquivos) nesta camada de infraestrutura.
"""

import os
import shutil
import re
from typing import Optional

STORAGE_DIR = os.environ.get("LOCAL_STORAGE", "storage")
PROCESSED_DIR = os.path.join(STORAGE_DIR, "processadas")


def normalize_mes_referencia(mes_referencia: Optional[str]) -> str:
    """
    Normaliza o mês de referência de MM/AAAA para MM-AAAA.
    
    A substituição do caractere '/' por '-' é necessária porque a barra é interpretada
    pelos sistemas operacionais como delimitador de diretório, o que corromperia o
    caminho de destino final ao tentar salvar o arquivo físico.
    """
    if not mes_referencia or str(mes_referencia).strip() in ("", "None", "null"):
        return "mes_referencia_não_localizado"
    
    cleaned = str(mes_referencia).strip()
    # Identifica formato padrão MM/AAAA ou variações com delimitadores para normalizar
    match = re.search(r"(\d{2})[/-](\d{4})", cleaned)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    # Se não bater com o padrão de data de referência esperado (MM/AAAA ou MM-AAAA),
    # tratamos como não localizado para evitar arquivos com nomes inválidos.
    return "mes_referencia_não_localizado"


def resolve_unique_filename(dest_dir: str, base_name: str, ext: str) -> str:
    """
    Resolve conflitos de nome gerando um sufixo numérico incremental.
    
    Isso previne que faturas históricas processadas sejam sobrescritas em caso
    de reprocessamento de lote ou se duas faturas concorrentes possuírem a mesma
    unidade consumidora e período de referência.
    """
    filename = f"{base_name}{ext}"
    full_path = os.path.join(dest_dir, filename)
    if not os.path.exists(full_path):
        return filename

    counter = 1
    while True:
        candidate_name = f"{base_name}({counter}){ext}"
        candidate_path = os.path.join(dest_dir, candidate_name)
        if not os.path.exists(candidate_path):
            return candidate_name
        counter += 1


def move_processed_pdf(src_path: str, id_sof: Optional[str], mes_referencia: Optional[str]) -> str:
    """
    Move e renomeia o PDF processado para sua respectiva pasta estruturada por ID_sof.
    
    Caso o ID_sof seja nulo ou indefinido por falha no mapeamento da UC, o arquivo
    é movido para uma subpasta de auditoria 'Falha_no_ID' para triagem manual.
    """
    # Define a subpasta de destino com base na presença do ID_sof do cliente
    folder_name = str(id_sof).strip() if id_sof and str(id_sof).strip() not in ("None", "") else "Falha_no_ID"
    target_dir = os.path.join(PROCESSED_DIR, folder_name)
    os.makedirs(target_dir, exist_ok=True)

    # Normaliza a data para gerar o nome base do arquivo PDF de destino
    base_name = normalize_mes_referencia(mes_referencia)
    _, ext = os.path.splitext(src_path)
    
    # Resolve conflitos se o arquivo já existir no diretório de destino
    final_name = resolve_unique_filename(target_dir, base_name, ext)
    dest_path = os.path.join(target_dir, final_name)
    
    # Realiza a movimentação destrutiva do arquivo original
    shutil.move(src_path, dest_path)
    print(f"DEBUG (storage): Arquivo original movido com sucesso para {dest_path}")
    return dest_path



def save_file(file_name: str, content: bytes) -> str:
    """Salva o arquivo recebido no diretório de storage."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    file_path = os.path.join(STORAGE_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(content)
    print(f"DEBUG (storage): Arquivo salvo em {file_path}")
    return file_path


def move_file(old_name: str, new_name: str) -> str:
    """Move o arquivo para subpasta organizada por distribuidora."""
    old_path = os.path.join(STORAGE_DIR, old_name)
    new_path = os.path.join(STORAGE_DIR, new_name)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    if os.path.exists(old_path):
        shutil.move(old_path, new_path)
        print(f"DEBUG (storage): Arquivo movido de {old_path} para {new_path}")
    return new_path
