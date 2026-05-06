"""
refinement_utils.py
-------------------
Refina os dados extraídos por regex usando o Gemini (Google AI).
Se a chave GOOGLE_API_KEY não estiver configurada, usa
fallback local (regex adicional + regra de negócio) sem chamar API externa.
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
    "consumo_total_kwh",
    "geracao_kwh",
    "leitura_atual",
    "leitura_anterior",
    "bandeira_tarifaria",
    "tipo_fornecimento",
    "classe_consumidor",
    "tarifa_rs_kwh",
    "demanda_ativa",
    "demanda_reativa_excedente",
    "consumo_ativo_na_ponta_tusd",
    "consumo_ativo_fora_ponta_tusd",
    "consumo_ativo_na_ponta_te",
    "consumo_ativo_fora_ponta_te",
    "consumo_reativo_exc_na_ponta",
    "consumo_reativo_exc_fora_ponta",
    "codigo_cliente",
    "data_leitura_anterior",
    "data_leitura_atual",
    "numero_dias_faturamento",
    "demanda_contratada",
    "classificacao_detalhada",
    "demanda_ativa_preco_unitario",
    "demanda_reativa_excedente_preco_unitario",
    "consumo_ativo_na_ponta_tusd_preco_unitario",
    "consumo_ativo_fora_ponta_tusd_preco_unitario",
    "consumo_ativo_na_ponta_te_preco_unitario",
    "consumo_ativo_fora_ponta_te_preco_unitario",
    "consumo_reativo_exc_na_ponta_preco_unitario",
    "consumo_reativo_exc_fora_ponta_preco_unitario",
]

DEFAULT_OUTPUT = {field: "None" for field in BILL_FIELDS}

# Modelo configurável via variável de ambiente (padrão: gemini-2.5-flash)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

PROMPT_TEMPLATE = (
    "Você é um especialista em leitura de contas de energia elétrica brasileiras.\n"
    "Analise os dados extraídos abaixo e o texto original da conta.\n"
    "Retorne APENAS um JSON válido com exatamente estes campos (sem texto fora do JSON):\n\n"
    "{\n"
    '  "distribuidora": "None",\n'
    '  "cpf_cnpj_titular": "None",\n'
    '  "endereco_titular": "None",\n'
    '  "numero_instalacao": "None",\n'
    '  "numero_fatura": "None",\n'
    '  "mes_referencia": "None",\n'
    '  "data_vencimento": "None",\n'
    '  "valor_total": "None",\n'
    '  "consumo_total_kwh": "None",\n'
    '  "geracao_kwh": "None",\n'
    '  "leitura_atual": "None",\n'
    '  "leitura_anterior": "None",\n'
    '  "bandeira_tarifaria": "None",\n'
    '  "tipo_fornecimento": "None",\n'
    '  "classe_consumidor": "None",\n'
    '  "tarifa_rs_kwh": "None",\n'
    '  "demanda_ativa": "None",\n'
    '  "demanda_reativa_excedente": "None",\n'
    '  "consumo_ativo_na_ponta_tusd": "None",\n'
    '  "consumo_ativo_fora_ponta_tusd": "None",\n'
    '  "consumo_ativo_na_ponta_te": "None",\n'
    '  "consumo_ativo_fora_ponta_te": "None",\n'
    '  "consumo_reativo_exc_na_ponta": "None",\n'
    '  "consumo_reativo_exc_fora_ponta": "None",\n'
    '  "codigo_cliente": "None",\n'
    '  "data_leitura_anterior": "None",\n'
    '  "data_leitura_atual": "None",\n'
    '  "numero_dias_faturamento": "None",\n'
    '  "demanda_contratada": "None",\n'
    '  "classificacao_detalhada": "None",\n'
    '  "demanda_ativa_preco_unitario": "None",\n'
    '  "demanda_reativa_excedente_preco_unitario": "None",\n'
    '  "consumo_ativo_na_ponta_tusd_preco_unitario": "None",\n'
    '  "consumo_ativo_fora_ponta_tusd_preco_unitario": "None",\n'
    '  "consumo_ativo_na_ponta_te_preco_unitario": "None",\n'
    '  "consumo_ativo_fora_ponta_te_preco_unitario": "None",\n'
    '  "consumo_reativo_exc_na_ponta_preco_unitario": "None",\n'
    '  "consumo_reativo_exc_fora_ponta_preco_unitario": "None"\n'
    "}\n\n"
    "Regras de formatação:\n"
    "- Valores numéricos: use apenas o número com ponto como separador decimal (ex: '127.45')\n"
    "- Consumos e Demandas: capture a QUANTIDADE na primeira coluna numérica (ex: 200.00).\n"
    "- Preços Unitários (_preco_unitario): capture o valor da tarifa/preço unitário aplicado (geralmente possui 4 ou mais casas decimais, ex: 24.50994627 ou 0.58363583).\n"
    "- consumo_total_kwh: CALCULE a soma de 'Consumo Ativo Na Ponta(kWh)-TE' + 'Consumo Ativo Fora Ponta(kWh)-TE' + 'geracao_kwh' (se houver).\n"
    "- geracao_kwh: capture o valor numérico que aparece antes de um sinal '-' (ex: capture '8379.98' de '8.379,98-').\n"
    "- demanda_ativa: procure por 'Demanda Ativa(kW)'.\n"
    "- consumo_ativo_na_ponta: procure por 'Consumo Ativo Na Ponta(kWh)' diferenciando TUSD de TE.\n"
    "- consumo_reativo_exc: procure por 'Consumo Reativo Exc.' na Ponta ou Fora Ponta.\n"
    "- data_leitura_anterior, data_leitura_atual: capture no formato DD/MM/AAAA\n"
    "- codigo_cliente, numero_dias_faturamento, demanda_contratada: capture apenas os números\n"
    "- classificacao_detalhada: capture a string completa (ex: 'A4 Horo-sazonal Verde')\n"
    "- data_vencimento: DD/MM/AAAA\n"
    "- mes_referencia: MM/AAAA ou 'Janeiro/2024'\n"
    "- bandeira_tarifaria: 'Verde', 'Amarela', 'Vermelha Patamar 1' ou 'Vermelha Patamar 2'\n"
    "- distribuidora: nome da empresa distribuidora (ex: 'Celpe', 'Cemig', 'Enel')\n"
    "- Campo não identificado: coloque 'None'\n\n"
    "Dados extraídos inicialmente pela regex:\n"
)


def build_prompt(bill_data: dict, raw_text: str) -> str:
    return (
        PROMPT_TEMPLATE
        + json.dumps(bill_data, indent=2, ensure_ascii=False)
        + "\n\nTexto completo da conta de energia (extraído via OCR):\n"
        + raw_text[:4000]  # Limita para não extrapolar o contexto
        + "\n\nRetorne apenas o JSON válido, sem blocos de código markdown."
    )


def refine_data_local(bill_data: dict, raw_text: str, processed_text: str) -> dict:
    """
    Tenta refinar via Gemini API. Se não estiver configurada, usa fallback regex.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")

    if HAS_GEMINI and api_key:
        try:
            return _refine_with_gemini(bill_data, raw_text, api_key)
        except Exception as exc:
            print(f"DEBUG (refinement): Gemini API falhou, usando fallback: {exc}")

    return _refine_fallback(bill_data, raw_text, processed_text)


def _refine_with_gemini(bill_data: dict, raw_text: str, api_key: str) -> dict:
    """Chama o Gemini (google-genai SDK) para corrigir e completar os campos extraídos."""
    client = genai.Client(api_key=api_key)
    prompt = build_prompt(bill_data, raw_text)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    raw_response = response.text
    print(f"DEBUG (refinement): Modelo usado: {GEMINI_MODEL}")
    print(f"DEBUG (refinement): Resposta Gemini (primeiros 500 chars): {raw_response[:500]}")
    return _parse_json_response(raw_response)


def _parse_json_response(raw: str) -> dict:
    """Extrai o JSON da resposta da IA e valida os campos."""
    # Remove blocos de código markdown que o modelo possa retornar
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
    raw = raw.replace("```", "").strip()

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
    Aplica regra de negócio: consumo total = TE + Geração.
    """
    result = DEFAULT_OUTPUT.copy()
    for field in BILL_FIELDS:
        result[field] = _normalize(bill_data.get(field))

    extras = {
        "distribuidora": [
            r"\b(celpe|cemig|copel|enel|light|coelba|energisa|equatorial|elektro|cpfl|rge|cosern|ceal|ceron|amazonas\s*energia)\b",
        ],
        "data_vencimento": [
            r"(?:vence|vencimento|pague\s+at[eé])[:\s]*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})",
            r"([0-9]{2}[\/][0-9]{2}[\/][0-9]{4})",
        ],
        "valor_total": [
            r"(?:total|pagar|fatura)[:\s]*R?\$?\s*([0-9]{1,4}[,\.][0-9]{2})",
        ],
        "consumo_total_kwh": [
            r"([0-9]+(?:[,\.][0-9]+)?)\s*kwh",
        ],
        "geracao_kwh": [
            r"([\d\.,]+)-",
        ],
        "bandeira_tarifaria": [
            r"\b(verde|amarela|vermelha)\b",
        ],
        "mes_referencia": [
            r"((?:janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)[\/\s]*[0-9]{4})",
            # Padrão estrito: MM de 01-12 e ano começando com 20xx
            r"\b((?:0[1-9]|1[0-2])\/20[0-9]{2})\b",
        ],
        # Leituras do medidor: captura números grandes com vírgula decimal
        "leitura_anterior": [
            r"(?:leitura\s+anterior|medida\s+anterior)[:\s]*([\d\.]+[,\.]\d{2})",
            r"(?:leitura\s+anterior|medida\s+anterior)[:\s]*([\d]+)",
        ],
        "leitura_atual": [
            r"(?:leitura\s+atual|medida\s+atual)[:\s]*([\d\.]+[,\.]\d{2})",
            r"(?:leitura\s+atual|medida\s+atual)[:\s]*([\d]+)",
        ],
        "demanda_ativa": [r"Demanda\s+Ativa\(kW\)[\s]*([\d\.,]+)"],
        "demanda_reativa_excedente": [r"Demanda\s+Reativa\s+Excedente\.?\(kVAR\)[\s]*([\d\.,]+)"],
        "consumo_ativo_na_ponta_tusd": [r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-\s*TUSD[\s]*([\d\.,]+)"],
        "consumo_ativo_fora_ponta_tusd": [r"Consumo\s+Ativo\s+Fora\s+de\s+Ponta\(kWh\)-TUSD[\s]*([\d\.,]+)"],
        "consumo_ativo_na_ponta_te": [r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-TE[\s]*([\d\.,]+)"],
        "consumo_ativo_fora_ponta_te": [r"Consumo\s+Ativo\s+Fora\s+Ponta\(kWh\)-TE[\s]*([\d\.,]+)"],
        "consumo_reativo_exc_na_ponta": [r"Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)[\s]*([\d\.,]+)"],
        "consumo_reativo_exc_fora_ponta": [r"Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)[\s]*([\d\.,]+)"],
        # Novos campos administrativos
        "codigo_cliente": [r"(?:c[oó]digo\s+do\s+cliente)[:\s]*(\d+)"],
        "data_leitura_anterior": [r"(?:leitura\s+anterior)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})"],
        "data_leitura_atual": [r"(?:leitura\s+atual)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})"],
        "numero_dias_faturamento": [r"(?:n[º°]?\s+de\s+dias)[:\s]*(\d+)"],
        "demanda_contratada": [r"(?:demanda\s+contratada)[:\s]*([\d\.,]+)"],
        "classificacao_detalhada": [r"(?:classifica[çc][ãa]o)[:\s]*([A-Za-z0-9\-\s]+)(?:\n|\r|$)"],
        # Preços Unitários
        "demanda_ativa_preco_unitario": [r"Demanda\s+Ativa\(kW\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "demanda_reativa_excedente_preco_unitario": [r"Demanda\s+Reativa\s+Excedente\.?\(kVAR\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_na_ponta_tusd_preco_unitario": [r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-\s*TUSD[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_fora_ponta_tusd_preco_unitario": [r"Consumo\s+Ativo\s+Fora\s+de\s+Ponta\(kWh\)-TUSD[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_na_ponta_te_preco_unitario": [r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_fora_ponta_te_preco_unitario": [r"Consumo\s+Ativo\s+Fora\s+Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_reativo_exc_na_ponta_preco_unitario": [r"Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_reativo_exc_fora_ponta_preco_unitario": [r"Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
    }


    for field, patterns in extras.items():
        if result[field] == "None":
            for p in patterns:
                val = _find(p, raw_text) or _find(p, processed_text)
                if val:
                    result[field] = _normalize(val)
                    break

    # --- Regra de negócio: calcular consumo total ---
    if result["consumo_total_kwh"] == "None":
        try:
            def _to_float(val: str) -> float:
                val = val.strip().replace(".", "").replace(",", ".")
                return float(val) if val and val != "None" else 0.0

            ponta = _to_float(result["consumo_ativo_na_ponta_te"])
            fora_ponta = _to_float(result["consumo_ativo_fora_ponta_te"])
            geracao = _to_float(result["geracao_kwh"])
            
            total = ponta + fora_ponta + geracao
            if total > 0:
                result["consumo_total_kwh"] = f"{total:.2f}"
                print(f"DEBUG (refinement): consumo_total_kwh calculado = {total:.2f} "
                      f"(Ponta: {ponta} + Fora: {fora_ponta} + Ger: {geracao})")
        except:
            pass

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
