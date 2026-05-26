"""
id_sof_utils.py
---------------
Utilitários para mapeamento de código de cliente para ID_sof.
"""

import json
import os
from typing import Optional

_UC_MAP = None

def load_uc_mapping(path: Optional[str] = None) -> dict:
    """Carrega o mapeamento de codigo_cliente para ID_sof uma única vez (singleton)."""
    global _UC_MAP
    if _UC_MAP is None:
        p = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uc_mapping.json")
        try:
            with open(p, "r", encoding="utf-8") as fh:
                _UC_MAP = json.load(fh)
        except FileNotFoundError:
            print(f"AVISO (id_sof_utils): uc_mapping.json não encontrado em {p}")
            _UC_MAP = {}
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
        codigo,                              # 1. Valor bruto (já pode estar normalizado)
        _normalize_codigo_cliente(codigo),   # 2. Normalizado (sem separadores)
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
