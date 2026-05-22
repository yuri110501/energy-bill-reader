"""
rules.py
--------
Centraliza as regras de extração (Regex) por perfil de distribuidora/fatura.
"""

REGEX_RULES = {
    "Neoenergia_A": {
        "metadata": {
            "distribuidora": r"(?i)^(COMPANHIA\s+ENERGÉTICA\s+DE\s+PERNAMBUCO|CELPE|NEOENERGIA)",
            "codigo_cliente": r"(?:C[ÓO]?DIGO\s+DO\s+CLIENTE|CONTA CONTRATO)[\s\S]*?(\d{10})",
            "mes_referencia": r"MÊS/ANO[\s\S]*?(\d{2}/\d{4})",
            "data_vencimento": r"VENCIMENTO[\s\S]*?(\d{2}/\d{2}/\d{4})",
            "classificacao_detalhada": r"CLASSIFICAÇÃO:\s*([^\n]*?)(?=\s{2,}|TIPO DE FORNECIMENTO|$)",
            "tipo_fornecimento": r"TIPO DE FORNECIMENTO:\s*(.*?)(?=\s*TARIFA|$)",
            "bandeira_tarifaria": r"(?i)bandeira[\s\w]+é\s+a\s+(\w+)",
        },
        "financial": {
            "valor_total": r"TOTAL\s+([\d.]+,\d{2})",
        },
        "technical": {
            "geracao_kwh": r"Consumo Ativo Fora de Ponta.*?([\d.]+,\d{2})-",
            "demanda_ativa": r"Demanda Ativa kW\s+([\d.]+,\d{2})",
            "demanda_reativa_excedente": r"Demanda Reativa Exc\.\s+kVAr\s+([\d.]+,\d{2})",
            "consumo_ativo_na_ponta_tusd": r"Consumo-TUSD NPonta kWh\s+([\d.]+,\d{2})",
            "consumo_ativo_fora_ponta_tusd": r"Consumo-TUSD F\.Ponta kWh\s+([\d.]+,\d{2})",
            "consumo_reativo_exc_na_ponta": r"Cons\.Reat\.Exc\.NPonta kVARh\s+([\d.]+,\d{2})",
            "consumo_reativo_exc_fora_ponta": r"Cons\.Reat Exc\.FPonta kVARh\s+([\d.]+,\d{2})",
        },
        "tariffs": {
            "demanda_ativa_preco_unitario": r"Demanda Ativa kW\s+[\d.]+,\d{2}\s+([\d,]+)",
            "demanda_reativa_excedente_preco_unitario": r"Demanda Reativa Exc\.\s+kVAr\s+[\d.]+,\d{2}\s+([\d,]+)",
            "consumo_ativo_na_ponta_tusd_preco_unitario": r"Consumo-TUSD NPonta kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
            "consumo_ativo_na_ponta_te_preco_unitario": r"Consumo-TE Na Ponta kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
            "consumo_ativo_fora_ponta_tusd_preco_unitario": r"Consumo-TUSD F\.Ponta kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
            "consumo_ativo_fora_ponta_te_preco_unitario": r"Consumo-TE F\.Ponta kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
            "consumo_reativo_exc_na_ponta_preco_unitario": r"Cons\.Reat\.Exc\.NPonta kVARh\s+[\d.]+,\d{2}\s+([\d,]+)",
        }
    },
    
    "Neoenergia_B": {
        "metadata": {
            "distribuidora": r"(?i)^(COMPANHIA\s+ENERGÉTICA\s+DE\s+PERNAMBUCO|CELPE|NEOENERGIA|RIO GRANDE DO NORTE|COSERN)",
            "codigo_cliente": r"(?:C[ÓO]?DIGO|INSTALAO)[\s\S]{1,150}?\b(70\d{8})\b|\b(70\d{8})\b[\s\S]{1,150}?(?:C[ÓO]?DIGO|INSTALAO)",
            "mes_referencia": r"(?:REF:MÊS/ANO|MÊS/ANO)[\s\S]{1,50}?(\d{2}/\d{4})",
            "data_vencimento": r"VENCIMENTO[\s\S]{1,100}?(\d{2}/\d{2}/\d{4})",
            "classificacao_detalhada": r"CLASSIFICAÇÃO:\s*([^\n]*?)(?=\s{2,}|TIPO DE FORNECIMENTO|$)",
            "tipo_fornecimento": r"TIPO DE FORNECIMENTO:\s*([\w\s.\-]+)(?=\s*ITENS|$)",
            "bandeira_tarifaria": r"(?i)bandeira[\s\w]+é\s+a\s+(\w+)",
        },
        "financial": {
            "valor_total": r"TOTAL\s+([\d.]+,\d{2})",
        },
        "technical": {
            "geracao_kwh": r"(?:Total de credi\s*tos utilizados na unidade:|CAT de -)\s*(\d+)\s*kWh",
            "consumo_ativo_fora_ponta_tusd": r"Consumo-TUSD\s+kWh\s+([\d.]+,\d{2})",
        },
        "tariffs": {
             "consumo_ativo_fora_ponta_tusd_preco_unitario": r"Consumo-TUSD\s+kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
             "consumo_ativo_fora_ponta_te_preco_unitario": r"Consumo-TE\s+kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
        }
    },

    "Neoenergia_B1": {
        "metadata": {
            "distribuidora": r"(?i)^(COMPANHIA\s+ENERGÉTICA\s+DE\s+PERNAMBUCO|CELPE|NEOENERGIA)",
            "codigo_cliente": r"(?:CÓDIGO\s+DO\s+CLIENTE)\D*(\d{10})|(\d{10})\D*CÓDIGO\s+DO\s+CLIENTE",
            "mes_referencia": r"(?:REF:MÊS/ANO|MÊS/ANO)[\s\S]{1,50}?(\d{2}/\d{4})",
            "data_vencimento": r"VENCIMENTO[\s\S]{1,100}?(\d{2}/\d{2}/\d{4})",
            "classificacao_detalhada": r"CLASSIFICAÇÃO:\s*([^\n]*?)(?=\s{2,}|TIPO DE FORNECIMENTO|$)",
            "tipo_fornecimento": r"TIPO\s+DE\s+FORNECIMENTO:\s*(.*)",
            "bandeira_tarifaria": r"Band\.\s+([A-Z]+)",
        },
        "financial": {
            "valor_total": r"TOTAL\s+([\d.]+,\d{2})",
        },
        "technical": {
            "consumo_ativo_fora_ponta_tusd": r"Consumo-TUSD\s+kWh\s+([\d.]+,\d{2})",
        },
        "tariffs": {
             "consumo_ativo_fora_ponta_tusd_preco_unitario": r"Consumo-TUSD\s+kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
             "consumo_ativo_fora_ponta_te_preco_unitario": r"Consumo-TE\s+kWh\s+[\d.]+,\d{2}\s+([\d,]+)",
        }
    },

    "Equatorial": {
        "METADATA": {
            "codigo_cliente": r"(\d{1,3}\.\d{3}\.\d{3}\.\d{3}-\d{2})",
            "data_vencimento": r"((?:\d{2})/(?:\d{2})/(?:\d{4}))\s+R\$",  # DD/MM/YYYY seguido de R$
            "mes_referencia": r"REFERÊNCIA[\s\S]*?((?:0[1-9]|1[0-2])/\d{4})",
            "tipo_fornecimento": r"TIPO\s+DE\s+FORNECIMENTO:\s+(\w+)",
        },
        "FINANCIAL": {
            "valor_total": r"R\$\s+([\d\.]+,\d{2})",  # R$ seguido do valor            
        },
        "TECHNICAL": {
            "geracao_kwh": r"Consumo Compensado FP\s*\(kWh\)\s+([\d\.]+,\d{2})",
            "demanda_ativa": r"Demanda\s+Contratada\s+Ú?nica\s*\(kW\)\s*:\s*([\d\.]+,\d{2})",
            "consumo_ativo_na_ponta_tusd": r"Consumo Ponta\s*\(kWh\)\s+([\d\.]+,\d{2})",
            "consumo_ativo_fora_ponta_tusd": r"Consumo Fora Ponta\s*\(kWh\)\s+([\d\.]+,\d{2})",
            "consumo_reativo_exc_fora_ponta": r"Consumo Reativo Excedente FP\s*\(kVAr\)\s+([\d\.]+,\d{2})",
        },
        "TARIFFS": {
            "demanda_ativa_preco_unitario": r"Demanda Ativa\s*\(kW\)\s+[\d\.]+,\d{2}\s+([\d,]+)",
            "consumo_ativo_na_ponta_tusd_preco_unitario": r"Consumo Ponta\s*\(kWh\)\s+[\d\.]+,\d{2}\s+([\d,]+)",
            "consumo_ativo_fora_ponta_tusd_preco_unitario": r"Consumo Fora Ponta\s*\(kWh\)\s+[\d\.]+,\d{2}\s+([\d,]+)",
            "consumo_reativo_exc_fora_ponta_preco_unitario": r"Consumo Reativo Excedente FP\s*\(kVAr\)\s+[\d\.]+,\d{2}\s+([\d,]+)",
        }
    },
    "Ambar": {
        "METADATA": {
            "codigo_cliente": r"(\d{7}-\d)",
            "mes_referencia": r"^\s*\d+-\d\s+([0-9]{2}/[0-9]{4})",
            "data_vencimento": r"(?:Vencimento\s+)(\d{2}/\d{2}/\d{4})|(\d{2}/\d{2}/\d{4})\s+R\$",
            "valor_total": r"R\$\s+([\d\.]+,\d{2})",
        },
        "TECHNICAL": {
            "demanda_ativa": r"D\.\s+Ctda\s+Pta:\s+(\d+)",
            "consumo_ativo_na_ponta_tusd": r"Consumo\s+Ponta\s+(\d+(?:\.\d+)*)\s+kWh",
            "consumo_ativo_fora_ponta_tusd": r"Consumo\s+F/Ponta\s+(\d+(?:\.\d+)*)\s+kWh(?:\s+a\s+[\d,]+)?",
            "consumo_reativo_exc_na_ponta": r"En\s+R\s+Exc\s+Ponta\s+(\d+(?:\.\d+)*)\s+kWh",
            "consumo_reativo_exc_fora_ponta": r"En\s+R\s+Exc\s+F/Ponta\s+(\d+(?:\.\d+)*)\s+kWh",
        },
        "TARIFFS": {
            "demanda_ativa_preco_unitario": r"Demanda\s+\d+\s+kW\s+a\s+([\d,]+)",
            "consumo_ativo_na_ponta_tusd_preco_unitario": r"Consumo\s+Ponta\s+[\d\.]+\s+kWh\s+a\s+([\d,]+)",
            "consumo_ativo_fora_ponta_tusd_preco_unitario": r"Consumo\s+F/Ponta\s+[\d\.]+\s+kWh\s+a\s+([\d,]+)",
            "consumo_reativo_exc_na_ponta_preco_unitario": r"En\s+R\s+Exc\s+Ponta\s+[\d\.]+\s+kWh\s+a\s+([\d,]+)",
        }
    },

    "Generico": {
        "metadata": {
            "distribuidora": r"(?i)(COMPANHIA\s+ENERGÉTICA\s+DE\s+PERNAMBUCO|CELPE|NEOENERGIA|CEMIG|ENEL|COPEL|COMPANHIA\s+ENEGERTICA\s+DO\s+RIO\s+GRANDE\s+DO\s+NORTE|EQUATORIAL\s+MARANHÃO\s+DISTRIB.\s+DE\s+ENERGIA\s+S.A.|AMBAR\s+ENERGIA\s+-\s+AM|AMAZONAS\s+ENERGIA)",
            "mes_referencia": r"(?i)(?:Mês/Ano|Referência|Período)[\s\S]*?(\d{2}/\d{4})",
            "data_vencimento": r"(?i)(?:Vencimento|Data Vencto)[\s\S]*?(\d{2}/\d{2}/\d{4})",
            "classificacao_detalhada": r"(?:CLASSIFICAÇÃO:\s*([^\n]*?)|(B3\s+COMERCIAL|A4\s+HORO))(?=\s{2,}|TIPO DE FORNECIMENTO|$)",
        },
        "financial": {
            "valor_total": r"(?i)(?:Total a Pagar|Valor Total|Total da Fatura)\s*R\$\s*([\d.,]+)",
        }
    }
}
