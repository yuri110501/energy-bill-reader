"""
extraction.py
-------------
Motor de extração estruturada de faturas de energia baseado em perfis (rules-driven).
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from core.rules import REGEX_RULES

# Configuração de logging
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Campos críticos para cálculo de confiança
# ---------------------------------------------------------------------------
CRITICAL_FIELDS = [
    "distribuidora", "valor_total", "mes_referencia", "data_vencimento",
]

# ---------------------------------------------------------------------------
# Mapeamento de tabelas (mantido para o sensor primário)
# ---------------------------------------------------------------------------
TABLE_ROW_MAP: Dict[str, Dict[str, str]] = {
    "demanda ativa(kw)": {
        "quantity": "demanda_ativa",
        "price":    "demanda_ativa_preco_unitario",
    },
    "demanda ativa": { 
        "quantity": "demanda_ativa",
        "price":    "demanda_ativa_preco_unitario",
    },
    "demanda reativa excedente": {
        "quantity": "demanda_reativa_excedente",
        "price":    "demanda_reativa_excedente_preco_unitario",
    },
    "consumo ativo na ponta(kwh)-tusd": {
        "quantity": "consumo_ativo_na_ponta_tusd",
        "price":    "consumo_ativo_na_ponta_tusd_preco_unitario",
    },
    "consumo-tusd nponta": {
        "quantity": "consumo_ativo_na_ponta_tusd",
        "price":    "consumo_ativo_na_ponta_tusd_preco_unitario",
    },
    "consumo ativo fora de ponta(kwh)-tusd": {
        "quantity": "consumo_ativo_fora_ponta_tusd",
        "price":    "consumo_ativo_fora_ponta_tusd_preco_unitario",
    },
    "consumo-tusd f.ponta": {
        "quantity": "consumo_ativo_fora_ponta_tusd",
        "price":    "consumo_ativo_fora_ponta_tusd_preco_unitario",
    },
    "consumo-tusd": {
        "quantity": "consumo_ativo_fora_ponta_tusd",
        "price":    "consumo_ativo_fora_ponta_tusd_preco_unitario",
    },
    "cons.reat.exc.nponta": {
        "quantity": "consumo_reativo_exc_na_ponta",
        "price":    "consumo_reativo_exc_na_ponta_preco_unitario",
    },
    "cons.reat exc.fponta": {
        "quantity": "consumo_reativo_exc_fora_ponta",
    },
    "classificação:": {
        "value": "classificacao_detalhada"
    },
    "distribuidora:": {
        "value": "distribuidora"
    }
}

# ---------------------------------------------------------------------------
# Utilitários de Normalização
# ---------------------------------------------------------------------------

def _normalize_number(value: str) -> Optional[str]:
    """Converte formato brasileiro (1.234,56) para float string (1234.56)."""
    if not value: return None
    v = str(value).strip().rstrip("-").replace(" ", "")
    if re.search(r"\d\.\d{3},\d", v):
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        v = v.replace(",", ".")
    v = re.sub(r"[^\d.-]", "", v)
    try:
        return str(float(v))
    except ValueError:
        return None

def _calculate_confidence(data: Dict[str, Any]) -> float:
    """Calcula score de confiança baseado nos campos críticos."""
    filled = sum(1 for f in CRITICAL_FIELDS if data.get(f) and data[f] not in (None, "None", ""))
    return filled / len(CRITICAL_FIELDS)

# ---------------------------------------------------------------------------
# Motor de Extração (Core Engine)
# ---------------------------------------------------------------------------

def decide_profile(dist: str, classif: str, raw_text: str = "") -> str:
    """
    Decide o perfil de regras com base nas âncoras extraídas.
    """
    if not dist: return "Generico"
    
    dist_upper = dist.upper()
    classif_upper = classif.upper() if classif else ""
    raw_upper = raw_text.upper() if raw_text else ""
    
    is_neoenergia = any(k in dist_upper for k in ["CELPE", "PERNAMBUCO", "NEOENERGIA", "RIO GRANDE DO NORTE", "COSERN", "BAHIA","COELBA"])
    
    if is_neoenergia:
        # Prioridade 1: Classificação extraída
        if "A4" in classif_upper: return "Neoenergia_A"
        if "B3" in classif_upper: return "Neoenergia_B"
        if "B1" in classif_upper: return "Neoenergia_B1"
        
        '''
        Essa funcionalidade precisa ser implementada
        # Prioridade 2: Busca direta no texto bruto (fallback)
        if "A4" in raw_upper: return "Neoenergia_A"
        if "B3" in raw_upper: return "Neoenergia_B"
        if "B1" in raw_upper: return "Neoenergia_B1"
        '''
        
    return "Generico"

def apply_rules(text: str, profile: str) -> Dict[str, Any]:
    """Aplica o dicionário de regras."""
    rules = REGEX_RULES.get(profile, REGEX_RULES["Generico"])
    extracted = {}
    
    for category, fields in rules.items():
        for field, pattern in fields.items():
            # Usa DOTALL apenas para o código do cliente se necessário, 
            # ou lidamos com [\s\S] no pattern para ser universal
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    val = None
                    for i in range(1, len(match.groups()) + 1):
                        if match.group(i):
                            val = match.group(i).strip()
                            break
                    if not val:
                        val = match.group(0).strip()
                except IndexError:
                    val = match.group(0).strip()
                
                if val:
                    if category in ["technical", "tariffs"] or field == "valor_total":
                        val = _normalize_number(val)
                    extracted[field] = val
                    
    return extracted

# ---------------------------------------------------------------------------
# Sensores de Extração
# ---------------------------------------------------------------------------

def extract_from_tables(tables: List[List[List[str]]]) -> Dict[str, Any]:
    """Extração primária baseada na estrutura nativa de tabelas do PDF."""
    result = {}
    for table in tables:
        for row in table:
            cells = [str(c).strip() if c else "" for c in row]
            if not cells or not cells[0]: continue
            desc = cells[0].lower()

            for key, mapping in TABLE_ROW_MAP.items():
                if key in desc:
                    if "value" in mapping:
                        val = re.sub(rf"(?i){re.escape(key)}", "", cells[0]).strip()
                        if val: 
                            val = val.replace("\n", " ").strip()
                            val = re.sub(r"\s{2,}", " ", val)
                            result[mapping["value"]] = val
                        continue

                    if len(cells) > 1 and mapping.get("quantity"):
                        val = _normalize_number(cells[3]) if len(cells) > 3 else _normalize_number(cells[1])
                        if val: result[mapping["quantity"]] = val
                    
                    if len(cells) > 2 and mapping.get("price"):
                        val = _normalize_number(cells[4]) if len(cells) > 4 else _normalize_number(cells[2])
                        if val: result[mapping["price"]] = val
                    break
    return result

def extract_bill_data(raw_text: str, tables: Optional[List[List[List[str]]]] = None) -> Tuple[Dict[str, Any], float]:
    """
    Ponto de entrada principal com roteamento inteligente por âncoras.
    """
    result = {}
    
    # 1. Gera texto das tabelas para o Regex (auxiliar)
    processed_text = ""
    if tables:
        for table in tables:
            for row in table:
                processed_text += " ".join([str(c) for c in row if c]) + "\n"

    # 2. PASSO 1: Extrair Âncoras (Distribuidora e Classificação)
    if tables:
        result.update(extract_from_tables(tables))
    
    # Tenta via Regex Genérico para preencher o que faltar das âncoras
    anchor_data = apply_rules(raw_text, "Generico")
    for k in ["distribuidora", "classificacao_detalhada"]:
        if k not in result or not result[k]:
            result[k] = anchor_data.get(k)

    # 3. PASSO 2: Decidir Perfil e Extrair Dados Técnicos
    profile = decide_profile(
        result.get("distribuidora", ""), 
        result.get("classificacao_detalhada", ""),
        raw_text
    )
    
    # Aplica as regras do perfil decidido (Celpe_A, Celpe_B, etc)
    # Testa no texto original E no texto reconstruído das tabelas
    for text_to_parse in [raw_text, processed_text]:
        specific_data = apply_rules(text_to_parse, profile)
        for k, v in specific_data.items():
            if v and (not result.get(k) or result.get(k) == "None"):
                result[k] = v
                
        # Fallback genérico para campos universais (Vencimento, Total, etc)
        generic_data = apply_rules(text_to_parse, "Generico")
        for k, v in generic_data.items():
            if v and (not result.get(k) or result.get(k) == "None"):
                result[k] = v

    confidence = _calculate_confidence(result)
    print(f"DEBUG (extraction): score={confidence:.2f} | profile={profile} | anchors=[{result.get('distribuidora')}, {result.get('classificacao_detalhada')}]")

    return result, confidence

def preprocess_text(text: str) -> str:
    """Limpeza básica do texto OCR."""
    if not text: return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
