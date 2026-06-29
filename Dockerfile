# Usa uma imagem oficial leve do Python
FROM python:3.11-slim

# Evita que o Python grave arquivos .pyc no disco e habilita logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala as dependências do sistema operacional necessárias
# Tesseract OCR, pacote de idioma Português e bibliotecas para processamento de imagens e PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho no container
WORKDIR /app

# Copia e instala primeiro os requirements para otimizar o cache da camada do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia todo o código fonte para o diretório de trabalho
COPY . .

# Comando padrão de inicialização (inicia o watcher para monitoramento)
CMD ["python", "watcher.py"]
