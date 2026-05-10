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


def sanitize_folder_name(name: str) -> str:
    """
    Remove acentos, caracteres especiais e espaços de um nome de pasta.
    Essencial para garantir a integridade dos caminhos no sistema de arquivos.
    """
    import unicodedata
    if not name or name == "None":
        return "outros"
    # Normaliza e remove acentos
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    # Substitui espaços e outros caracteres por '_'
    name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", name)
