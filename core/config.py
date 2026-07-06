"""
config.py
---------
Ponto único de configuração do sistema. Centraliza todas as variáveis de ambiente
para facilitar auditoria, testes e manutenção, eliminando leituras dispersas de
os.environ nos demais módulos.
"""

import os

# --- Armazenamento Local ---
# Diretório raiz de persistência (JSON, CSV, PDFs processados)
LOCAL_STORAGE: str = os.environ.get("LOCAL_STORAGE", "storage")

# Diretório monitorado pelo Watcher em busca de novas faturas
WATCH_DIR: str = os.environ.get("WATCH_DIR", "Contas")

# --- IA / Refinamento ---
# Chave da API Gemini (obrigatória para acionamento da IA)
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")

# Modelo Gemini configurável (padrão: gemini-2.5-flash)
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Score de confiança abaixo do qual a IA é acionada como fallback
AI_CONFIDENCE_THRESHOLD: float = float(
    os.environ.get("AI_CONFIDENCE_THRESHOLD", "0.5")
)

# --- OCR (Tesseract) ---
# Caminho do executável do Tesseract. No Windows, definível via .env.
# Em Linux/Docker, o Tesseract é resolvido automaticamente pelo PATH do sistema.
TESSERACT_CMD: str = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)
