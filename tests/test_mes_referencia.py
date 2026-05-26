"""
test_mes_referencia.py
-----------------------
Valida o REGEX de mes_referencia para o perfil Neoenergia_A4_2022
contra MÚLTIPLOS arquivos de inspeção pré-existentes, sem alterar
os demais perfis. Segue o padrão do test_new_patterns.py.
"""
import re
import os
import glob

# ---------------------------------------------------------------------------
# Padrões candidatos a testar — somente para Neoenergia_A4_2022
# ---------------------------------------------------------------------------
CANDIDATES = {
    "ATUAL  (MÊS REFERÊNCIA\\D*)":
        r"MÊS\s+REFERÊNCIA\D*(\d{2}/\d{4})",

    "CANDIDATO G (Combinação restrita)":
        r"MÊS\s+REFERÊNCIA[^\d\n]*(\d{2}/\d{4})|(\d{2}/\d{4})[^\n]*\n[^\n]*MÊS\s+REFERÊNCIA",

    "CANDIDATO H (Combinação lookahead)":
        r"(?:(\d{2}/\d{4})\s+(?:\d{2}/\d{2}/\d{4})?\s*\n\s*MÊS\s+REFERÊNCIA|MÊS\s+REFERÊNCIA[^\d\n]*(\d{2}/\d{4}))",
}

# Outros perfis — devemos garantir que seus padrões ATUAIS continuam OK
OUTROS_PERFIS = {
    "Neoenergia_A4   (MÊS/ANO)":
        r"MÊS/ANO[\s\S]*?(\d{2}/\d{4})",
    "Neoenergia_B3   (REF:MÊS/ANO|MÊS/ANO)":
        r"(?:REF:MÊS/ANO|MÊS/ANO)[\s\S]{1,50}?(\d{2}/\d{4})",
    "Neoenergia_B1   (REF:MÊS/ANO|MÊS/ANO)":
        r"(?:REF:MÊS/ANO|MÊS/ANO)[\s\S]{1,50}?(\d{2}/\d{4})",
    "Generico        (Mês/Ano|Referência|Período)":
        r"(?i)(?:Mês/Ano|Referência|Período)[\s\S]*?(\d{2}/\d{4})",
}

SCRATCH_DIR = os.path.join(
    r"c:\Users\bruno\OneDrive - triOS College\Desktop\Projetos\energy-bill-reader",
    "scratch", "scratch"
)

def first_group(match) -> str:
    """Extrai o primeiro grupo não-None de um match."""
    if not match:
        return None
    return next((g for g in match.groups() if g is not None), match.group(0))

def run_tests():
    txt_files = sorted(glob.glob(os.path.join(SCRATCH_DIR, "inspecao_*.txt")))
    if not txt_files:
        print(f"ERRO: Nenhum arquivo de inspeção encontrado em {SCRATCH_DIR}")
        return

    print("\n" + "=" * 90)
    print("  VALIDAÇÃO: mes_referencia — Candidatos para Neoenergia_A4_2022")
    print("=" * 90)

    for path in txt_files:
        fname = os.path.basename(path)
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        print(f"\n- {fname}")
        print(f"  {'Padrão':<50} | {'Resultado':<12} | {'Status'}")
        print(f"  {'-'*50}-+-{'-'*12}-+-{'-'*6}")

        for label, pattern in CANDIDATES.items():
            m = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            value = first_group(m) if m else None
            status = "[OK]   " if value else "[FALHA]"
            resultado = value if value else "—"
            print(f"  {label:<50} | {resultado:<12} | {status}")

    print("\n" + "=" * 90)
    print("  REGRESSÃO: Padrões dos outros perfis (não devem ser tocados)")
    print("=" * 90)

    for path in txt_files:
        fname = os.path.basename(path)
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        print(f"\n- {fname}")
        print(f"  {'Perfil':<48} | {'Resultado':<12} | {'Status'}")
        print(f"  {'-'*48}-+-{'-'*12}-+-{'-'*6}")

        for label, pattern in OUTROS_PERFIS.items():
            m = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            value = first_group(m) if m else None
            status = "[OK]   " if value else "[N/A]  "
            resultado = value if value else "—"
            print(f"  {label:<48} | {resultado:<12} | {status}")

if __name__ == "__main__":
    run_tests()
