"""
models.py
---------
Modelos Pydantic para validação de schema dos dados extraídos.
Define a estrutura canônica de uma fatura de energia na ordem desejada pelo usuário.
"""

from typing import Optional
from pydantic import BaseModel, Field


class BillData(BaseModel):
    """
    Modelo canônico de uma conta de energia elétrica brasileira.
    A ordem dos campos aqui define a ordem no JSON final.
    """
    # --- Identificação e Classificação ---
    distribuidora: Optional[str] = Field(None, description="Nome da distribuidora de energia")
    cpf_cnpj_titular: Optional[str] = Field(None, description="CPF ou CNPJ do titular da conta")
    codigo_cliente: Optional[str] = Field(None, description="Código do cliente na distribuidora")
    bandeira_tarifaria: Optional[str] = Field(None, description="Bandeira tarifária vigente")
    tipo_fornecimento: Optional[str] = Field(None, description="Monofásico, Bifásico ou Trifásico")
    classificacao_detalhada: Optional[str] = Field(None, description="Classificação completa")

    # --- Datas e Referência ---
    mes_referencia: Optional[str] = Field(None, description="Mês/ano de referência (MM/AAAA)")
    data_vencimento: Optional[str] = Field(None, description="Data de vencimento (DD/MM/AAAA)")


    # --- Valores Financeiros e Geração ---
    valor_total: Optional[str] = Field(None, description="Valor total a pagar (R$)")
    geracao_kwh: Optional[str] = Field(None, description="Geração injetada (kWh)")


    # --- Demandas (Grupo A) ---
    demanda_ativa: Optional[str] = Field(None, description="Demanda ativa (kW)")
    demanda_ativa_preco_unitario: Optional[str] = None
    demanda_reativa_excedente: Optional[str] = Field(None, description="Demanda reativa excedente (kVAR)")
    demanda_reativa_excedente_preco_unitario: Optional[str] = None

    # --- Consumos Detalhados (Grupo A) ---
    consumo_ativo_na_ponta_tusd: Optional[str] = None
    consumo_ativo_na_ponta_te_preco_unitario: Optional[str] = None
    consumo_ativo_na_ponta_tusd_preco_unitario: Optional[str] = None
    
    consumo_ativo_fora_ponta_tusd: Optional[str] = None
    consumo_ativo_fora_ponta_tusd_preco_unitario: Optional[str] = None
    consumo_ativo_fora_ponta_te_preco_unitario: Optional[str] = None

    consumo_reativo_exc_na_ponta: Optional[str] = None
    consumo_reativo_exc_na_ponta_preco_unitario: Optional[str] = None
    
    consumo_reativo_exc_fora_ponta: Optional[str] = None


    def to_flat_dict(self) -> dict[str, str]:
        """Converte para dict com 'None' string ao invés de None Python."""
        return {k: (v if v is not None else "None") for k, v in self.model_dump().items()}

    @classmethod
    def from_raw_dict(cls, data: dict) -> "BillData":
        """
        Cria a partir de um dict bruto, filtrando apenas os campos existentes no modelo.
        """
        cleaned = {}
        for k in cls.model_fields:
            v = data.get(k)
            cleaned[k] = None if v in (None, "None", "null", "") else str(v)
        return cls(**cleaned)
