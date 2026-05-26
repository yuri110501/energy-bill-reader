import re
from typing import Dict, Optional

def test_regex_celpe():
    # Caminho do arquivo de inspeção (texto bruto)
    file_path = r'c:\Users\bruno\OneDrive - triOS College\Desktop\Projetos\energy-bill-reader\scratch\scratch\inspecao_BREMEN AUDI CELPE MES 0.txt'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Padrões fornecidos pelo usuário
    patterns = {
        "codigo_cliente": r"(?:CÓDIGO\s+DO\s+CLIENTE)\D*(\d{10})|(\d{10})\D*CÓDIGO\s+DO\s+CLIENTE",
        "bandeira_tarifaria": r"Band\.\s+([A-Z]+)",
        "tipo_fornecimento": r"TIPO\s+DE\s+FORNECIMENTO:\s*(.*)",
        "data_leitura_anterior": r"LEITURA\s+ANTERIOR\s+(\d{2}/\d{2}/\d{4})",
        "data_leitura_atual": r"LEITURA\s+ATUAL\s+(\d{2}/\d{2}/\d{4})",
        "numero_dias_faturamento": r"N°\s+DE\s+DIAS\s+(\d+)",
        "leitura_atual": r"Energia\s+Ativa\s+\w+\s+[\d.]+,\d{2}\s+([\d.]+,\d{2})",
        "leitura_anterior": r"Energia\s+Ativa\s+\w+\s+([\d.]+,\d{2})",
        "consumo_ativo_fora_ponta_tusd": r"Consumo-TUSD\s+kWh\s+([\d.]+,\d{2})",
        "consumo_ativo_fora_ponta_tusd_preco_unitario": r"Consumo-TUSD\s+kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
        "consumo_ativo_fora_ponta_te_preco_unitario": r"Consumo-TE\s+kWh\s+[\d.]+,\d{2}\s+([\d,]+)"
    }

    print(f"{'Campo':<45} | {'Resultado':<20} | {'Status'}")
    print("-" * 80)

    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            # Pega o primeiro grupo não nulo (para o caso do código_cliente com OR)
            value = next((g for g in match.groups() if g is not None), "N/A")
            print(f"{field:<45} | {value:<20} | [OK]")
        else:
            print(f"{field:<45} | {'NÃO ENCONTRADO':<20} | [FALHA]")

if __name__ == "__main__":
    test_regex_celpe()
