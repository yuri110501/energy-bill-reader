"""
extraction.py
-------------
Camada Core responsável pela extração de dados usando Regex.
"""

import os
import re
import nltk
from nltk.corpus import stopwords
from typing import Dict, Any

NLTK_DATA_PATH = os.environ.get("NLTK_DATA", "/usr/local/share/nltk_data")
if NLTK_DATA_PATH not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_PATH)

def ensure_nltk_data():
    try:
        stopwords.words("portuguese")
    except LookupError:
        nltk.download("stopwords", download_dir=NLTK_DATA_PATH)
        if NLTK_DATA_PATH not in nltk.data.path:
            nltk.data.path.append(NLTK_DATA_PATH)

def preprocess_text(text: str) -> str:
    """Limpa e normaliza o texto extraído por OCR."""
    ensure_nltk_data()
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9à-ú\s,.:/-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = re.findall(r"[\wÀ-ú]+", text, flags=re.UNICODE)
    stop_words = set(stopwords.words("portuguese"))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    return " ".join(filtered_tokens)

def _find(pattern: str, text: str, flags=0) -> str | None:
    """Aplica regex e retorna o primeiro grupo capturado não-vazio, ou None."""
    match = re.search(pattern, text, re.IGNORECASE | flags)
    if not match:
        return None
    for g in match.groups():
        if g and g.strip():
            return g.strip()
    return None

def extract_bill_data(text: str) -> Dict[str, Any]:
    """
    Extrai campos de uma conta de energia elétrica via regex.
    """
    if not text:
        return {}

    # --- Padrões de extração ---
    cpf_cnpj_pattern = r"(?:DADOS\s+DO\s+CLIENTE|NOME\s+DO\s+CLIENTE)[\s\S]{0,500}?(?:CNPJ|CNPU|CPF)[:\s]*((\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/]?\d{4}[-\s]?\d{2}|\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\s]?\d{2}))"
    vencimento_pattern = r"(?:vencimento|data\s+de\s+vencimento|vence\s+em)[\s\S]{0,150}?([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})"
    referencia_pattern = r"REF[:\.]?M[EÊ]S[\/\s]?ANO[\s\S]{0,50}?\n.*?((?:0[1-9]|1[0-2])\/20[0-9]{2})"
    referencia_pattern2 = r"^((?:0[1-9]|1[0-2])\/20[0-9]{2})\s+[\d\.,]+\s+\d{2}\/\d{2}\/\d{4}"
    referencia_pattern3 = r"(?:DADOS\s+DO\s+CLIENTE|NOME)[\s\S]{0,200}?\d{2}\/\d{2}\/\d{4}\s+(\d{2}\/\d{2}\/\d{4})\s+\d+"
    valor_total_pattern = r"(?:total\s+a\s+pagar|valor\s+total|total\s+da\s+fatura|valor\s+a\s+pagar|total)[:\s]*R?\$?\s*([\d\.,]+)"
    leitura_atual_pattern = r"\d+\s+Energia\s+Ativa\s+[^\n]+?[\d\.]+,\d+\s+([\d\.]+,\d+)\s+[\d\.]+,\d+"
    leitura_anterior_pattern = r"\d+\s+Energia\s+Ativa\s+[^\n]+?([\d\.]+,\d+)\s+[\d\.]+,\d+\s+[\d\.]+,\d+"
    instalacao_pattern = r"N[°ºº]?\s*DA\s+INSTALA[CÇ][AÃ]O\s*\n[^\n]+(\d{7})\s*$"
    numero_fatura_pattern = r"NOTA\s+FISCAL[^\n]*\n[^\n]+?(\d{9})\s+\d{7}"
    distribuidora_pattern = r"(?:distribuidora|concession[aá]ria)[:\s]*(.+?)(?:\n|$)"
    distribuidora_nome_pattern = r"\b(celpe|neoenergia(?:pernambuco)?|cemig|copel|enel|light|coelba|energisa|equatorial|elektro|cpfl|rge|cosern|ceal|ceron|amazonas\s*energia)\b"
    distribuidora_celpe_pattern = r"(COMPANHIA\s+ENERG[EÉ]TICA\s+DE\s+PERNAMBUCO)"
    bandeira_pattern = r"(?:BANDEIRA|Band\.?\s+)[:\s]*(VERDE|AMARELA|VERMELHA\s+PATAMAR\s+[12]|ESCASSEZ\s+H[IÍ]DRICA)"
    fornecimento_pattern = r"(monof[aá]sico|bif[aá]sico|trif[aá]sico)"
    tarifa_pattern = r"(?:tarifa|te\s+\+\s+tusd)[:\s]*R?\$?\s*([\d\.,]+)"
    
    # Grupo A
    demanda_ativa_pattern = r"Demanda\s+Ativa\(kW\)[\s]*([\d\.,]+)"
    demanda_reativa_pattern = r"Demanda\s+Reativ[oa].*?\(kVAR\)[^\d]*([\d\.,]+)"
    demanda_reativo_ponta_pattern = r"Demanda\s+Reativ[oa]\s+(?:Na\s+)?Ponta.*?[\s]*([\d\.,]+)"
    demanda_reativo_fora_ponta_pattern = r"Demanda\s+Reativ[oa]\s+Fora\s+(?:de\s+)?Ponta.*?[\s]*([\d\.,]+)"
    consumo_ponta_tusd_pattern = r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-\s*TUSD[\s]*([\d\.,]+)"
    consumo_fora_ponta_tusd_pattern = r"Consumo\s+Ativo\s+Fora\s+de\s+Ponta\(kWh\)-TUSD[\s]*([\d\.,]+)"
    consumo_ponta_te_pattern = r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-TE[\s]*([\d\.,]+)"
    consumo_fora_ponta_te_pattern = r"Consumo\s+Ativo\s+Fora\s+Ponta\(kWh\)-TE[\s]*([\d\.,]+)"
    reativo_exc_ponta_pattern = r"Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)[\s]*([\d\.,]+)"
    reativo_exc_fora_ponta_pattern = r"Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)[\s]*([\d\.,]+)"
    geracao_pattern = r"(?i)(?:Consumo\s+Ativo\s+Fora\s+de\s+Ponta|Gera[çc][ãa]o).*?([\d\.,]+)-"

    codigo_cliente_pattern = r"(\d{10})\s+\d{2}\/\d{2}\/\d{4}\s+[\d\.,]+\s*\nC[OÓ]DIGO\s+DO\s+CLIENTE\s+VENCIMENTO"
    codigo_cliente_tabela_pattern = r"N[°º]\s+DO\s+CLIENTE\s*\n[^\n]+?(\d{10})\s*(?:\n|$)"
    codigo_cliente_boleto_dados_pattern = r"\d{6,}\s+(\d{10})\s+\d{2}\/\d{2}\/\d{4}"
    data_leitura_anterior_pattern = r"(?:leitura\s+anterior)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})"
    data_leitura_atual_pattern = r"(?:leitura\s+atual)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})"
    numero_dias_faturamento_pattern = r"(?:n[º°]?\s+de\s+dias)[:\s]*(\d+)"
    classificacao_pattern = r"[CG]LASSIFICA[ÇC][ÃA]O[:\s]*(?:\n)([^\n]+)"
    classificacao_inline_pattern = r"[CG]LASSIFICA[ÇC][ÃA]O[:\s]*([A-Za-z][\w\s\-]{2,30}?(?:COMERCIAL|RESIDENCIAL|INDUSTRIAL|RURAL))"
 
    demanda_ativa_preco_pattern = r"Demanda\s+Ativa\(kW\)[^\d]*(?:[\d\.,]+)[^\d]+([\d\.,]+)"
    demanda_reativa_preco_pattern = r"Demanda\s+Reativ[oa].*?\(kVAR\)[^\d]*(?:[\d\.,]+)[^\d]+([\d\.,]+)"
    consumo_ponta_tusd_preco_pattern = r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-\s*TUSD[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"
    consumo_fora_ponta_tusd_preco_pattern = r"Consumo\s+Ativo\s+Fora\s+de\s+Ponta\(kWh\)-TUSD[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"
    consumo_ponta_te_preco_pattern = r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"
    consumo_fora_ponta_te_preco_pattern = r"Consumo\s+Ativo\s+Fora\s+Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"
    reativo_exc_ponta_preco_pattern = r"Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"
    reativo_exc_fora_ponta_preco_pattern = r"Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"

    # --- Extração ---
    cpf_cnpj_raw = _find(cpf_cnpj_pattern, text)
    cpf_cnpj = cpf_cnpj_raw if cpf_cnpj_raw and cpf_cnpj_raw.replace(".","").replace("/","").replace("-","") not in {"10835932000108"} else None

    vencimento = _find(vencimento_pattern, text)
    referencia = (
        _find(referencia_pattern, text) or
        _find(referencia_pattern2, text, flags=re.MULTILINE) or
        _find(referencia_pattern3, text)
    )
    if referencia and '/' in referencia and len(referencia) == 10:
        parts = referencia.split('/')
        referencia = f"{parts[1]}/{parts[2]}"

    valor_total = _find(valor_total_pattern, text)
    geracao = _find(geracao_pattern, text)
    leitura_atual = _find(leitura_atual_pattern, text)
    leitura_anterior = _find(leitura_anterior_pattern, text)
    
    consumo_ponta_te = _find(consumo_ponta_te_pattern, text)
    consumo_fora_ponta_te = _find(consumo_fora_ponta_te_pattern, text)

    def _to_float(val):
        if not val: return 0.0
        try:
            return float(val.replace(".", "").replace(",", "."))
        except:
            return 0.0

    ponta_te_val = _to_float(consumo_ponta_te)
    fora_ponta_te_val = _to_float(consumo_fora_ponta_te)
    geracao_val = _to_float(geracao)
    
    consumo_total_val = ponta_te_val + fora_ponta_te_val + geracao_val
    
    if consumo_total_val == 0:
        atu_val = _to_float(leitura_atual)
        ant_val = _to_float(leitura_anterior)
        consumo_total_val = atu_val - ant_val
        if consumo_total_val < 0: consumo_total_val = 0

    consumo_total_kwh = f"{consumo_total_val:.2f}" if consumo_total_val > 0 else None

    distribuidora_raw = _find(distribuidora_pattern, text) or _find(distribuidora_nome_pattern, text)
    if not distribuidora_raw and _find(distribuidora_celpe_pattern, text):
        distribuidora_raw = "celpe"
    if distribuidora_raw and "neoenergia" in distribuidora_raw.lower():
        distribuidora_raw = "celpe"

    return {
        "distribuidora": distribuidora_raw,
        "cpf_cnpj_titular": cpf_cnpj,
        "numero_instalacao": _find(instalacao_pattern, text, flags=re.MULTILINE),
        "numero_fatura": _find(numero_fatura_pattern, text, flags=re.MULTILINE),
        "mes_referencia": referencia,
        "data_vencimento": vencimento,
        "valor_total": valor_total,
        "consumo_total_kwh": consumo_total_kwh,
        "geracao_kwh": geracao,
        "leitura_atual": leitura_atual,
        "leitura_anterior": leitura_anterior,
        "bandeira_tarifaria": _find(bandeira_pattern, text),
        "tipo_fornecimento": _find(fornecimento_pattern, text),
        "tarifa_rs_kwh": _find(tarifa_pattern, text),
        "demanda_ativa": _find(demanda_ativa_pattern, text),
        "demanda_reativa_excedente": _find(demanda_reativa_pattern, text),
        "demanda_reativo_ponta": _find(demanda_reativo_ponta_pattern, text),
        "demanda_reativo_fora_ponta": _find(demanda_reativo_fora_ponta_pattern, text),
        "consumo_ativo_na_ponta_tusd": _find(consumo_ponta_tusd_pattern, text),
        "consumo_ativo_fora_ponta_tusd": _find(consumo_fora_ponta_tusd_pattern, text),
        "consumo_ativo_na_ponta_te": consumo_ponta_te,
        "consumo_ativo_fora_ponta_te": consumo_fora_ponta_te,
        "consumo_reativo_exc_na_ponta": _find(reativo_exc_ponta_pattern, text),
        "consumo_reativo_exc_fora_ponta": _find(reativo_exc_fora_ponta_pattern, text),
        "codigo_cliente": _find(codigo_cliente_pattern, text) or _find(codigo_cliente_tabela_pattern, text) or _find(codigo_cliente_boleto_dados_pattern, text),
        "data_leitura_anterior": _find(data_leitura_anterior_pattern, text),
        "data_leitura_atual": _find(data_leitura_atual_pattern, text),
        "numero_dias_faturamento": _find(numero_dias_faturamento_pattern, text),
        "classificacao_detalhada": _find(classificacao_pattern, text, flags=re.MULTILINE) or _find(classificacao_inline_pattern, text),
        "demanda_ativa_preco_unitario": _find(demanda_ativa_preco_pattern, text),
        "demanda_reativa_excedente_preco_unitario": _find(demanda_reativa_preco_pattern, text),
        "consumo_ativo_na_ponta_tusd_preco_unitario": _find(consumo_ponta_tusd_preco_pattern, text),
        "consumo_ativo_fora_ponta_tusd_preco_unitario": _find(consumo_fora_ponta_tusd_preco_pattern, text),
        "consumo_ativo_na_ponta_te_preco_unitario": _find(consumo_ponta_te_preco_pattern, text),
        "consumo_ativo_fora_ponta_te_preco_unitario": _find(consumo_fora_ponta_te_preco_pattern, text),
        "consumo_reativo_exc_na_ponta_preco_unitario": _find(reativo_exc_ponta_preco_pattern, text),
        "consumo_reativo_exc_fora_ponta_preco_unitario": _find(reativo_exc_fora_ponta_preco_pattern, text),
    }
