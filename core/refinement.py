"""
refinement.py
-------------
Refina os dados extraídos por regex usando IA (Gemini) e regras de negócio locais.
Utiliza os modelos Pydantic da camada core para garantir a estrutura correta.
"""

import os
import json
import re
from typing import Dict, Any

from core.models import BillData

# Modelo configurável via variável de ambiente (padrão: gemini-2.5-flash)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Usa o dicionário flat gerado pelo Pydantic para criar o template de prompt
_dummy_bill = BillData().to_flat_dict()
_json_template_str = json.dumps(_dummy_bill, indent=2)

PROMPT_TEMPLATE = (
    "Você é um especialista em leitura de contas de energia elétrica brasileiras.\n"
    "Analise os dados extraídos abaixo e o texto original da conta.\n"
    "Retorne APENAS um JSON válido com exatamente estes campos (sem texto fora do JSON):\n\n"
    f"{_json_template_str}\n\n"
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


def build_prompt(bill_data: Dict[str, Any], raw_text: str) -> str:
    return (
        PROMPT_TEMPLATE
        + json.dumps(bill_data, indent=2, ensure_ascii=False)
        + "\n\nTexto completo da conta de energia (extraído via OCR):\n"
        + raw_text[:4000]  # Limita para não extrapolar o contexto
        + "\n\nRetorne apenas o JSON válido, sem blocos de código markdown."
    )


def refine_data(bill_data: Dict[str, Any], raw_text: str, processed_text: str) -> BillData:
    """
    Coordena o refinamento. Tenta a API primeiro; se falhar ou ausente, usa fallback.
    Retorna a instância validada do modelo BillData.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")

    refined_dict = None
    if HAS_GEMINI and api_key:
        try:
            refined_dict = _refine_with_gemini(bill_data, raw_text, api_key)
        except Exception as exc:
            print(f"DEBUG (refinement): Gemini API falhou, usando fallback: {exc}")

    if not refined_dict:
        refined_dict = _refine_fallback(bill_data, raw_text, processed_text)

    # Converte o dicionário final para o modelo Pydantic para garantir consistência
    return BillData.from_raw_dict(refined_dict)


def _refine_with_gemini(bill_data: Dict[str, Any], raw_text: str, api_key: str) -> Dict[str, Any]:
    """Chama o Gemini para corrigir e completar os campos extraídos."""
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


def _parse_json_response(raw: str) -> Dict[str, Any]:
    """Extrai o JSON da resposta da IA."""
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
    raw = raw.replace("```", "").strip()

    match = re.search(r"(\{[\s\S]*\})", raw)
    cleaned = match.group(1) if match else raw.strip()

    try:
        data = json.loads(cleaned)
        return data
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON inválido retornado pela IA: {exc}\n{cleaned}")


def _refine_fallback(bill_data: Dict[str, Any], raw_text: str, processed_text: str) -> Dict[str, Any]:
    """
    Fallback local: combina os dados do regex com padrões alternativos.
    """
    result = BillData().to_flat_dict()
    for field in result.keys():
        val = bill_data.get(field)
        result[field] = str(val).strip() if val else "None"

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
            r"\b((?:0[1-9]|1[0-2])\/20[0-9]{2})\b",
        ],
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
        "codigo_cliente": [r"(?:c[oó]digo\s+do\s+cliente)[:\s]*(\d+)"],
        "data_leitura_anterior": [r"(?:leitura\s+anterior)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})"],
        "data_leitura_atual": [r"(?:leitura\s+atual)[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})"],
        "numero_dias_faturamento": [r"(?:n[º°]?\s+de\s+dias)[:\s]*(\d+)"],
        "demanda_contratada": [r"(?:demanda\s+contratada)[:\s]*([\d\.,]+)"],
        "classificacao_detalhada": [r"(?:classifica[çc][ãa]o)[:\s]*([A-Za-z0-9\-\s]+)(?:\n|\r|$)"],
        "demanda_ativa_preco_unitario": [r"Demanda\s+Ativa\(kW\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "demanda_reativa_excedente_preco_unitario": [r"Demanda\s+Reativa\s+Excedente\.?\(kVAR\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_na_ponta_tusd_preco_unitario": [r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-\s*TUSD[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_fora_ponta_tusd_preco_unitario": [r"Consumo\s+Ativo\s+Fora\s+de\s+Ponta\(kWh\)-TUSD[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_na_ponta_te_preco_unitario": [r"Consumo\s+Ativo\s+Na\s+Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_ativo_fora_ponta_te_preco_unitario": [r"Consumo\s+Ativo\s+Fora\s+Ponta\(kWh\)-TE[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_reativo_exc_na_ponta_preco_unitario": [r"Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
        "consumo_reativo_exc_fora_ponta_preco_unitario": [r"Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)[^\d]*(?:[\d\.,]+)[\s]+([\d\.,]+)"],
    }

    def _find_fallback(pattern: str, text: str):
        if not text: return None
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip() if match.lastindex else match.group(0).strip()
        return None

    for field, patterns in extras.items():
        if result.get(field, "None") == "None":
            for p in patterns:
                val = _find_fallback(p, raw_text) or _find_fallback(p, processed_text)
                if val:
                    result[field] = val
                    break

    # Regra de negócio: calcular consumo total
    if result.get("consumo_total_kwh", "None") == "None":
        try:
            def _to_float(val: str) -> float:
                if not val or val == "None": return 0.0
                val = val.strip().replace(".", "").replace(",", ".")
                return float(val)

            ponta = _to_float(result.get("consumo_ativo_na_ponta_te", "0"))
            fora_ponta = _to_float(result.get("consumo_ativo_fora_ponta_te", "0"))
            geracao = _to_float(result.get("geracao_kwh", "0"))
            
            total = ponta + fora_ponta + geracao
            if total > 0:
                result["consumo_total_kwh"] = f"{total:.2f}"
                print(f"DEBUG (refinement): consumo_total_kwh calculado = {total:.2f}")
        except:
            pass

    return result
