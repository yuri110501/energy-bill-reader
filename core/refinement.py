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
    "Sua função é APENAS REFINAR e CORRIGIR os dados já extraídos abaixo.\n"
    "REGRA FUNDAMENTAL: Você só pode preencher um campo se o valor estiver EXPLICITAMENTE no texto da conta.\n"
    "NUNCA invente, estime ou deduza valores que não estejam literalmente no texto.\n"
    "Se um campo não aparecer claramente no texto, mantenha 'None'.\n\n"
    "Retorne APENAS um JSON válido com exatamente estes campos (sem texto fora do JSON):\n\n"
    f"{_json_template_str}\n\n"
    "Regras de formatação:\n"
    "- Valores numéricos: use apenas o número com ponto como separador decimal (ex: '127.45')\n"
    "- cpf_cnpj_titular: busque APENAS na seção 'PAGADOR | CPF/CNPJ' do boleto, NUNCA use o CNPJ da distribuidora\n"
    "- Consumos e Demandas: capture a QUANTIDADE na primeira coluna numérica (ex: 200.00).\n"
    "- Preços Unitários (_preco_unitario): capture o valor da tarifa/preço unitário aplicado.\n"
    "- consumo_total_kwh: CALCULE a soma de 'Consumo Ativo Na Ponta(kWh)-TE' + 'Consumo Ativo Fora Ponta(kWh)-TE' + 'geracao_kwh' (se houver).\n"
    "- geracao_kwh: capture APENAS o valor numérico com sinal '-' indicando crédito de geração solar. Não confunda com CNPJ ou outros números.\n"

    "- valor_total: busque na linha 'MM/AAAA <valor> DD/MM/AAAA' ou 'TOTAL A PAGAR R$ <valor>'\n"
    "- codigo_cliente, demanda_contratada: capture apenas os números\n"
    "- classificacao_detalhada: capture a string completa (ex: 'B3 COMERCIAL')\n"
    "- data_vencimento: DD/MM/AAAA\n"
    "- mes_referencia: MM/AAAA\n"
    "- bandeira_tarifaria: 'Verde', 'Amarela', 'Vermelha Patamar 1' ou 'Vermelha Patamar 2'\n"
    "- distribuidora: nome da empresa distribuidora (ex: 'Celpe', 'Cemig', 'Enel')\n"
    "- Campo não identificado no texto: coloque 'None'\n\n"
    "Dados extraídos inicialmente (refine apenas o que estiver errado ou incompleto):\n"
)


def build_prompt(bill_data: Dict[str, Any], raw_text: str) -> str:
    return (
        PROMPT_TEMPLATE
        + json.dumps(bill_data, indent=2, ensure_ascii=False)
        + "\n\nTexto completo da conta de energia (extraído via OCR):\n"
        + raw_text[:4000]
        + "\n\nRetorne apenas o JSON válido, sem blocos de código markdown."
    )


def refine_data(bill_data: Dict[str, Any], raw_text: str, processed_text: str) -> BillData:
    """
    Coordena o refinamento. Tenta a API primeiro; se falhar ou ausente, usa fallback.
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

    return BillData.from_raw_dict(refined_dict)


def _refine_with_gemini(bill_data: Dict[str, Any], raw_text: str, api_key: str) -> Dict[str, Any]:
    client = genai.Client(api_key=api_key)
    prompt = build_prompt(bill_data, raw_text)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return _parse_json_response(response.text)


def _parse_json_response(raw: str) -> Dict[str, Any]:
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
    raw = raw.replace("```", "").strip()
    match = re.search(r"(\{[\s\S]*\})", raw)
    cleaned = match.group(1) if match else raw.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON inválido retornado pela IA: {exc}\n{cleaned}")


def _refine_fallback(bill_data: Dict[str, Any], raw_text: str, processed_text: str) -> Dict[str, Any]:
    """
    Fallback local: Limpo de regexes genéricos que causam ruído.
    Confia no que foi extraído pelo motor especializado por perfil.
    """
    result = BillData().to_flat_dict()
    for field in result.keys():
        val = bill_data.get(field)
        # Normalização básica de string para o modelo
        result[field] = str(val).strip() if val and val != "None" else "None"

    # Regra de negócio: calcular consumo total (Soma de ponta + fora ponta + geração)
    try:
        def _to_float(val: str) -> float:
            if not val or val == "None": return 0.0
            v = val.strip().replace(".", "").replace(",", ".")
            try: return float(v)
            except: return 0.0

        ponta = _to_float(result.get("consumo_ativo_na_ponta_tusd", "0"))
        fora_ponta = _to_float(result.get("consumo_ativo_fora_ponta_tusd", "0"))
        geracao = _to_float(result.get("geracao_kwh", "0"))
        
        # O consumo total é a soma algébrica (geração costuma ser negativa no texto, tratamos como valor absoluto se necessário)
        total = ponta + fora_ponta + abs(geracao)
        if total > 0:
            result["consumo_total_kwh"] = f"{total:.2f}"
            print(f"DEBUG (refinement): consumo_total_kwh calculado = {total:.2f}")
    except:
        pass

    return result
