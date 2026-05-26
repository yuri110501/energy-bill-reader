"""
validate_regex.py
-----------------
Valida os REGEX candidatos contra todos os PDFs disponíveis em Contas/.
Não altera nenhum arquivo de produção.

Uso: python scratch/validate_regex.py
"""

import re
import sys
import os

# Garante que o projeto raiz está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.ocr import extract_structured

# ---------------------------------------------------------------------------
# REGEX candidatos a validar (corrigidos apos inspecao do texto real)
# ---------------------------------------------------------------------------
CANDIDATE_PATTERNS = {
    # demanda_reativa: padroes originais do usuario - funcionam no Grupo A
    "demanda_reativa_excedente": (
        r"Demanda\s+Reativa\s+Exc\w*\.?\s*\(?kVAr\)?\s+([\d.,]+)"
    ),
    "demanda_reativa_excedente_preco_unitario": (
        r"Demanda\s+Reativa\s+Exc\w*\.?\s*\(?kVAr\)?\s+[\d.,]+\s+([\d.,]+)"
    ),
    # consumo reativo: padroes CORRIGIDOS com texto completo real do pdfplumber
    # Texto real: "Consumo Reativo Exc. Na Ponta(kVARh)  1,9500000  0,36731606"
    "consumo_reativo_exc_na_ponta": (
        r"Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)\s+([\d.,]+)"
    ),
    "consumo_reativo_exc_na_ponta_preco_unitario": (
        r"Consumo\s+Reativo\s+Exc\.\s+Na\s+Ponta\(kVARh\)\s+[\d.,]+\s+([\d.,]+)"
    ),
    # "Fora" obrigatorio para evitar match ambiguo com "Na Ponta"
    "consumo_reativo_exc_fora_ponta": (
        r"Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)\s+([\d.,]+)"
    ),
    "consumo_reativo_exc_fora_ponta_preco_unitario": (
        r"Consumo\s+Reativo\s+Exc\.\s+Fora\s+Ponta\(kVARh\)\s+[\d.,]+\s+([\d.,]+)"
    ),
}

CONTAS_DIR = "Contas"
SEPARATOR = "=" * 70


def test_patterns(raw_text: str, filename: str) -> dict[str, str | None]:
    """Aplica todos os candidatos sobre o texto e retorna os resultados."""
    results: dict[str, str | None] = {}
    for field, pattern in CANDIDATE_PATTERNS.items():
        m = re.search(pattern, raw_text, re.IGNORECASE)
        results[field] = m.group(1).strip() if m else None
    return results


def show_context(raw_text: str, pattern: str, window: int = 80) -> str:
    """Retorna trecho do texto em torno do match para diagnostico."""
    m = re.search(pattern, raw_text, re.IGNORECASE)
    if not m:
        return "  -> Nenhum trecho encontrado no texto."
    start = max(0, m.start() - window)
    end   = min(len(raw_text), m.end() + window)
    snippet = raw_text[start:end].replace("\n", "<LF>")
    return f"  -> MATCH: ...{snippet}..."


def main() -> None:
    pdf_files = [
        os.path.join(CONTAS_DIR, f)
        for f in os.listdir(CONTAS_DIR)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print("Nenhum PDF encontrado em Contas/")
        return

    print(SEPARATOR)
    print("VALIDAÇÃO DE REGEX CANDIDATOS")
    print(f"PDFs testados: {len(pdf_files)}")
    print(SEPARATOR)

    # Sumário global: campo → lista de hits
    global_summary: dict[str, list[str]] = {k: [] for k in CANDIDATE_PATTERNS}

    for pdf_path in sorted(pdf_files):
        filename = os.path.basename(pdf_path)
        print(f"\n[PDF] [{filename}]")

        raw_text, _ = extract_structured(pdf_path)
        results = test_patterns(raw_text, filename)

        for field, value in results.items():
            status = "[OK]  " if value else "[FAIL]"
            print(f"  {status} {field:<55} -> {value or 'None'}")
            if value:
                global_summary[field].append(filename)
            else:
                # Mostra contexto para diagnóstico quando falha
                ctx = show_context(raw_text, CANDIDATE_PATTERNS[field])
                print(f"       {ctx}")

    # -----------------------------------------------------------------------
    # Sumário Global
    # -----------------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("SUMARIO GLOBAL (hits por arquivo)")
    print(SEPARATOR)
    total_pdfs = len(pdf_files)
    for field, hits in global_summary.items():
        hit_count = len(hits)
        bar = "#" * hit_count + "." * (total_pdfs - hit_count)
        print(f"  {field:<55} [{bar}] {hit_count}/{total_pdfs}")
        for h in hits:
            print(f"    -> {h}")

    print(f"\n{'=' * 70}")
    print("Validacao concluida. Nenhum arquivo de producao foi alterado.")


if __name__ == "__main__":
    main()
