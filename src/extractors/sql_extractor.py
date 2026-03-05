"""
Extrator de dados do banco SQL.

Por que usar pd.read_sql() e não session.query()?
- pd.read_sql() retorna direto um DataFrame pronto para análise
- Permite escrever queries SQL com JOINs facilmente
- O Pandas já faz parse de datas automaticamente

Retorna DataFrames padronizados para o processador (Fase 04).
"""
import pandas as pd
from src.database import engine

def extrair_vendas(data_inicio: str = None, data_fim: str = None) -> pd.DataFrame:
    """
    Extrai vendas com dados do vendedor e do produto.

    Usa JOIN para trazer tudo numa tabela só:
    - vendas + vendedores (quem vendeu)
    - vendas + produtos (o que vendeu)

    Parâmetros opcionais de período (formato: 'YYYY-MM-DD').
    Se não passar, traz todas.

    Retorna DataFrame com colunas:
        id, data, vendedor, setor, produto, categoria, quantidade,
        valor_total, cliente, cidade, status
    """
    query = """
SELECT
            v.id,
            v.data,
            vd.nome AS vendedor,
            vd.departamento AS setor,
            p.nome AS produto,
            p.categoria,
            v.quantidade,
            v.valor_total,
            v.status
        FROM vendas v
        JOIN vendedores vd ON v.vendedor_id = vd.id
        JOIN produtos p ON v.produto_id = p.id
        WHERE 1=1
    """

    # WHERE 1=1 é um truque para facilitar adicionar filtros:
    # Não precisa verificar se é o primeiro AND ou não.
    if data_inicio:
        query += f" AND v.data >= '{data_inicio}'"
    if data_fim:
        query += f" AND v.data <= '{data_fim}'"

    query += " ORDER BY v.data DESC"

    df = pd.read_sql(query, engine, parse_dates=["data"])
    return df

def extrair_vendas_resumo() -> pd.DataFrame:
    """
    Extrai resumo rápido de vendas (sem JOINs).
    Útil para contagens e totais simples.
    """
    query = "SELECT * FROM vendas ORDER BY data DESC"
    return pd.read_sql(query, engine, parse_dates=["data"])