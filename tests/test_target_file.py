
import os
import json
from services.bill_service import BillService

def test_specific_file():
    file_path = r"Contas\TOYOLEX IMBIR MES 12 CELPE.pdf"
    print(f"--- Testando extração: {file_path} ---")
    
    try:
        final_data, json_path = BillService.process_file(file_path)
        print("\n[RESULTADO DA EXTRAÇÃO]")
        print(json.dumps(final_data, indent=2, ensure_ascii=False))
        
        # Validação dos campos solicitados pelo usuário
        targets = {
            "consumo_ativo_na_ponta_tusd_preco_unitario": "1.83953972",
            "consumo_ativo_fora_ponta_tusd_preco_unitario": "0.11432740",
            "consumo_reativo_exc_fora_ponta_preco_unitario": "0.43418402"
        }
        
        print("\n[VERIFICAÇÃO DE ALVOS]")
        for k, expected in targets.items():
            actual = final_data.get(k)
            status = "✅ OK" if str(actual) == expected else f"❌ FALHA (Esperado: {expected})"
            print(f"{k}: {actual} -> {status}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_specific_file()
