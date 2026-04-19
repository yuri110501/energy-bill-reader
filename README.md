# 🔌 Energy Bill Reader

Leitura automática de **contas de energia elétrica** com OCR + IA.  
Extrai dados estruturados em JSON e os acumula em CSV para análise de dados.

---

## 📁 Estrutura do Projeto

```
energy-bill-reader/
├── app.py               # Servidor Flask (API REST)
├── ocr_utils.py         # OCR com Tesseract
├── text_utils.py        # Extração de campos via regex
├── refinement_utils.py  # Refinamento via Claude API (+ fallback regex)
├── export_utils.py      # Salva JSON individual + acumula CSV
├── storage_utils.py     # Gerencia arquivos locais
├── requirements.txt
├── storage/             # Criado automaticamente ao rodar
│   ├── json/            # Um JSON por conta processada
│   ├── bills_data.csv   # CSV acumulado para análise
│   └── <distribuidora>/ # Imagens organizadas por empresa
└── dataset/bills/       # Coloque aqui suas contas de teste
```

---

## ⚙️ Instalação

### 1. Pré-requisitos

**Tesseract OCR** (obrigatório para leitura das imagens):

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-por

# macOS
brew install tesseract tesseract-lang
```

### 2. Dependências Python

```bash
pip install -r requirements.txt
```

### 3. Dados NLTK (stopwords em português)

```python
python -c "import nltk; nltk.download('stopwords')"
```

---

## 🚀 Executando

```bash
python app.py
```

O servidor sobe em `http://localhost:8080`.

---

## 🔑 Configuração da Claude API (opcional)

Se quiser refinamento com IA (melhora muito a extração de campos ambíguos), exporte sua chave:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Sem a chave, o sistema funciona 100% offline usando apenas regex como fallback.

---

## 📡 Endpoints

### `POST /energy-bill`
Envia uma imagem de conta de energia e recebe os dados extraídos.

```bash
curl -X POST http://localhost:8080/energy-bill \
  -F "file=@minha_conta.jpg"
```

**Resposta:**
```json
{
  "dados_extraidos": {
    "distribuidora": "CELPE",
    "cpf_cnpj_titular": "123.456.789-00",
    "endereco_titular": "Rua das Flores, 123",
    "numero_instalacao": "1234567",
    "numero_fatura": "9876543",
    "mes_referencia": "Janeiro/2024",
    "data_vencimento": "15/02/2024",
    "valor_total": "187.45",
    "consumo_kwh": "342",
    "leitura_atual": "5432",
    "leitura_anterior": "5090",
    "bandeira_tarifaria": "Verde",
    "tipo_fornecimento": "Monofásico",
    "classe_consumidor": "Residencial",
    "tarifa_rs_kwh": "0.85"
  },
  "json_salvo_em": "storage/json/minha_conta_20240115_143022.json"
}
```

### `GET /bills`
Lista todas as contas já processadas (lê o CSV acumulado).

```bash
curl http://localhost:8080/bills
```

---

## 📊 Análise de Dados

Todos os dados ficam acumulados em `storage/bills_data.csv`.  
Abra direto no Excel/Power BI ou use pandas:

```python
import pandas as pd

df = pd.read_csv("storage/bills_data.csv")

# Consumo médio por distribuidora
print(df.groupby("distribuidora")["consumo_kwh"].mean())

# Evolução do valor total ao longo do tempo
df["data_vencimento"] = pd.to_datetime(df["data_vencimento"], dayfirst=True)
df.sort_values("data_vencimento").plot(x="data_vencimento", y="valor_total")
```

---

## 🏗️ Fluxo de Processamento

```
Imagem da conta
      │
      ▼
  OCR (Tesseract)
      │
      ▼
  Extração regex (text_utils.py)
      │
      ▼
  Refinamento IA (Claude API)
  └─ fallback: regex adicional
      │
      ▼
  Validação (CPF/CNPJ)
      │
      ├──► JSON individual  (storage/json/)
      ├──► Linha no CSV     (storage/bills_data.csv)
      └──► Imagem organizada por distribuidora
```

---

## 🗂️ Campos Extraídos

| Campo | Descrição | Exemplo |
|---|---|---|
| `distribuidora` | Nome da distribuidora | CELPE |
| `cpf_cnpj_titular` | CPF ou CNPJ do cliente | 123.456.789-00 |
| `endereco_titular` | Endereço da instalação | Rua das Flores, 123 |
| `numero_instalacao` | Código da UC | 1234567 |
| `numero_fatura` | Número da nota/fatura | 9876543 |
| `mes_referencia` | Mês de competência | Janeiro/2024 |
| `data_vencimento` | Data de vencimento | 15/02/2024 |
| `valor_total` | Valor a pagar (R$) | 187.45 |
| `consumo_kwh` | Consumo do mês (kWh) | 342 |
| `leitura_atual` | Leitura atual do medidor | 5432 |
| `leitura_anterior` | Leitura anterior do medidor | 5090 |
| `bandeira_tarifaria` | Bandeira do mês | Verde |
| `tipo_fornecimento` | Fase elétrica | Monofásico |
| `classe_consumidor` | Classe tarifária | Residencial |
| `tarifa_rs_kwh` | Tarifa (R$/kWh) | 0.85 |
