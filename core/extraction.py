"""
extraction.py
-------------
Camada Core responsável pela extração estruturada de dados de faturas de energia.

Estratégia (sem dependência de IA):
  1. Para PDFs digitais: usa as TABELAS extraídas pelo pdfplumber (estrutura nativa).
  2. Para qualquer tipo: usa regex direcionado apenas em seções específicas do texto
     (cabeçalho, datas, valor total) — não no texto inteiro.
  3. Retorna um score de confiança (0.0–1.0) para a camada de serviço decidir
     se precisa acionar a IA como fallback.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Campos críticos: se a maioria estiver preenchida, a IA não é necessária
# ---------------------------------------------------------------------------
CRITICAL_FIELDS = [
    "distribuidora", "valor_total", "mes_referencia",
    "data_vencimento",
]


# ---------------------------------------------------------------------------
# Mapeamento de linhas de tabela → campos do BillData
# Chave: substring a ser buscada na descrição da linha (case-insensitive)
# Valor: dict com 'quantity' e 'price' apontando para os campos do modelo
# ---------------------------------------------------------------------------
TABLE_ROW_MAP: Dict[str, Dict[str, str]] = {
    "consumo ativo na ponta(kwh)-tusd": {
        "quantity": "consumo_ativo_na_ponta_tusd",
        "price":    "consumo_ativo_na_ponta_tusd_preco_unitario",
    },
    "consumo ativo fora de ponta(kwh)-tusd": {
        "quantity": "consumo_ativo_fora_ponta_tusd",
        "price":    "consumo_ativo_fora_ponta_tusd_preco_unitario",
    },
    "consumo-tusd": {
        "quantity": "consumo_ativo_fora_ponta_tusd",
        "price":    "consumo_ativo_fora_ponta_tusd_preco_unitario",
    },
    "consumo-te": {
        "quantity": None,
        "price":    None,
    },
    "consumo reativo exc. na ponta(kvarh)": {
        "quantity": "consumo_reativo_exc_na_ponta",
        "price":    "consumo_reativo_exc_na_ponta_preco_unitario",
    },
    "consumo reativo exc. fora ponta(kvarh)": {
        "quantity": "consumo_reativo_exc_fora_ponta",
        "price":    "consumo_reativo_exc_fora_ponta_preco_unitario",
    },
    "demanda ativa(kw)": {
        "quantity": "demanda_ativa",
        "price":    "demanda_ativa_preco_unitario",
    },
    "demanda reativa excedente": {
        "quantity": "demanda_reativa_excedente",
        "price":    "demanda_reativa_excedente_preco_unitario",
    },
    "demanda reativa ponta": {
        "quantity": "demanda_reativo_ponta",
        "price":    None,
    },
    "demanda reativa fora": {
        "quantity": "demanda_reativo_fora_ponta",
        "price":    None,
    },
}

# Distribuidoras conhecidas (nome exibido → nome normalizado)
KNOWN_DISTRIBUTORS = {
    "celpe": "Celpe",
    "neoenergia pernambuco": "Celpe",
    "neoenergiapernambuco": "Celpe",
    "companhia energética de pernambuco": "Celpe",
    "cemig": "Cemig",
    "copel": "Copel",
    "enel": "Enel",
    "light": "Light",
    "coelba": "Coelba",
    "energisa": "Energisa",
    "equatorial": "Equatorial",
    "elektro": "Elektro",
    "cpfl": "CPFL",
    "rge": "RGE",
    "cosern": "Cosern",
    "ceal": "CEAL",
    "ceron": "CERON",
    "amazonas energia": "Amazonas Energia",
}


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _normalize_number(value: str) -> Optional[str]:
    """
    Converte número no formato brasileiro para float string.
    Suporta: '1.234,56' → '1234.56' | '1.234' → '1234' | '1234,56' → '1234.56'
    """
    if not value:
        return None
    v = value.strip().rstrip("-")
    # Formato brasileiro com milhares e centavos: 1.234,56
    if re.search(r"\d\.\d{3},\d", v):
        v = v.replace(".", "").replace(",", ".")
    # Apenas milhares sem centavos: 50.050 ou 1.234 (3 dígitos após o ponto)
    elif re.match(r"^\d+\.\d{3}$", v):
        v = v.replace(".", "")
    # Vírgula como decimal: 1234,56
    elif re.match(r"^\d+,\d+$", v):
        v = v.replace(",", ".")
    try:
        return str(float(v))
    except ValueError:
        return None


def _find(pattern: str, text: str, flags: int = 0) -> Optional[str]:
    """Aplica regex e retorna o primeiro grupo capturado não-vazio."""
    match = re.search(pattern, text, re.IGNORECASE | flags)
    if not match:
        return None
    for g in match.groups():
        if g and g.strip():
            return g.strip()
    return None


def _detect_distributor(text: str) -> Optional[str]:
    """Detecta a distribuidora no texto de cabeçalho."""
    text_lower = text.lower()
    for key, normalized in KNOWN_DISTRIBUTORS.items():
        if key in text_lower:
            return normalized
    return None


def _calculate_confidence(data: Dict[str, Any]) -> float:
    """
    Calcula score de confiança baseado nos campos críticos preenchidos.
    Retorna valor entre 0.0 e 1.0.
    """
    filled = sum(
        1 for f in CRITICAL_FIELDS
        if data.get(f) and data[f] not in (None, "None", "")
    )
    return filled / len(CRITICAL_FIELDS)


# ---------------------------------------------------------------------------
# Extração de tabelas (pdfplumber)
# ---------------------------------------------------------------------------

def extract_from_tables(tables: List[List[List[str]]]) -> Dict[str, Any]:
    """
    Parseia as tabelas extraídas pelo pdfplumber e mapeia para campos do BillData.
    As tabelas chegam como lista de tabelas, cada uma sendo lista de linhas,
    cada linha sendo lista de strings (células).
    """
    result: Dict[str, Any] = {}
    geracao = 0.0

    for table in tables:
        if not table:
            continue
        for row in table:
            if not row:
                continue

            # Normaliza as células: remove None e strip
            cells = [str(c).strip() if c else "" for c in row]
            if not cells or not cells[0]:
                continue

            desc = cells[0].lower()

            # --- Busca mapeamento direto ---
            for key, mapping in TABLE_ROW_MAP.items():
                if key in desc:
                    # Coluna 1 = quantidade, Coluna 2 = preço unitário
                    if len(cells) > 1 and mapping.get("quantity"):
                        val = _normalize_number(cells[1])
                        if val:
                            result[mapping["quantity"]] = val

                    if len(cells) > 2 and mapping.get("price"):
                        val = _normalize_number(cells[2])
                        if val:
                            result[mapping["price"]] = val
                    break

            # --- Detecção de geração solar/injetada ---
            # Exige que a célula de valor tenha sinal negativo (indicador de crédito)
            # para evitar capturar número de instalação ou outros campos
            is_geracao = (
                "energia injet" in desc
                or "gera\u00e7\u00e3o" in desc
                or "ger. fora" in desc
                or "ger. ponta" in desc
                or ("geracao" in desc and "consumo" not in desc)
            )
            if is_geracao and len(cells) > 1:
                raw_cell = cells[1]
                # Só aceita como geração se o valor original termina em '-' (sinal negativo)
                if raw_cell.endswith("-"):
                    val = _normalize_number(raw_cell)
                    if val:
                        result["geracao_kwh"] = val
                        try:
                            geracao = float(val)
                        except ValueError:
                            pass

            # --- Valor Total ---
            if any(k in desc for k in ["total a pagar", "valor total", "total da fatura"]):
                for cell in cells[1:]:
                    val = _normalize_number(cell)
                    if val:
                        result["valor_total"] = val
                        break

            # --- Classificação (Novo) ---
            if "classifica" in desc:
                # Otimizado v2: Suporta espaços extras, quebras de linha e torna o : opcional
                # Aqui buscamos na linha inteira da tabela concatenada
                row_text = " ".join(cells)
                classif = _find(r"CLASSIFICA[ÇC][ÃA]O[:\s]*\n?\s*([^\n|]+?)(?:\s{2,}|\||\n|$)", row_text)
                if classif:
                    result["classificacao_detalhada"] = classif



    return result


# ---------------------------------------------------------------------------
# Extração de texto (cabeçalho + seções específicas)
# ---------------------------------------------------------------------------

def extract_from_text(raw_text: str) -> Dict[str, Any]:
    """
    Extrai campos que vivem fora das tabelas: cabeçalho, datas, valor total,
    bandeira, classificação. Usa regex direcionado (não em texto inteiro).
    """
    result: Dict[str, Any] = {}

    # Distribuidora
    result["distribuidora"] = _detect_distributor(raw_text[:2000])

    # CPF/CNPJ do cliente (PAGADOR)
    # Na Celpe o CNPJ da distribuidora fica no cabeçalho; o do cliente fica na
    # seção 'PAGADOR | CPF/CNPJ' no rodapé — pode estar parcialmente mascarado
    cpf_cnpj = (
        # Busca explicitamente na seção do pagador
        _find(
            r"PAGADOR[^\n]*\n[^\n]+?\|\s*([\d\.\*/\-]+)",
            raw_text
        )
        # Ou busca após 'NOME DO CLIENTE:' contexto
        or _find(
            r"NOME\s+DO\s+CLIENTE[^\n]*\n[^\n]+?\n[^\n]*?\b([\d]{2}[\.\ ]?[\d]{3}[\.\ ]?[\d]{3}[\/][\d]{4}[-][\d]{2})\b",
            raw_text
        )
    )
    # Garante que não é o CNPJ da distribuidora conhecida (10.835.932 = Celpe)
    if cpf_cnpj and "10.835.932" in cpf_cnpj.replace(" ", ""):
        cpf_cnpj = None
    result["cpf_cnpj_titular"] = cpf_cnpj

    # Código do cliente
    result["codigo_cliente"] = (
        _find(r"(\d{10})\s+\d{2}\/\d{2}\/\d{4}\s+[\d\.,]+\s*\nC[OÓ]DIGO\s+DO\s+CLIENTE", raw_text)
        or _find(r"N[°º]\s+DO\s+CLIENTE\s*\n[^\n]+?(\d{10})", raw_text, re.MULTILINE)
        or _find(r"\d{6,}\s+(\d{10})\s+\d{2}\/\d{2}\/\d{4}", raw_text)
    )

    # Mês de referência
    mes_ref = (
        _find(r"REF[:\.]?M[EÊ]S[\\/\s]?ANO[\s\S]{0,50}?\n.*?((?:0[1-9]|1[0-2])\/20\d{2})", raw_text)
        or _find(r"^((?:0[1-9]|1[0-2])\/20\d{2})\s+[\d\.,]+\s+\d{2}\/\d{2}\/\d{4}", raw_text, re.MULTILINE)
    )
    # Se vier como DD/MM/AAAA, converte para MM/AAAA
    if mes_ref and len(mes_ref) == 10 and mes_ref.count("/") == 2:
        parts = mes_ref.split("/")
        mes_ref = f"{parts[1]}/{parts[2]}"
    result["mes_referencia"] = mes_ref

    # Data de vencimento
    result["data_vencimento"] = (
        _find(
            r"(?:vencimento|data\s+de\s+vencimento|vence\s+em)[\s\S]{0,150}?"
            r"([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})",
            raw_text
        )
        # Fallback Grupo A antigo: inline com Total a Pagar
        or _find(r"TOTAL\s+A\s+PAGAR\s*\(R\$\)\s+(\d{2}/\d{2}/\d{4})", raw_text)
    )

    # Datas de leitura (DD/MM/AAAA)
    result["data_leitura_anterior"] = _find(
        r"(?:leitura\s+anterior|medida\s+anterior)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})", raw_text
    )
    result["data_leitura_atual"] = _find(
        r"(?:leitura\s+atual|medida\s+atual)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})", raw_text
    )

    # Número de dias
    result["numero_dias_faturamento"] = _find(
        r"(?:n[º°]?\s+de\s+dias)[:\s]*(\d+)", raw_text
    )

    # Bandeira tarifária
    result["bandeira_tarifaria"] = (
        _find(
            r"(?:BANDEIRA|Band\.?\s+)[:\s]*(VERDE|AMARELA|VERMELHA\s+PATAMAR\s+[12]|ESCASSEZ\s+H[IÍ]DRICA)",
            raw_text
        )
        # Fallback Grupo B (DANFE): formato frase
        or _find(r"bandeira\s+em\s+vigor\s+[eé]\s+a\s+(VERDE|AMARELA|VERMELHA[^\n\.]*)", raw_text)
    )

    # Tipo de fornecimento
    result["tipo_fornecimento"] = (
        _find(r"(monof[aá]sico|bif[aá]sico|trif[aá]sico)", raw_text)
        # Fallback Grupo B/A: formato Conv. Monômia - Trifásico
        or _find(r"Conv\.\s+(?:Mon[oô]mia|Binom[iî]a)[^\n]*?-\s*(Monof[aá]sico|Bif[aá]sico|Trif[aá]sico)", raw_text)
    )

    # Classificação
    result["classificacao_detalhada"] = (
        # Otimizado v2: Suporta espaços extras, quebras de linha e torna o : opcional.
        # Funciona tanto para Grupo A (valor abaixo) quanto Grupo B (valor na linha).
        _find(r"CLASSIFICA[ÇC][ÃA]O[:\s]*\n?\s*([^\n|]+?)(?:\s{2,}|\||\n|$)", raw_text)
    )

    # Valor total: busca no formato Celpe (linha do mes com valor e vencimento)
    # Formato: "MM/AAAA 135,64 DD/MM/AAAA" ou "TOTAL A PAGAR R$ 135,64"
    valor_raw = (
        _find(
            r"^(?:0[1-9]|1[0-2])\/20\d{2}\s+([\d\.]+,\d{2})\s+\d{2}\/\d{2}\/20\d{2}",
            raw_text, re.MULTILINE
        )
        or _find(
            r"(?:total\s+a\s+pagar|valor\s+total|total\s+da\s+fatura)[:\s\n]*R?\$?\s*([\d\.]+,[\d]{2}|\d{3,}[.,]\d{2}|\d{2,})",
            raw_text
        )
    )
    if valor_raw and re.match(r"^\d{1}$", valor_raw.strip()):
        valor_raw = None
    result["valor_total"] = valor_raw

    # Leituras do medidor: formato tabular Celpe
    # Exemplo: "3213648496 Energia Ativa Único 321004,00 328347,00 1,00000 100,00"
    leitura_tabular = _find(
        r"Energia\s+Ativa[^\n]+?([\d\.]+,\d+)\s+([\d\.]+,\d+)\s+[\d\.]+,\d+\s+[\d\.]+,\d+",
        raw_text
    )
    # Se achou pelo padrão tabular, extrai os dois valores (anterior e atual)
    tabular_match = re.search(
        r"Energia\s+Ativa[^\n]+?([\d\.]+,\d+)\s+([\d\.]+,\d+)\s+[\d\.]+,\d+\s+[\d\.]+,\d+",
        raw_text, re.IGNORECASE
    )
    if tabular_match:
        leitura_anterior_raw = tabular_match.group(1)
        leitura_atual_raw = tabular_match.group(2)
    else:
        # Fallback: busca explícita por rótulo, requer 5+ dígitos para não pegar datas
        leitura_atual_raw = _find(
            r"(?:leitura\s+atual|medida\s+atual)[:\s]*(?!\d{2}\/\d{2}\/\d{4})([1-9]\d{4,})", raw_text
        )
        leitura_anterior_raw = _find(
            r"(?:leitura\s+anterior|medida\s+anterior)[:\s]*(?!\d{2}\/\d{2}\/\d{4})([1-9]\d{4,})", raw_text
        )
    result["leitura_atual"] = leitura_atual_raw
    result["leitura_anterior"] = leitura_anterior_raw

    # Geração solar no texto: só aceita quando há '-' após o valor (indicador de crédito)
    # Exige valores com vírgula decimal (ex: '8.379,98-') OU 4+ dígitos para evitar CNPJ/sufixos
    # Também busca por "credi tos utilizados" que é comum na Celpe
    geracao_text = (
        _find(
            r"(?:credi\s*tos\s*utilizados|cr[eé]ditos\s*utilizados)[^\d]*([\d\.]+)(?:\s*kwh)?",
            raw_text, re.IGNORECASE
        )
        or _find(
            r"(?:energia\s+injetad|gera[\u00e7c][\u00e3a]o\s+(?:fora|ponta|total)|ger\.\s+(?:fora|ponta))"
            r"[^\n]{0,80}?([\d]{1,3}(?:\.\d{3})+,\d+|\d+,\d{2}(?=-))",
            raw_text
        )
    )
    if geracao_text:
        result["geracao_kwh"] = _normalize_number(geracao_text)

    # Consumos Detalhados e Preços Unitários (NOVOS REGEX VALIDADOS)
    
    # 1. Quantidades
    result["demanda_ativa"] = _find(r'Demanda Ativa\(?kW\)?\s+([\d.,]+)', raw_text)
    result["consumo_ativo_na_ponta_tusd"] = (
        _find(r'Consumo-TUSD NPonta kWh\s+([\d.,]+)', raw_text)
        or _find(r'Consumo Ativo Na Ponta\(kWh\)-TUSD\s+([\d.,]+)', raw_text) # Grupo A
    )
    result["consumo_ativo_fora_ponta_tusd"] = (
        _find(r'Consumo-TUSD F\.Ponta kWh\s+([\d.,]+)', raw_text)
        or _find(r'Consumo Ativo Fora de Ponta\(kWh\)-TUSD\s+([\d.,]+)', raw_text) # Grupo A
    )
    result["demanda_reativa_excedente"] = _find(
        r"Demanda\s+Reativa\s+Exc\w*\.?\s*\(?kVAr\)?\s+([\d.,]+)", raw_text
    )
    result["consumo_reativo_exc_na_ponta"] = _find(
        r'Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)\s+([\d.,]+)', raw_text
    )
    result["consumo_reativo_exc_fora_ponta"] = _find(
        r'Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)\s+([\d.,]+)', raw_text
    )

    # 2. Preços Unitários
    result["demanda_ativa_preco_unitario"] = _find(r'Demanda Ativa\(?kW\)?\s+[\d.,]+\s+([\d.,]+)', raw_text)
    result["demanda_reativa_excedente_preco_unitario"] = _find(
        r'Demanda\s+Reativa\s+Exc\w*\.?\s*\(?kVAr\)?\s+[\d.,]+\s+([\d.,]+)', raw_text
    )
    result["consumo_ativo_na_ponta_tusd_preco_unitario"] = (
        _find(r'Consumo-TUSD NPonta kWh\s+[\d.,]+\s+([\d.,]+)', raw_text)
        or _find(r'Consumo Ativo Na Ponta\(kWh\)-TUSD\s+[\d.,]+\s+([\d.,]+)', raw_text) # Grupo A
    )
    result["consumo_ativo_fora_ponta_tusd_preco_unitario"] = (
        _find(r'Consumo-TUSD F\.Ponta kWh\s+[\d.,]+\s+([\d.,]+)', raw_text)
        or _find(r'Consumo Ativo Fora de Ponta\(kWh\)-TUSD\s+[\d.,]+\s+([\d.,]+)', raw_text) # Grupo A
    )
    result["consumo_ativo_na_ponta_te_preco_unitario"] = (
        _find(r"Consumo-TE\s+Na\s+Ponta\s+kWh\s+[\d.,]+\s+([\d.,]+)", raw_text)
        or _find(r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)", raw_text)
    )
    result["consumo_ativo_fora_ponta_te_preco_unitario"] = (
        _find(r"Consumo-TE\s+F\.?Ponta\s+kWh\s+[\d.,]+\s+([\d.,]+)", raw_text)
        or _find(r"Consumo\s+Ativo\s+Fora\s+(?:de\s+)?Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)", raw_text)
    )
    result["consumo_reativo_exc_na_ponta_preco_unitario"] = _find(
        r'Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)\s+[\d.,]+\s+([\d.,]+)', raw_text
    )
    result["consumo_reativo_exc_fora_ponta_preco_unitario"] = _find(
        r'Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)\s+[\d.,]+\s+([\d.,]+)', raw_text
    )

    return result


# ---------------------------------------------------------------------------
# Função principal — ponto de entrada do bill_service
# ---------------------------------------------------------------------------

def extract_bill_data(
    raw_text: str,
    tables: Optional[List[List[List[str]]]] = None
) -> Tuple[Dict[str, Any], float]:
    """
    Extrai dados estruturados da fatura combinando tabelas + texto.

    Args:
        raw_text:  Texto bruto extraído via OCR ou pdfplumber.
        tables:    Lista de tabelas do pdfplumber (opcional, para PDFs digitais).

    Returns:
        Tupla (dados_extraidos: dict, confidence_score: float).
        O score indica o quão completa foi a extração (0.0–1.0).
        Score < 0.5 → acionar IA como fallback.
    """
    result: Dict[str, Any] = {}

    # 1ª passagem: tabelas estruturadas (maior precisão)
    if tables:
        table_data = extract_from_tables(tables)
        result.update({k: v for k, v in table_data.items() if v is not None})

    # 2ª passagem: campos de texto (cabeçalho, datas, metadados)
    text_data = extract_from_text(raw_text)
    # Só substitui se o campo ainda não foi preenchido pelas tabelas
    for key, value in text_data.items():
        if value is not None and result.get(key) is None:
            result[key] = value

    confidence = _calculate_confidence(result)
    print(f"DEBUG (extraction): score de confiança = {confidence:.2f} ({sum(1 for v in result.values() if v)} campos preenchidos)")

    return result, confidence


# ---------------------------------------------------------------------------
# Mantido para compatibilidade com preprocess_text (usado no refinement fallback)
# ---------------------------------------------------------------------------

def preprocess_text(text: str) -> str:
    """Limpeza básica do texto OCR para normalização de espaços e caracteres."""
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
