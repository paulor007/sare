"""
Testes do gerador de relatório PDF.

Verifica se o PDF é gerado corretamente no disco.
"""

from pathlib import Path
from src.extractors import extrair_vendas, extrair_metas, extrair_cotacao_dolar
from src.processor import (
    resumo_vendas, vendas_por_categoria, vendas_por_vendedor,
    vendas_por_produto, vendas_por_mes, comparar_metas,
)
from src.report import gerar_relatorio

def test_gerar_relatorio_cria_pdf():
    """Verifica se o PDF é criado no disco."""
    vendas = extrair_vendas()
    metas = extrair_metas()
    dolar = extrair_cotacao_dolar()

    rv = resumo_vendas(vendas)

    caminho = gerar_relatorio(
        resumo=rv,
        top_categorias=vendas_por_categoria(vendas),
        top_vendedores=vendas_por_vendedor(vendas),
        top_produtos=vendas_por_produto(vendas),
        vendas_mes=vendas_por_mes(vendas),
        metas_comparativo=comparar_metas(vendas, metas),
        cotacao_dolar=dolar,
    )

    assert Path(caminho).exists(), "PDF não foi criado"
    assert caminho.endswith(".pdf"), "Arquivo não é PDF"
    assert Path(caminho).stat().st_size > 0, "PDF está vazio"