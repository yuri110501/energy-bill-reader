import os
from dotenv import load_dotenv
load_dotenv()  # Carrega as variáveis do .env

from flask import Flask, request, jsonify, render_template
from storage_utils import save_file, move_file
from ocr_utils import extract_text
from text_utils import preprocess_text, extract_bill_data, validate_cpf_cnpj
from refinement_utils import refine_data_local, replace_null_with_none
from export_utils import save_to_json, append_to_csv

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

    # Extrai texto via OCR local (Tesseract)
    extracted_text = extract_text(saved_path)
    processed_text = preprocess_text(extracted_text)

    # Extrai campos com regex (texto bruto + processado)
    bill_data_raw = extract_bill_data(extracted_text)
    bill_data_processed = extract_bill_data(processed_text)
    bill_data = {
        key: bill_data_raw.get(key) or bill_data_processed.get(key)
        for key in bill_data_raw
    }

    # Refinamento via IA (Claude API) com fallback local por regex
    refined_data = refine_data_local(bill_data, extracted_text, processed_text)

    if not validate_cpf_cnpj(refined_data.get("cpf_cnpj_titular", "")):
        refined_data["cpf_cnpj_titular"] = "CPF/CNPJ inválido/não encontrado"

    final_data = replace_null_with_none(refined_data)

    # Persiste: JSON individual + linha no CSV acumulado
    json_path = save_to_json(final_data, file_name)
    append_to_csv(final_data, file_name)

    # Organiza arquivos por distribuidora
    distribuidora = final_data.get("distribuidora", "outros").lower()
    folder = distribuidora.replace(" ", "_") if distribuidora != "None" else "outros"
    move_file(file_name, f"{folder}/{file_name}")

    return jsonify({
        "dados_extraidos": final_data,
        "json_salvo_em": json_path,
    }), 200


@app.route("/bills", methods=["GET"])
def list_bills():
    """Lista todas as contas já processadas lendo o CSV acumulado."""
    import pandas as pd
    csv_path = os.path.join(STORAGE_DIR, "bills_data.csv")
    if not os.path.exists(csv_path):
        return jsonify({"message": "Nenhuma conta processada ainda.", "data": []}), 200
    df = pd.read_csv(csv_path)
    return jsonify({"total": len(df), "data": df.to_dict(orient="records")}), 200


if __name__ == "__main__":
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(STORAGE_DIR, "json"), exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
