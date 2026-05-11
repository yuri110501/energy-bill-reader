# 🔌 Energy Bill Reader (Advanced Data Pipeline)

Este projeto é um pipeline de engenharia de dados de alta precisão para a extração, processamento e análise de faturas de energia elétrica. Ele utiliza uma abordagem híbrida de OCR, Processamento de Linguagem Natural (NLP) via Regex e Refinamento de IA (Gemini API) para converter documentos não estruturados em dados relacionais prontos para análise.

---

## 🏗️ Arquitetura do Sistema

O projeto segue princípios de **Clean Architecture**, separando a lógica de negócio das implementações de infraestrutura.

```text
energy-bill-reader/
├── app.py                  # API REST (Flask) para processamento unitário
├── batch_processor.py      # Script de alto desempenho para processamento em lote
├── run_test.py             # Suíte de testes de integração e validação
├── core/                   # Camada de Domínio e Lógica de Negócio
│   ├── extraction.py       # Motores de extração baseados em Regex (NLP)
│   ├── models.py           # Modelos de dados (Pydantic) e Tipagem (PEP 484)
│   └── refinement.py       # Lógica de integração com LLM para limpeza de dados
├── infrastructure/         # Detalhes de Implementação e Ferramentas Externas
│   ├── ocr.py              # Adaptadores de OCR (Tesseract / PDFPlumber)
│   ├── repository.py       # Camada de persistência (CSV/JSON)
│   └── storage.py          # Gestão de sistema de arquivos e organização
├── services/               # Camada de Aplicação e Orquestração
│   └── bill_service.py     # Orquestrador do fluxo OCR -> Extração -> Save
├── utils/                  # Utilitários Transversais
│   └── validators.py       # Validação de integridade (CPF/CNPJ, Datas)
├── storage/                # Data Lake Local (Estrutura de Bronze/Silver)
│   ├── json/               # Raw Data (Arquivos JSON individuais)
│   ├── bills_data.csv      # Consolidado para Analytics (Dataset Final)
│   └── <distribuidora>/    # Documentos organizados por categoria
└── requirements.txt        # Dependências do ecossistema
```

---

## 🚀 Setup do Ambiente

### 1. Requisitos de Sistema
O motor de OCR requer o **Tesseract** instalado no sistema:
- **Windows**: `winget install --id=Unix.TesseractOCR`
- **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-por`

### 2. Ambiente Virtual e Dependências
```bash
# Criação e ativação do venv
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instalação de dependências
pip install -r requirements.txt
```

### 3. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
GOOGLE_API_KEY="SUA_CHAVE_AQUI"
PORT=8080
```

---

## ⚙️ Modos de Operação

### A. API REST (Processamento Unitário)
Ideal para integração com front-ends ou sistemas de upload único.
```bash
python app.py
```
**Endpoint Principal:** `POST /energy-bill`
Recebe um arquivo e retorna o JSON estruturado.

### B. Batch Processor (Engenharia de Dados)
Ideal para processar históricos de contas (dataset de treino ou auditoria).
```bash
python batch_processor.py
```
O script varrerá o diretório configurado, processará todas as imagens e atualizará o `storage/bills_data.csv` de forma atômica.

---

## 📊 Pipeline de Dados (Data Flow)

1. **Ingestão**: Recebimento do PDF/Imagem via API ou Pasta.
2. **OCR Layer**: Conversão de imagem para texto bruto preservando a estrutura espacial.
3. **Extraction Layer**: Aplicação de padrões Regex otimizados para distribuidoras brasileiras (Neonergia, Celpe, etc).
4. **Refinement Layer**: O Gemini AI atua como um "Data Quality Specialist", corrigindo ruídos de leitura e inferindo campos complexos.
5. **Validation Layer**: Verificação de checksums de CPF/CNPJ e tipagem de dados.
6. **Persistência**: Escrita em CSV (Append-only) e organização física do arquivo por distribuidora.

---

## 🛠️ Qualidade de Código e TDD

Este projeto adota o ciclo **Red-Green-Refactor**:
- Use `python run_test.py` para validar o pipeline completo.
- Todos os campos extraídos seguem as tipagens definidas em `core/models.py`.
- O código é documentado focando no "Porquê" da lógica de negócio (especialmente nos padrões de Regex).

---

## 📈 Próximos Passos para o Analista de Dados
O arquivo `storage/bills_data.csv` está pronto para ingestão em ferramentas como:
- **Pandas**: `df = pd.read_csv('storage/bills_data.csv')`
- **Power BI / Tableau**: Conexão direta com o CSV.
- **SQL**: Pode ser facilmente importado para um PostgreSQL/BigQuery via scripts de ingestão.

---

## 🗂️ Campos Extraídos

| Campo | Descrição | Exemplo |
|---|---|---|
| `distribuidora` | Nome da distribuidora (Normalizado) | NEONERGIA |
| `cpf_cnpj_titular` | Identificação do cliente (Validado) | 123.456.789-00 |
| `endereco_titular` | Local de instalação | Rua das Flores, 123 |
| `numero_instalacao` | Código da Unidade Consumidora (UC) | 1234567 |
| `numero_fatura` | Identificador da nota fiscal | 9876543 |
| `mes_referencia` | Competência da fatura | Janeiro/2024 |
| `data_vencimento` | Prazo limite de pagamento | 15/02/2024 |
| `valor_total` | Montante total da fatura (R$) | 187.45 |
| `consumo_total_kwh` | Somatório de consumo (Ponta + Fora) | 342 |
| `geracao_kwh` | Créditos de geração distribuída | 100.00 |
| `leitura_atual` | Registro atual do medidor | 5432 |
| `leitura_anterior` | Registro do mês anterior | 5090 |
| `bandeira_tarifaria` | Status da bandeira (Verde/Amarela/Vermelha) | Verde |
| `tipo_fornecimento` | Configuração de fases (Monofásico/Trifásico) | Monofásico |
| `classe_consumidor` | Classificação tarifária | Residencial |
| `tarifa_rs_kwh` | Custo unitário do kWh (R$) | 0.85 |

---
> **Mentor Note:** Mantenha a estrutura de pastas organizada. A separação entre `infrastructure` e `core` garante que possamos trocar o motor de OCR ou o banco de dados sem quebrar a regra de negócio de como uma conta de luz é lida.
