"""
storage_utils.py
----------------
Gerencia o armazenamento local dos arquivos de contas de energia.
"""

import os
import shutil

STORAGE_DIR = os.environ.get("LOCAL_STORAGE", "storage")


def save_file(file_name: str, content: bytes) -> str:
    """Salva o arquivo recebido no diretório de storage."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    file_path = os.path.join(STORAGE_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(content)
    print(f"DEBUG (storage_utils): Arquivo salvo em {file_path}")
    return file_path


def move_file(old_name: str, new_name: str) -> str:
    """Move o arquivo para subpasta organizada por distribuidora."""
    old_path = os.path.join(STORAGE_DIR, old_name)
    new_path = os.path.join(STORAGE_DIR, new_name)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    if os.path.exists(old_path):
        shutil.move(old_path, new_path)
        print(f"DEBUG (storage_utils): Arquivo movido de {old_path} para {new_path}")
    return new_path
