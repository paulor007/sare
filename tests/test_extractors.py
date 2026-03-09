"""
Testes dos extratores de dados.

Verifica se cada extrator retorna dados no formato esperado.
Não testa o conteúdo dos dados (muda com o seed),
testa a ESTRUTURA (colunas, tipo, não vazio).
"""

import pandas as pd
from src.extractors import extrair_vendas, extrair_metas, extrair_cotacao_dolar

def test_extrair_vendas_retorna_dataframe():
    """Verifica se extrair_vendas retorna DataFrame não vazio."""
    df = extrair_vendas()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

def test_extrair_vendas_tem_colunas_obrigatorias():
    """Verifica se o DataFrame tem as colunas que o processador espera."""
    df = extrair_vendas()
    colunas_esperadas = ["vendedor", "produto", "categoria", "valor_total", "status"]
    for col in colunas_esperadas:
        assert col in df.columns, f"Coluna '{col}' ausente no DataFrame"

def test_extrair_vendas_status_validos():
    """Verifica se os status são os esperados (sem typos)."""
    df = extrair_vendas()
    status_validos = {"concluida", "pendente", "cancelada"}
    status_encontrados = set(df["status"].unique())
    assert status_encontrados.issubset(status_validos), (
        f"Status inesperados: {status_encontrados - status_validos}"
    )

def test_extrair_metas_retorna_dataframe():
    """Verifica se metas são lidas do Excel."""
    df = extrair_metas()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Vendedor" in df.columns
    assert "Meta Trimestre (R$)" in df.columns

def test_extrair_cotacao_dolar_retorna_dict():
    """Verifica se cotação retorna dict com data e valor."""
    dolar = extrair_cotacao_dolar()
    assert isinstance(dolar, dict)
    assert "data" in dolar
    assert "valor" in dolar
    assert isinstance(dolar["valor"], (int, float))
    assert dolar["valor"] > 0  # Deve ter valor (real ou fallback)