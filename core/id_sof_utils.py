"""
id_sof_utils.py
---------------
Utilitários para mapeamento de código de cliente para ID_sof.
O mapeamento é carregado em cache na memória, mas revalidado a cada chamada
via comparação de timestamp de modificação do arquivo (os.path.getmtime).
Isso permite que o container do watcher detecte novos mapeamentos sem precisar
ser reiniciado quando o uc_mapping.json for atualizado em tempo de execução.
"""

import json
import os
from typing import Optional

# Cache em memória do mapeamento: armazena tanto o dicionário quanto o
# timestamp do arquivo na última carga para permitir invalidação automática.
_UC_MAP: Optional[dict] = None
_UC_MAP_MTIME: float = 0.0

# Caminho padrão do arquivo de mapeamento (calculado uma única vez)
_DEFAULT_MAP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "uc_mapping.json"
)


def load_uc_mapping(path: Optional[str] = None) -> dict:
    """
    Carrega o mapeamento de codigo_cliente para ID_sof com invalidação automática de cache.
    Se o arquivo uc_mapping.json for modificado desde a última carga, o cache é invalidado
    e o arquivo é relido, permitindo atualizações em tempo real sem reiniciar o serviço.
    """
    global _UC_MAP, _UC_MAP_MTIME

    p = path or _DEFAULT_MAP_PATH

    # Verifica o timestamp de modificação atual do arquivo
    try:
        current_mtime = os.path.getmtime(p)
    except OSError:
        current_mtime = 0.0

    # Recarrega apenas se o cache estiver vazio ou o arquivo tiver sido modificado
    if _UC_MAP is None or current_mtime != _UC_MAP_MTIME:
        try:
            with open(p, "r", encoding="utf-8") as fh:
                raw_map = json.load(fh)
            _UC_MAP_MTIME = current_mtime
        except FileNotFoundError:
            print(f"AVISO (id_sof_utils): uc_mapping.json não encontrado em {p}")
            raw_map = {}

        _UC_MAP = {}
        for codigo, id_sof in raw_map.items():
            _UC_MAP[str(codigo)] = id_sof

            normalized_codigo = _normalize_codigo_cliente(codigo)
            if normalized_codigo and normalized_codigo not in _UC_MAP:
                _UC_MAP[normalized_codigo] = id_sof

            if normalized_codigo.isdigit():
                stripped_codigo = normalized_codigo.lstrip("0")
                if stripped_codigo and stripped_codigo not in _UC_MAP:
                    _UC_MAP[stripped_codigo] = id_sof

    return _UC_MAP


def _normalize_codigo_cliente(codigo: str) -> str:
    """Normaliza codigo_cliente para aumentar chance de match no mapping."""
    if not codigo:
        return ""
    s = str(codigo).strip().upper()
    for ch in (" ", ".", "-", "/", "\\"):
        s = s.replace(ch, "")
    return s


def get_id_sof_from_codigo(codigo: str) -> str:
    """
    Busca ID_sof para um codigo_cliente dado.
    Tenta múltiplas formas de normalização para aumentar acerto.

    Args:
        codigo: Código do cliente a mapear

    Returns:
        ID_sof string ou "" se não encontrado.
    """
    if not codigo:
        return ""

    uc_map = load_uc_mapping()

    # Tenta candidatos em ordem de prioridade
    candidates = [
        codigo,                             # 1. Valor bruto (já pode estar normalizado)
        _normalize_codigo_cliente(codigo),  # 2. Normalizado (sem separadores)
    ]

    # Tenta também remover zeros à esquerda (se numérico)
    norm = _normalize_codigo_cliente(codigo)
    if norm and norm.isdigit():
        candidates.append(norm.lstrip("0"))

    for c in candidates:
        if c in uc_map:
            id_sof = uc_map[c]
            print(f"DEBUG (id_sof_utils): codigo_cliente='{codigo}' -> ID_sof='{id_sof}'")
            return id_sof

    # Se não encontrar, loga para posterior manutenção do mapping
    print(f"AVISO (id_sof_utils): codigo_cliente='{codigo}' não mapeado em uc_mapping.json")
    return ""
