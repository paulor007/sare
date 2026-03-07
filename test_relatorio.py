"""Teste: gera PDF completo do SARE."""

from src.extractors import extrair_vendas, extrair_metas, extrair_cotacao_dolar
from src.processor import (
    resumo_vendas,
    vendas_por_categoria,
    vendas_por_vendedor,
    vendas_por_produto,
    vendas_por_mes,
    comparar_metas,
)
from src.report import gerar_relatorio

# ── Extrair ──
print("📥 Extraindo dados...")
vendas = extrair_vendas()
metas = extrair_metas()
dolar = extrair_cotacao_dolar()

# ── Processar ──
print("🔄 Processando...")
rv = resumo_vendas(vendas)
cat = vendas_por_categoria(vendas)
rank = vendas_por_vendedor(vendas)
prod = vendas_por_produto(vendas)
mes = vendas_por_mes(vendas)
comp = comparar_metas(vendas, metas)

# ── Gerar PDF ──
print("📄 Gerando PDF...")
caminho = gerar_relatorio(
    resumo=rv,
    top_categorias=cat,
    top_vendedores=rank,
    top_produtos=prod,
    vendas_mes=mes,
    metas_comparativo=comp,
    cotacao_dolar=dolar,
)

print(f"\n✅ Relatório gerado: {caminho}")
print("   Abra o PDF na pasta output/ para conferir!")