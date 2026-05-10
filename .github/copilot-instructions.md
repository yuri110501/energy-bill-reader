## Energy Bill Reader — Instruções rápidas para agentes AI

Resumo (1 linha): imagem → OCR (Tesseract) → extração por regex → refinamento opcional via Claude → salvar JSON + linha CSV.

Arquivos chave (abra antes de editar)
- `app.py` — endpoints principais: `POST /energy-bill` (upload) e `GET /bills` (histórico). Ponto de integração para mudanças.
- `ocr_utils.py` — pré-processamento de imagem e suporte a PDF (PyMuPDF). Veja `_preprocess_image()` e `extract_text()`.
- `text_utils.py` — todas as regex de extração (função `extract_bill_data`). Alterações aqui mudam o comportamento offline.
- `refinement_utils.py` — prompt (`PROMPT_TEMPLATE`), parsing de resposta IA e fallback local. Mantenha saída JSON com os campos em `BILL_FIELDS`.
- `export_utils.py` — `CSV_COLUMNS`, `save_to_json`, `append_to_csv` (formato persistente usado por UI/backend).
- `storage_utils.py` — `save_file` / `move_file` e uso de `LOCAL_STORAGE`.

Regras e convenções específicas deste projeto
- Sempre preserve a forma e os nomes dos campos: use os mesmos nomes de `BILL_FIELDS`/`CSV_COLUMNS` (ex.: `valor_total`, `consumo_kwh`, `distribuidora`).
- Quando modificar extrações: atualizar tanto `text_utils.extract_bill_data` quanto os padrões extras em `refinement_utils._refine_fallback` para consistência.
- O refinamento por IA (Anthropic/Claude) só é usado se `ANTHROPIC_API_KEY` estiver presente e a lib `anthropic` importável; caso contrário o projeto usa fallback 100% local.
- A resposta esperada da IA deve ser estritamente JSON conforme o `PROMPT_TEMPLATE`; o código usa regex para extrair o primeiro JSON da resposta.

Ambiente e comandos essenciais
- Instalar dependências Python: `pip install -r requirements.txt`.
- Tesseract: necessário externamente (Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-por`; macOS: `brew install tesseract tesseract-lang`).
- NLTK stopwords: `python -c "import nltk; nltk.download('stopwords')"` (o projeto pode usar `NLTK_DATA`).
- Rodar local (dev): `python app.py` → servidor em `http://localhost:8080` (usa `PORT` env se definido).

Pontos importantes para revisão automática por agentes
- Não alterar o `PROMPT_TEMPLATE` sem atualizar o parse em `_parse_json_response` — mudanças podem quebrar o parse JSON.
- Testar mudanças de regex com imagens reais (colocar em `dataset/bills/`) e validar JSON + `storage/bills_data.csv`.
- PDF handling: `ocr_utils.extract_text` usa PyMuPDF; ao adicionar suporte multi-page, atualize docstring e testes manuais.

Integrações externas
- Tesseract (local binary) — caminho padrão Windows configurado em `ocr_utils.py`.
- Anthropic/Claude via `anthropic` (opcional) — ver `refinement_utils._refine_with_claude`.

Quando abrir um PR
- Inclua: imagem de teste (ou referência), JSON de saída esperado, diff do `storage/bills_data.csv` (linha adicionada) e descrição curta de como a mudança melhora extração/cobertura.

Perguntas ao mantenedor (se necessário)
- Tem imagens de teste padronizadas que podemos adicionar (em `dataset/bills/`)?
- Preferem formato de data/valor com vírgula ou ponto no CSV? (atualmente ambos aparecem; normalizar ajuda análises).

FIM — peça feedback se quiser que eu adapte o conteúdo para um estilo mais curto/mais detalhado.
