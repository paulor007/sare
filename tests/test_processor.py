"""
Testes do processador de dados.

Testa as funções de análise que calculam métricas e agrupamentos.
Usa dados reais do banco (gerados pelo seed).
"""

import pandas as pd
from src.extractors import extrair_vendas, extrair_metas
from src.processor import (
    resumo_vendas,
    vendas_por_categoria,
    vendas_por_vendedor,
    vendas_por_mes,
    comparar_metas,
)

def test_resumo_vendas_retorna_metricas():
    """Verifica se resumo tem todas as métricas esperadas."""
    vendas = extrair_vendas()
    rv = resumo_vendas(vendas)

    assert "faturamento_total" in rv
    assert "ticket_medio" in rv
    assert "total_vendas" in rv
    assert "total_pendentes" in rv
    assert "total_canceladas" in rv
    assert rv["faturamento_total"] > 0
    assert rv["total_vendas"] > 0

def test_resumo_vendas_faturamento_positivo():
    """Faturamento deve ser positivo (temos vendas no seed)."""
    vendas = extrair_vendas()
    rv = resumo_vendas(vendas)
    assert rv["faturamento_total"] > 0

def test_vendas_por_categoria_retorna_dataframe():
    """Deve retornar DataFrame com colunas corretas."""
    vendas = extrair_vendas()
    cat = vendas_por_categoria(vendas)

    assert isinstance(cat, pd.DataFrame)
    if not cat.empty:
        assert "Categoria" in cat.columns
        assert "Faturamento" in cat.columns


def test_vendas_por_vendedor_ordenado():
    """Ranking deve vir ordenado por faturamento (maior primeiro)."""
    vendas = extrair_vendas()
    rank = vendas_por_vendedor(vendas)

    if len(rank) > 1:
        valores = rank["Faturamento"].tolist()
        assert valores == sorted(valores, reverse=True)


def test_vendas_por_mes_tem_meses():
    """Deve ter pelo menos 1 mês de dados."""
    vendas = extrair_vendas()
    mes = vendas_por_mes(vendas)

    assert isinstance(mes, pd.DataFrame)
    assert len(mes) >= 1


def test_comparar_metas_tem_atingimento():
    """Comparativo deve calcular % de atingimento."""
    vendas = extrair_vendas()
    metas = extrair_metas()
    comp = comparar_metas(vendas, metas)

    if not comp.empty:
        assert "Atingimento (%)" in comp.columns
        assert "Meta" in comp.columns
        assert "Real" in comp.columns


def test_resumo_vendas_dataframe_vazio():
    """Se receber DataFrame vazio, não deve crashar."""
    df_vazio = pd.DataFrame()
    rv = resumo_vendas(df_vazio)
    assert rv["faturamento_total"] == 0
    assert rv["total_vendas"] == 0