"""
refinement_utils.py
-------------------
Refina os dados extraídos por regex usando a Claude API.
Se a chave ANTHROPIC_API_KEY não estiver configurada, usa
fallback local (regex adicional) sem chamar nenhuma API externa.
"""

import os
import json
import re

BILL_FIELDS = [
    "distribuidora",
    "cpf_cnpj_titular",
    "endereco_titular",
    "numero_instalacao",
    "numero_fatura",
    "mes_referencia",
    "data_vencimento",
    "valor_total",
    "consumo_kwh",
    "leitura_atual",
    "leitura_anterior",
    "bandeira_tarifaria",
    "tipo_fornecimento",
    "classe_consumidor",
    "tarifa_rs_kwh",
]

DEFAULT_OUTPUT = {field: "None" for field in BILL_FIELDS}

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

PROMPT_TEMPLATE = (
    "Você é um especialista em leitura de contas de energia elétrica brasileiras.\n"
    "Analise os dados extraídos abaixo e o texto original da conta.\n"
    "Retorne APENAS um JSON com exatamente estes campos (sem texto fora do JSON):\n\n"
    "{\n"
    '  "distribuidora": "None",\n'
    '  "cpf_cnpj_titular": "None",\n'
    '  "endereco_titular": "None",\n'
    '  "numero_instalacao": "None",\n'
    '  "numero_fatura": "None",\n'
    '  "mes_referencia": "None",\n'
    '  "data_vencimento": "None",\n'
    '  "valor_total": "None",\n'
    '  "consumo_kwh": "None",\n'
    '  "leitura_atual": "None",\n'
    '  "leitura_anterior": "None",\n'
    '  "bandeira_tarifaria": "None",\n'
    '  "tipo_fornecimento": "None",\n'
    '  "classe_consumidor": "None",\n'
    '  "tarifa_rs_kwh": "None"\n'
    "}\n\n"
    "Regras de formatação:\n"
    "- valor_total: apenas o número (ex: '127.45')\n"
    "- consumo_kwh: apenas o número inteiro (ex: '342')\n"
    "- data_vencimento: DD/MM/AAAA\n"
    "- mes_referencia: MM/AAAA ou 'Janeiro/2024'\n"
    "- bandeira_tarifaria: 'Verde', 'Amarela', 'Vermelha Patamar 1' ou 'Vermelha Patamar 2'\n"
    "- Campo não identificado: coloque 'None'\n\n"
    "Dados extraídos inicialmente:\n"
)


def build_prompt(bill_data: dict, processed_text: str) -> str:
    return (
        PROMPT_TEMPLATE
        + json.dumps(bill_data, indent=2, ensure_ascii=False)
        + "\n\nTexto da conta de energia:\n"
        + processed_text
        + "\n\nRetorne apenas o JSON válido."
    )


def refine_data_local(bill_data: dict, raw_text: str, processed_text: str) -> dict:
    """
    Tenta refinar via Claude API. Se não estiver configurada, usa fallback regex.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if HAS_ANTHROPIC and api_key:
        try:
            return _refine_with_claude(bill_data, processed_text, api_key)
        except Exception as exc:
            print(f"DEBUG (refinement): Claude API falhou, usando fallback: {exc}")

    return _refine_fallback(bill_data, raw_text, processed_text)


def _refine_with_claude(bill_data: dict, processed_text: str, api_key: str) -> dict:
    """Chama a Claude API para corrigir e completar os campos extraídos."""
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(bill_data, processed_text)

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    raw_response = message.content[0].text
    print(f"DEBUG (refinement): Resposta Claude (primeiros 500 chars): {raw_response[:500]}")
    return _parse_json_response(raw_response)


def _parse_json_response(raw: str) -> dict:
    """Extrai o JSON da resposta da IA e valida os campos."""
    match = re.search(r"(\{[\s\S]*\})", raw)
    cleaned = match.group(1) if match else raw.strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON inválido retornado pela IA: {exc}\n{cleaned}")

    for field in BILL_FIELDS:
        if field not in data:
            data[field] = "None"

    return {field: _normalize(data.get(field)) for field in BILL_FIELDS}


def _refine_fallback(bill_data: dict, raw_text: str, processed_text: str) -> dict:
    """
    Fallback 100% local: combina os dados já extraídos por regex
    com tentativas extras de padrões alternativos.
    """
    result = DEFAULT_OUTPUT.copy()
    for field in BILL_FIELDS:
        result[field] = _normalize(bill_data.get(field))

    extras = {
        "distribuidora": [
            r"(celpe|cemig|copel|enel|light|coelba|energisa|equatorial|elektro|cpfl|rge|cosern|ceal|ceron|amazonas\s*energia)[^\n]*",
        ],
        "data_vencimento": [
            r"(?:vence|vencimento|pague\s+at[eé])[:\s]*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})",
            r"([0-9]{2}[\/][0-9]{2}[\/][0-9]{4})",
        ],
        "valor_total": [
            r"(?:total|pagar|fatura)[:\s]*R?\$?\s*([0-9]{1,4}[,\.][0-9]{2})",
        ],
        "consumo_kwh": [
            r"([0-9]+(?:[,\.][0-9]+)?)\s*kwh",
        ],
        "bandeira_tarifaria": [
            r"\b(verde|amarela|vermelha)\b",
        ],
        "mes_referencia": [
            r"((?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)[\/\s]*[0-9]{4})",
            r"([0-9]{2}[\/][0-9]{4})",
        ],
    }

    for field, patterns in extras.items():
        if result[field] == "None":
            for p in patterns:
                val = _find(p, raw_text) or _find(p, processed_text)
                if val:
                    result[field] = _normalize(val)
                    break

    return result


def _find(pattern: str, text: str):
    if not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip() if match.lastindex else match.group(0).strip()
    return None


def replace_null_with_none(value):
    if isinstance(value, dict):
        return {k: replace_null_with_none(v) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_null_with_none(i) for i in value]
    return "None" if value is None else value


def _normalize(value) -> str:
    if value is None:
        return "None"
    if isinstance(value, str):
        value = value.strip()
        return value if value else "None"
    return str(value)
