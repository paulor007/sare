"""
Extrator de dados do banco SQL.

Por que usar pd.read_sql() e não session.query()?
- pd.read_sql() retorna direto um DataFrame pronto para análise
- Permite escrever queries SQL com JOINs facilmente
- O Pandas já faz parse de datas automaticamente

Retorna DataFrames padronizados para o processador.

Segurança:
- Usa parâmetros SQL (bind params) em vez de f-strings para evitar SQL Injection
- sqlalchemy.text() garante que os parâmetros são escapados corretamente
"""
import pandas as pd
from sqlalchemy import text
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
        valor_total, status
    """
    query_str = """
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

    # Parâmetros SQL (bind params) — protegem contra SQL Injection.
    # Em vez de colocar o valor direto na string (f-string),
    # usei :nome_param e passei o valor separado.
    # O SQLAlchemy escapa automaticamente.
    params = {}

    if data_inicio:
        query_str += " AND v.data >= :data_inicio"
        params["data_inicio"] = data_inicio
    if data_fim:
        query_str += " AND v.data <= :data_fim"
        params["data_fim"] = data_fim

    query_str += " ORDER BY v.data DESC"

    # text() transforma a string em objeto SQL seguro do SQLAlchemy
    df = pd.read_sql(text(query_str), engine, params=params, parse_dates=["data"])
    return df

def extrair_vendas_resumo() -> pd.DataFrame:
    """
    Extrai resumo rápido de vendas (sem JOINs).
    Útil para contagens e totais simples.
    """
    query = text("SELECT * FROM vendas ORDER BY data DESC")
    return pd.read_sql(query, engine, parse_dates=["data"])