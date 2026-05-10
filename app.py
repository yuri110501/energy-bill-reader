import os
from dotenv import load_dotenv
load_dotenv()  # Carrega as variáveis do .env

from flask import Flask, request, jsonify, render_template

from infrastructure.storage import save_file, move_file
from services.bill_service import BillService
from utils.validators import validate_cpf_cnpj, sanitize_folder_name

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload

STORAGE_DIR = os.environ.get("LOCAL_STORAGE", "storage")


@app.route("/")
def index():
    """Serve a interface web principal."""
    return render_template("index.html")


@app.route("/energy-bill", methods=["POST"])
def energy_bill():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Arquivo sem nome"}), 400

    file_name = file.filename
    content = file.read()
    saved_path = save_file(file_name, content)

    try:
        # A Camada de Serviço orquestra tudo (OCR -> Regex -> Gemini -> DB/JSON)
        final_data, json_path = BillService.process_file(saved_path)

        if not validate_cpf_cnpj(final_data.get("cpf_cnpj_titular", "")):
            final_data["cpf_cnpj_titular"] = "CPF/CNPJ inválido/não encontrado"

        # Organiza arquivos por distribuidora (move da raiz do storage para subpasta)
        distribuidora = final_data.get("distribuidora", "outros")
        folder = sanitize_folder_name(distribuidora)
        move_file(file_name, f"{folder}/{file_name}")

        return jsonify({
            "dados_extraidos": final_data,
            "json_salvo_em": json_path,
        }), 200

    except Exception as e:
        print(f"ERROR (app): {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/bills", methods=["GET"])
def list_bills():
    """Lista todas as contas já processadas."""
    try:
        bills = BillService.get_all_bills()
        if not bills:
            return jsonify({"message": "Nenhuma conta processada ainda.", "data": []}), 200
        return jsonify({"total": len(bills), "data": bills}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/batch-process", methods=["POST"])
def batch_process():
    """
    Processa todos os arquivos de uma pasta informada via JSON.
    Ex: { "folder_path": "C:/contas", "output_file": "meu_batch.txt" }
    """
    data = request.get_json()
    if not data or "folder_path" not in data:
        return jsonify({"error": "Caminho da pasta (folder_path) não informado"}), 400
    
    folder_path = data["folder_path"]
    output_file = data.get("output_file", os.path.join(STORAGE_DIR, "batch_results.txt"))
    
    if not os.path.isdir(folder_path):
        return jsonify({"error": f"Caminho '{folder_path}' não é um diretório válido"}), 400
    
    from batch_processor import run_batch
    
    # Executa o processamento em lote
    run_batch(folder_path, output_file)
    
    return jsonify({
        "message": "Processamento em lote concluído com sucesso",
        "folder_path": folder_path,
        "output_file": output_file
    }), 200


if __name__ == "__main__":
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(STORAGE_DIR, "json"), exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
