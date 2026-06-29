# 🔌 Energy Bill Reader (Advanced Data Pipeline)

Este projeto é um pipeline de engenharia de dados de alta precisão para a extração, processamento e análise de faturas de energia elétrica. Ele utiliza uma abordagem híbrida de OCR, Processamento de Linguagem Natural (NLP) via **Arquitetura Config-Driven (Regex as Variables)** e Refinamento de IA (Gemini API) como fallback final.

---

## 🏗️ Arquitetura do Sistema

O projeto segue princípios de **Clean Architecture**, separando a lógica de negócio das implementações de infraestrutura e permitindo escalabilidade modular.

```text
energy-bill-reader/
├── app.py                  # API REST (Flask) para processamento unitário
├── batch_processor.py      # Script de alto desempenho para processamento em lote
├── run_test.py             # Suíte de testes de integração e validação
├── core/                   # Camada de Domínio e Lógica de Negócio (CORE)
│   ├── extraction.py       # Motor genérico de extração (Rules-Based Engine)
│   ├── rules.py            # [NOVO] Dicionário mestre de padrões Regex por perfil
│   ├── models.py           # Modelos de dados (Pydantic) e Tipagem (PEP 484)
│   └── refinement.py       # Lógica de integração com LLM para fallback de qualidade
├── infrastructure/         # Detalhes de Implementação e Adaptadores
│   ├── ocr.py              # Adaptadores de OCR (PDFPlumber / Tesseract)
│   ├── repository.py       # Camada de persistência e repositório CSV
│   └── storage.py          # Gestão de sistema de arquivos e organização
├── services/               # Camada de Aplicação e Orquestração
│   └── bill_service.py     # Orquestrador do fluxo: Tabelas -> Regex -> Fallback IA
├── storage/                # Data Lake Local (Estrutura de Bronze/Silver)
│   ├── json/               # Raw Data (Arquivos JSON individuais)
│   └── bills_data.csv      # Consolidado para Analytics (Dataset Final)
└── requirements.txt        # Dependências do ecossistema
```

---

## 🚀 Arquitetura Config-Driven

Diferente de sistemas tradicionais com lógica rígida, este motor utiliza **Perfis de Configuração**. Para adicionar uma nova distribuidora ou layout, basta editar o arquivo `core/rules.py`.

### Hierarquia de Extração:
1.  **Sensor 1 (Tabelas)**: Tenta extrair dados via estrutura nativa do PDF (PDFPlumber).
2.  **Sensor 2 (Motor de Regex)**: Identifica o perfil (Ex: `Celpe_A`) e aplica padrões específicos de NLP.
3.  **Sensor 3 (Fallback Genérico)**: Se campos críticos falharem, aplica padrões universais.
4.  **Sensor 4 (AI Fallback)**: Se o Score de Confiança for inferior a **0.5**, a IA entra em ação para refinar os dados.

---

## 📊 Pipeline de Dados (Data Flow)

1.  **Ingestão**: Recebimento do PDF/Imagem via API ou Processamento em Lote.
2.  **OCR Layer**: Conversão de imagem/PDF para texto bruto preservando a estrutura espacial.
3.  **Classification Layer**: Identificação automática da distribuidora e grupo tarifário (A/B).
4.  **Extraction Engine**: Aplicação iterativa de regras baseadas no perfil detectado.
5.  **Refinement Layer**: O Gemini AI atua como um "Data Quality Specialist" apenas quando a extração determinística falha.
6.  **Persistência**: Escrita atômica em CSV e persistência em JSON para rastreabilidade.

---

## 🛠️ Qualidade de Código e TDD

Este projeto adota o ciclo **Red-Green-Refactor**:
- Use `python run_test.py` para validar o pipeline completo.
- Todos os campos extraídos seguem as tipagens definidas em `core/models.py`.
- O código é documentado focando no **"Porquê"** da lógica (especialmente as nuances matemáticas de Grupo A).

---

## 📈 Campos Extraídos (Destaques Técnicos)

O pipeline captura mais de 30 campos, incluindo métricas críticas de auditoria:

| Categoria | Campos Principais |
|---|---|
| **Metadados** | Distribuidora, Código Cliente, Mês Ref, Vencimento, Valor Total. |
| **Demanda (A)** | Demanda Ativa (kW), Demanda Reativa Excedente (kVAr). |
| **Consumo TUSD** | Consumo Ativo Ponta/Fora Ponta (kWh). |
| **Consumo TE** | Consumo Ativo Ponta/Fora Ponta (kWh) + Preços Unitários. |
| **Reativo** | Consumo Reativo Excedente Ponta/Fora Ponta (kVARh). |
| **Geração** | Energia Injetada no Mês (Geração Distribuída). |

---
> **Mentor Note:** A migração para `rules.py` transforma o código em um produto escalável. Agora, o desenvolvedor não precisa mais mexer na lógica do motor para suportar novas faturas, apenas "ensinar" novos padrões ao dicionário de regras.

---

## 🐳 Setup e Execução via Docker (Recomendado para Novos Computadores)

Para facilitar a execução em computadores que não possuem ambiente de programação configurado (sem necessidade de instalar Python, dependências ou Tesseract OCR), o projeto conta com um ambiente isolado em Docker.

### Passo a Passo

1. **Clonar o Repositório**
   Abra o terminal e clone o projeto:
   ```bash
   git clone https://github.com/yuri110501/energy-bill-reader.git
   cd energy-bill-reader
   ```

2. **Configurar as Variáveis de Ambiente**
   Renomeie o arquivo de exemplo para o formato definitivo:
   - No Windows: `ren .env.example .env` (ou copie manualmente renomeando)
   - No Linux/macOS: `cp .env.example .env`

3. **Construir o Ambiente Docker**
   Certifique-se de que o **Docker Desktop** (ou Docker Engine) esteja em execução. No terminal, rode:
   ```bash
   docker compose build
   ```
   *(Este passo só demora na primeira vez, pois ele compilar o Tesseract OCR e pacotes de idioma em português).*

4. **Escolher o Modo de Execução**
   O docker-compose possui múltiplos serviços configurados:
   
   - **Modo Watcher (Monitoramento Contínuo):**
     Monitora ativamente a pasta `Contas/` no seu computador. Qualquer PDF arrastado para essa pasta será processado em tempo real.
     ```bash
     docker compose up watcher
     ```
   
   - **Modo Batch (Processamento em Lote Imediato):**
     Processa de uma só vez todas as faturas atuais da pasta `Contas/` e encerra.
     ```bash
     docker compose run --rm batch
     ```

Todos os resultados estruturados e CSVs analíticos serão salvos diretamente na pasta local `storage/`, que será criada automaticamente no diretório do projeto.
