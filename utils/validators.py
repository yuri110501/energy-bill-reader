"""
validators.py
-------------
Validadores genéricos reutilizáveis (CPF/CNPJ, datas, etc.).
Extraído de text_utils.py para respeitar responsabilidade única.
"""

import re


def validate_cpf_cnpj(doc: str) -> bool:
    """
    Valida se o documento tem 11 dígitos (CPF) ou 14 dígitos (CNPJ).
    Não valida dígitos verificadores — apenas formato básico.
    """
    if not doc:
        return False
    cleaned = re.sub(r"\D", "", str(doc))
    return len(cleaned) in (11, 14)

