import os
import json
import glob
from dotenv import load_dotenv

load_dotenv()

from ocr_utils import extract_text
from text_utils import preprocess_text, extract_bill_data, validate_cpf_cnpj
from refinement_utils import refine_data_local, replace_null_with_none

def process_file(file_path):
    """
    Processa um único arquivo através do pipeline completo.
    """
    print(f"DEBUG (batch): Processando {file_path}...")
    try:
        # 1. OCR
        extracted_text = extract_text(file_path)
        if not extracted_text.strip():
            print(f"WARN (batch): Nenhum texto extraído de {file_path}")
            return None
            
        processed_text = preprocess_text(extracted_text)
        
        # 2. Extração via Regex
        bill_data_raw = extract_bill_data(extracted_text)
        bill_data_processed = extract_bill_data(processed_text)
        
        # Combina resultados
        bill_data = {
            key: bill_data_raw.get(key) or bill_data_processed.get(key)
            for key in bill_data_raw
        }

        # 3. Refinamento via IA / Fallback
        refined_data = refine_data_local(bill_data, extracted_text, processed_text)
        
        # 4. Validação
        if not validate_cpf_cnpj(refined_data.get("cpf_cnpj_titular", "")):
            refined_data["cpf_cnpj_titular"] = "CPF/CNPJ inválido/não encontrado"

        result = replace_null_with_none(refined_data)
        result["_file_name"] = os.path.basename(file_path)
        return result
        
    except Exception as e:
        print(f"ERROR (batch): Falha ao processar {file_path}: {e}")
        return None

def run_batch(folder_path, output_file="batch_results.txt"):
    """
    Lê todos os arquivos da pasta e salva os JSONs em um único documento TXT.
    """
    if not os.path.isdir(folder_path):
        print(f"ERROR: O caminho '{folder_path}' não é um diretório válido.")
        return

    # Extensões suportadas
    extensions = ["*.pdf", "*.jpg", "*.jpeg", "*.png"]
    files = []
    for ext in extensions:
        # Busca recursiva simples ou apenas na pasta? Usuário disse "na pasta".
        files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    if not files:
        print(f"WARN: Nenhum arquivo compatível encontrado em {folder_path}")
        return

    print(f"INFO: Iniciando processamento de {len(files)} arquivos...")
    
    results = []
    for f in files:
        res = process_file(f)
        if res:
            results.append(res)

    # Salva todos os resultados em um único arquivo TXT (um JSON por linha)
    try:
        with open(output_file, "w", encoding="utf-8") as out:
            for item in results:
                line = json.dumps(item, ensure_ascii=False)
                out.write(line + "\n")
        
        print(f"\n✅ SUCESSO: {len(results)} arquivos processados com êxito.")
        print(f"📂 Resultados salvos em: {output_file}")
    except Exception as e:
        print(f"ERROR: Falha ao salvar arquivo de saída: {e}")

if __name__ == "__main__":
    import sys
    
    # Adota o padrão TDD de verificação de argumentos
    if len(sys.argv) < 2:
        print("\n🚀 BATCH PROCESSOR - Energy Bill Reader")
        print("-" * 40)
        print("Uso: python batch_processor.py <caminho_da_pasta> [arquivo_saida.txt]")
        print("Exemplo: python batch_processor.py ./Contas resultados.txt\n")
    else:
        folder = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "batch_results.txt"
        run_batch(folder, output)
