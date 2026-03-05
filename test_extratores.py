"""Teste rápido dos 3 extratores."""

from src.extractors import extrair_vendas, extrair_metas, extrair_cotacao_dolar

# ── Vendas (SQL) ──
print("══ Vendas (SQL) ══")
vendas = extrair_vendas()
print(f"Total: {len(vendas)} registros")
print(f"Colunas: {list(vendas.columns)}")
print(f"Vendedores: {vendas['vendedor'].nunique()}")
print(f"Produtos: {vendas['produto'].nunique()}")
print(vendas.head(3).to_string(index=False))

# ── Metas (Excel) ──
print("\n══ Metas (Excel) ══")
metas = extrair_metas()
print(f"Total: {len(metas)} vendedores")
print(metas.to_string(index=False))

# ── Dólar (API) ──
print("\n══ Cotação Dólar (API BCB) ══")
dolar = extrair_cotacao_dolar()
print(f"R$ {dolar['valor']:.2f} em {dolar['data']}")

print("\n Todos os extratores funcionando!")