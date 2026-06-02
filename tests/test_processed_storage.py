"""
test_processed_storage.py
-------------------------
Conjunto de testes de unidade para validar a movimentação inteligente,
normalização de dados temporais e prevenção de colisões de arquivos no storage.
Adota o ciclo TDD (fase RED inicial).
"""

import os
import shutil
import tempfile
import json
import pytest
from typing import Generator

# Importações dos módulos sob teste. 
# Inicialmente, essas funções ainda não foram implementadas (RED).
from infrastructure.storage import (
    normalize_mes_referencia,
    resolve_unique_filename,
    move_processed_pdf
)
from infrastructure.repository import BillRepository


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """
    Cria um diretório temporário isolado para os testes de I/O,
    evitando poluir as pastas locais de storage durante a execução da suite.
    """
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


def test_normalize_mes_referencia_valid() -> None:
    """
    Valida a normalização de formatos de datas típicos de faturas.
    O separador '/' deve ser substituído por '-' para evitar que o sistema operacional
    interprete o caractere como delimitador de diretórios.
    """
    assert normalize_mes_referencia("05/2026") == "05-2026"
    assert normalize_mes_referencia("12-2025") == "12-2025"


def test_normalize_mes_referencia_invalid() -> None:
    """
    Garante um fallback seguro para quando a data de referência for corrompida,
    ausente ou não localizada pelo motor de OCR/IA, gerando uma string padronizada.
    """
    assert normalize_mes_referencia(None) == "mes_referencia_não_localizado"
    assert normalize_mes_referencia("") == "mes_referencia_não_localizado"
    assert normalize_mes_referencia("None") == "mes_referencia_não_localizado"
    assert normalize_mes_referencia("invalid_date") == "mes_referencia_não_localizado"


def test_resolve_unique_filename_no_conflict(temp_dir: str) -> None:
    """
    Verifica se o nome original é mantido caso não exista nenhum arquivo homônimo
    no diretório de destino (caminho feliz).
    """
    filename = resolve_unique_filename(temp_dir, "05-2026", ".pdf")
    assert filename == "05-2026.pdf"


def test_resolve_unique_filename_with_conflict(temp_dir: str) -> None:
    """
    Simula cenário de duplicidade (ex: reprocessamento da mesma fatura ou contas distintas
    do mesmo mês). Deve gerar sufixos incrementais numéricos para evitar sobrescrita de dados históricos.
    """
    # Cria arquivos concorrentes vazios
    open(os.path.join(temp_dir, "05-2026.pdf"), "w").close()
    open(os.path.join(temp_dir, "05-2026(1).pdf"), "w").close()

    # O próximo a ser gerado deve conter o sufixo (2)
    filename = resolve_unique_filename(temp_dir, "05-2026", ".pdf")
    assert filename == "05-2026(2).pdf"


def test_move_processed_pdf_with_id(temp_dir: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Valida a movimentação estruturada para faturas identificadas (ID_sof presente).
    Deve criar a estrutura correspondente e mover o arquivo preservando os dados.
    """
    # Mocka a pasta de armazenamento base para apontar para o nosso diretório temporário
    monkeypatch.setenv("LOCAL_STORAGE", temp_dir)
    
    # Recarrega a constante PROCESSED_DIR simulada através do mock da variável de ambiente
    import infrastructure.storage as storage_mod
    processed_base = os.path.join(temp_dir, "processadas")
    monkeypatch.setattr(storage_mod, "PROCESSED_DIR", processed_base)

    # Cria um PDF de origem fictício
    src_file = os.path.join(temp_dir, "conta_teste.pdf")
    with open(src_file, "w") as f:
        f.write("CONTEUDO_PDF_TESTE")

    id_sof = "SOF-0001.0016"
    mes_ref = "05/2026"

    # Executa a movimentação sob teste
    dest_path = move_processed_pdf(src_file, id_sof, mes_ref)

    # Verifica se o arquivo de origem foi removido/movido e o novo destino existe
    assert not os.path.exists(src_file)
    assert os.path.exists(dest_path)
    assert id_sof in dest_path
    assert "05-2026.pdf" in dest_path


def test_move_processed_pdf_without_id(temp_dir: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Testa o tratamento de exceção arquitetural para faturas cujas chaves de identificação
    não foram encontradas. Devem ser movidas para a pasta de auditoria 'Falha_no_ID'.
    """
    monkeypatch.setenv("LOCAL_STORAGE", temp_dir)
    import infrastructure.storage as storage_mod
    processed_base = os.path.join(temp_dir, "processadas")
    monkeypatch.setattr(storage_mod, "PROCESSED_DIR", processed_base)

    src_file = os.path.join(temp_dir, "conta_anonima.pdf")
    with open(src_file, "w") as f:
        f.write("CONTEUDO_PDF_TESTE")

    # ID_sof nulo/vazio
    dest_path = move_processed_pdf(src_file, None, "05/2026")

    assert not os.path.exists(src_file)
    assert os.path.exists(dest_path)
    assert "Falha_no_ID" in dest_path
    assert "05-2026.pdf" in dest_path


def test_repository_saves_processed_pdf_path(temp_dir: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Testa se a integração do repositório persiste corretamente o metadado 'processed_pdf_path'
    no documento JSON sem corromper as colunas nem alterar a tabela CSV consolidada.
    """
    monkeypatch.setenv("LOCAL_STORAGE", temp_dir)
    
    # Atualiza as variáveis globais de diretório do repository baseado na env mockada
    import infrastructure.repository as repo_mod
    monkeypatch.setattr(repo_mod, "STORAGE_DIR", temp_dir)
    monkeypatch.setattr(repo_mod, "JSON_DIR", os.path.join(temp_dir, "json"))
    monkeypatch.setattr(repo_mod, "CSV_PATH", os.path.join(temp_dir, "bills_data.csv"))

    dummy_data = {
        "codigo_cliente": "7047093265",
        "distribuidora": "Celpe",
        "valor_total": "150.00",
        "mes_referencia": "05/2026"
    }
    pdf_path = os.path.join(temp_dir, "processadas", "SOF-0001.0016", "05-2026.pdf")

    # Salva
    json_path = BillRepository.save_all(dummy_data, "fatura.pdf", processed_pdf_path=pdf_path)

    # 1. Verifica se o JSON contém o metadado no nível superior (top-level)
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        parsed_json = json.load(f)
    
    assert parsed_json["processed_pdf_path"] == pdf_path
    assert parsed_json["arquivo_origem"] == "fatura.pdf"
    assert parsed_json["dados"]["codigo_cliente"] == "7047093265"

    # 2. Verifica se o CSV foi criado e NÃO contém o cabeçalho/campo 'processed_pdf_path'
    csv_path = os.path.join(temp_dir, "bills_data.csv")
    assert os.path.exists(csv_path)
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
    
    assert "processed_pdf_path" not in header
    # Assegura que colunas críticas continuam lá
    assert "arquivo_origem" in header
    assert "codigo_cliente" in header
