import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.rules import REGEX_RULES

def test_pattern(file_path):
    print(f"\n============================================================")
    print(f"VALIDAÇÃO OTIMIZADA - NEOENERGIA_A4_2022")
    print(f"Arquivo: {os.path.basename(file_path)}")
    print(f"============================================================")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"Erro ao ler arquivo {file_path}: {e}")
        return False

    rules = REGEX_RULES["Neoenergia_A4_2022"]
    extracted = {}

    print(f"{'Campo':<45} | {'Resultado':<20} | {'Status'}")
    print("-" * 80)

    for category, fields in rules.items():
        for field, pattern in fields.items():
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                val = None
                for i in range(1, len(match.groups()) + 1):
                    if match.group(i):
                        val = match.group(i).strip()
                        break
                if not val:
                    val = match.group(0).strip()
                extracted[field] = val
                print(f"{field:<45} | {val[:20]:<20} | [OK]")
            else:
                print(f"{field:<45} | {'-':<20} | [FALHA]")

    if not extracted.get("mes_referencia"):
        print("\n[ERRO CRÍTICO] mes_referencia não extraído!")
        return False
    return True

if __name__ == "__main__":
    files = [
        r"c:\Users\bruno\OneDrive - triOS College\Desktop\Projetos\energy-bill-reader\scratch\scratch\inspecao_TOYOLEX IMBIRIBEIRA MES 7.txt",
        r"c:\Users\bruno\OneDrive - triOS College\Desktop\Projetos\energy-bill-reader\scratch\scratch\inspecao_TOYOLEX IMB MES 05.txt",
        r"c:\Users\bruno\OneDrive - triOS College\Desktop\Projetos\energy-bill-reader\scratch\scratch\inspecao_TOYOLEX IMB MÊS 02.txt"
    ]
    
    all_passed = True
    for file in files:
        if os.path.exists(file):
            if not test_pattern(file):
                all_passed = False
        else:
            print(f"Arquivo não encontrado: {file}")
            
    if all_passed:
        print("\n\n[SUCESSO] TODOS OS TESTES PASSARAM COM SUCESSO!")
        sys.exit(0)
    else:
        print("\n\n❌ HOUVE FALHAS NA EXTRAÇÃO.")
        sys.exit(1)
