# Energy Bill Reader

Este repositório automatiza o processamento de faturas de energia em PDF ou imagem, extraindo dados estruturados para posterior análise. O fluxo atual combina OCR, extração baseada em regras e regex, refinamento opcional por IA e persistência local em JSON e CSV.

## O que o projeto faz

- Lê arquivos de conta de energia em formato PDF ou imagem.
- Usa pdfplumber para PDFs digitais e Tesseract para PDFs escaneados ou imagens.
- Extrai campos estruturados com regras e regex, com pontuação de confiança.
- Pode usar a API do Google Gemini para refinar dados quando a extração local não é suficiente.
- Persiste os resultados em arquivos JSON individuais e em um CSV consolidado.
- Possui um watcher para processar novos arquivos automaticamente em uma pasta monitorada e um modo batch para processamento sob demanda.

## Fluxo de processamento

1. Ingestão do arquivo em uma pasta de entrada.
2. Extração de texto e, quando possível, tabelas estruturadas.
3. Identificação de campos via regras e regex.
4. Refinamento opcional por IA se a confiança estiver abaixo do limite configurado.
5. Persistência em armazenamento local.

## Estrutura do repositório

```text
energy-bill-reader/
├── batch_processor.py      # Processamento em lote de arquivos
├── watcher.py              # Monitoramento contínuo de uma pasta
├── run_test.py             # Script de validação manual do pipeline
├── core/                   # Regras de extração, modelos e refinamento
├── infrastructure/         # OCR, repositório e armazenamento local
├── services/               # Orquestração do processamento principal
├── data/                   # Mapeamentos e dados auxiliares
├── storage/                # JSONs processados e CSV consolidado
├── tests/                  # Testes e scripts de inspeção
├── docker-compose.yml      # Serviços Docker para watcher, batch e testes
├── Dockerfile              # Imagem do ambiente de execução
├── requirements.txt        # Dependências Python
└── .env.example            # Variáveis de ambiente de exemplo
```

## Requisitos

- Python 3.11+
- Tesseract OCR instalado no sistema
- Dependências listadas em requirements.txt

No Windows, o executável do Tesseract pode precisar ser apontado via variável de ambiente ou configuração em core/config.py.

## Configuração

1. Crie o arquivo .env a partir do exemplo:

```bash
copy .env.example .env
```

2. Ajuste as variáveis conforme necessário:

- LOCAL_STORAGE: pasta para persistência local
- WATCH_DIR: pasta monitorada pelo watcher
- GOOGLE_API_KEY: chave da API do Google Gemini (opcional)
- GEMINI_MODEL: modelo Gemini a ser usado
- AI_CONFIDENCE_THRESHOLD: limite para disparar refinamento por IA
- TESSERACT_CMD: caminho do executável do Tesseract (Windows)

## Instalação local

```bash
pip install -r requirements.txt
```

Se necessário, instale o Tesseract no sistema:

- Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-por
- macOS: brew install tesseract tesseract-lang
- Windows: instalar o pacote oficial do Tesseract e apontar o caminho em TESSERACT_CMD

## Execução local

### Modo watcher

Monitora a pasta de entrada e processa novos arquivos automaticamente:

```bash
python watcher.py
```

### Modo batch

Processa todos os arquivos compatíveis em uma pasta e gera um arquivo de resultados:

```bash
python batch_processor.py ./Contas ./storage/batch_results.txt
```

### Validação manual

```bash
python run_test.py
```

### Testes

```bash
pytest
```

## Execução com Docker

O projeto já inclui um ambiente Docker para facilitar o uso em diferentes máquinas.

### Build da imagem

```bash
docker compose build
```

### Watcher

```bash
docker compose up watcher
```

### Processamento em lote

```bash
docker compose run --rm batch
```

### Testes

```bash
docker compose run --rm tests
```

## Saídas geradas

Os resultados são salvos em:

- storage/json/: um JSON por arquivo processado
- storage/bills_data.csv: consolidação dos dados extraídos
- storage/processadas/: PDFs arquivados após o processamento
- storage/batch_results.txt: resumo do processamento em lote

## Observações importantes

- Se GOOGLE_API_KEY não estiver configurada, o pipeline funciona apenas com a extração local.
- O watcher é pensado para uso contínuo em uma pasta de entrada, enquanto o batch é mais indicado para processamentos pontuais.
- O projeto está estruturado para evoluir com novas regras de extração sem alterar a lógica principal do motor.
