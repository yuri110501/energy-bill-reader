import os
import re
import nltk
from nltk.corpus import stopwords

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


def preprocess_text(text):
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


def extract_bill_data(text):
    """
    Extrai campos de uma conta de energia elétrica via regex.
    Retorna dicionário com os campos definidos em BILL_FIELDS.
    """
    if not text:
        return _empty_bill()

    # --- Padrões de extração ---
    # CPF/CNPJ do titular
    cpf_pattern = r"(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}-\d{2})"
    cnpj_pattern = r"(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/]?\d{4}[-\s]?\d{2})"

    # Data de vencimento
    vencimento_pattern = r"(?:vencimento|data\s+de\s+vencimento|vence\s+em)[:\s]*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})"

    # Mês/competência de referência
    referencia_pattern = r"(?:referente?\s+a|compet[eê]ncia|m[eê]s\s+de\s+refer[eê]ncia|per[ií]odo)[:\s]*([a-zA-Záàâãéêíóôõú]+[\s\/]*[0-9]{4}|[0-9]{2}[\/][0-9]{4})"

    # Valor total a pagar
    valor_total_pattern = r"(?:total\s+a\s+pagar|valor\s+total|total\s+da\s+fatura|valor\s+a\s+pagar|total)[:\s]*R?\$?\s*([\d\.,]+)"

    # Consumo em kWh
    consumo_kwh_pattern = r"(?:consumo|energia\s+ativa|kwh\s+consumido)[:\s]*([\d\.,]+)\s*kwh"

    # Leitura anterior e atual
    leitura_atual_pattern = r"(?:leitura\s+atual|medida\s+atual)[:\s]*([\d\.,]+)"
    leitura_anterior_pattern = r"(?:leitura\s+anterior|medida\s+anterior)[:\s]*([\d\.,]+)"

    # Número da instalação / unidade consumidora
    instalacao_pattern = r"(?:n[uú]mero\s+da\s+instala[cç][aã]o|instala[cç][aã]o|unidade\s+consumidora|n[°º]?\s*uc)[:\s]*([0-9A-Z\-]+)"

    # Número da fatura / nota
    numero_fatura_pattern = r"(?:nota\s+fiscal|nf|n[uú]mero\s+da\s+fatura|fatura\s+n[°º]?)[:\s]*([0-9A-Z\-]+)"

    # Distribuidora (nome da empresa)
    distribuidora_pattern = r"(?:distribuidora|concession[aá]ria)[:\s]*(.+?)(?:\n|$)"

    # Endereço do titular
    endereco_pattern = r"((?:rua|av\.?|avenida|rodovia|al\.?|logradouro)[^\n]+)"

    # Bandeira tarifária
    bandeira_pattern = r"(?:bandeira)[:\s]*(verde|amarela|vermelha\s+patamar\s+[12]|escassez\s+h[ií]drica)"

    # Tipo de fornecimento (monofásico, bifásico, trifásico)
    fornecimento_pattern = r"(monof[aá]sico|bif[aá]sico|trif[aá]sico)"

    # Classe do consumidor
    classe_pattern = r"(?:classe|grupo)[:\s]*(residencial|comercial|industrial|rural|poder\s+p[uú]blico)"

    # Tarifa (R$/kWh)
    tarifa_pattern = r"(?:tarifa|te\s+\+\s+tusd)[:\s]*R?\$?\s*([\d\.,]+)"

    # --- Aplicar extração ---
    cpf_cnpj = re.findall(cpf_pattern, text) or re.findall(cnpj_pattern, text)
    vencimento = _find(vencimento_pattern, text)
    referencia = _find(referencia_pattern, text)
    valor_total = _find(valor_total_pattern, text)
    consumo_kwh = _find(consumo_kwh_pattern, text)
    leitura_atual = _find(leitura_atual_pattern, text)
    leitura_anterior = _find(leitura_anterior_pattern, text)
    instalacao = _find(instalacao_pattern, text)
    numero_fatura = _find(numero_fatura_pattern, text)
    distribuidora = _find(distribuidora_pattern, text)
    endereco = re.findall(endereco_pattern, text, re.IGNORECASE)
    bandeira = _find(bandeira_pattern, text)
    fornecimento = _find(fornecimento_pattern, text)
    classe = _find(classe_pattern, text)
    tarifa = _find(tarifa_pattern, text)

    return {
        "distribuidora": distribuidora,
        "cpf_cnpj_titular": cpf_cnpj[0].strip() if cpf_cnpj else None,
        "endereco_titular": endereco[0].strip() if endereco else None,
        "numero_instalacao": instalacao,
        "numero_fatura": numero_fatura,
        "mes_referencia": referencia,
        "data_vencimento": vencimento,
        "valor_total": valor_total,
        "consumo_kwh": consumo_kwh,
        "leitura_atual": leitura_atual,
        "leitura_anterior": leitura_anterior,
        "bandeira_tarifaria": bandeira,
        "tipo_fornecimento": fornecimento,
        "classe_consumidor": classe,
        "tarifa_rs_kwh": tarifa,
    }


def _find(pattern, text):
    """Aplica regex e retorna o primeiro grupo capturado, ou None."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _empty_bill():
    """Retorna dicionário vazio com todos os campos da conta."""
    return {
        "distribuidora": None,
        "cpf_cnpj_titular": None,
        "endereco_titular": None,
        "numero_instalacao": None,
        "numero_fatura": None,
        "mes_referencia": None,
        "data_vencimento": None,
        "valor_total": None,
        "consumo_kwh": None,
        "leitura_atual": None,
        "leitura_anterior": None,
        "bandeira_tarifaria": None,
        "tipo_fornecimento": None,
        "classe_consumidor": None,
        "tarifa_rs_kwh": None,
    }


def validate_cpf_cnpj(doc):
    """Valida se o documento tem 11 dígitos (CPF) ou 14 dígitos (CNPJ)."""
    if not doc:
        return False
    cleaned = re.sub(r"\D", "", str(doc))
    return len(cleaned) in (11, 14)
