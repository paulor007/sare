"""
Pacote de extratores de dados.

Cada extrator é responsável por uma fonte de dados:
  - sql_extractor: banco de dados SQLite (via SQLAlchemy)
  - excel_extractor: planilhas Excel (.xlsx)
  - api_extractor: APIs externas (Banco Central)

Todos retornam DataFrames padronizados ou dicts.
"""
from .sql_extractor import extrair_vendas, extrair_vendas_resumo
from .excel_extractor import extrair_metas
from .api_extractor import extrair_cotacao_dolar

__all__ = [
    "extrair_vendas",
    "extrair_vendas_resumo",
    "extrair_metas",
    "extrair_cotacao_dolar",
]