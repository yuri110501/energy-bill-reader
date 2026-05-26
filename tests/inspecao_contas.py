"""
inspecao_contas.py — Inspeciona o texto bruto (pdfplumber) de todos os
PDFs da pasta Contas, exibindo apenas as linhas relevantes para análise
de REGEX: classificação, fornecimento, consumo, demanda, bandeira, etc.
"""
import pdfplumber
import os
import glob

PASTA = os.path.join(os.path.dirname(__file__), "..", "Contas")

KEYWORDS = [
    "classif", "fornecimento", "demanda", "consumo",
    "bandeira", "vencimento", "ref:", "total a pagar",
    "a4", "a3", "b3", "horo", "verde", "amarela",
    "vermelha", "kw", "kwh", "leitura",
]

pdfs = glob.glob(os.path.join(PASTA, "**", "*.pdf"), recursive=True)

for pdf_path in pdfs:
    print("\n" + "=" * 72)
    print(f"ARQUIVO: {os.path.basename(pdf_path)}")
    print("=" * 72)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages[:2]):
                text = page.extract_text(layout=True) or ""
                print(f"\n--- PAGINA {i + 1} ---")
                for linha in text.split("\n"):
                    l_lower = linha.lower()
                    if any(k in l_lower for k in KEYWORDS):
                        s = linha.strip()
                        if s:
                            print(repr(s))
    except Exception as e:
        print(f"ERRO: {e}")
