"""
Extrator de dados de planilhas Excel.

Por que um módulo só para ler Excel?
- Centraliza o caminho do arquivo (não fica espalhado pelo código)
- Trata erros (arquivo não existe, formato errado)
- Normaliza colunas (remove espaços extras)
- Facilita trocar o arquivo sem mexer em outros módulos

Usa openpyxl como engine (é o padrão para .xlsx no Pandas).
"""

import pandas as pd
from pathlib import Path

from src.config import DATA_DIR

def extrair_metas(caminho: str = None) -> pd.DataFrame:
    """
    Extrai metas por vendedor da planilha Excel.

    Se não passar caminho, usa o arquivo padrão (data/metas_vendas.xlsx).

    Retorna DataFrame com colunas:
        Vendedor, Setor, Meta Mensal (R$), Meta Trimestral (R$)

    Raises:
        FileNotFoundError: se a planilha não existe
    """
    if caminho is None:
        caminho = DATA_DIR / "metas_vendas.xlsx"

    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Planilha não encontrada: {caminho}\n"
            f"Rode: python data/seed_meta.py"
        )
    
    # engine="openpyxl" é obrigatório para arquivos .xlsx
    # O Pandas precisa de uma engine para ler Excel (não lê sozinho)
    df = pd.read_excel(str(caminho), engine="openpyxl")

    # Normaliza nomes de colunas (remove espaços antes e depois)
    # "  Meta Mensal (R$) " → "Meta Mensal (R$)"
    df.columns = df.columns.str.strip()

    return df