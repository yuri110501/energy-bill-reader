import re

text = """
NOSSO NMERO N DO DOCUMENTO CDIGO DO CLIENTE DATA DE VENCIMENTO VALOR DO DOCUMENTO 109907354740 6876477 7047062327 11/08/2025 132,75
7047062327 11/08/2025 132,75 07/2025 CDIGO DO CLIENTE
"""

# Regex sugerido (Otimizado com prefixo 70 e wildcard flexível)
pattern = r"(?:CDIGO\s+DO\s+CLIENTE).*?\b(70\d{8})\b|\b(70\d{8})\b.*?(?:CDIGO\s+DO\s+CLIENTE)"

match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
if match:
    # Pega o grupo 1 ou 2 que tiver valor
    val = match.group(1) or match.group(2)
    print(f"Encontrado: {val}")
else:
    print("Não encontrado.")
