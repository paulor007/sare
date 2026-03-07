"""Teste: gera PDF e envia por email."""

from src.extractors import extrair_vendas, extrair_metas, extrair_cotacao_dolar
from src.processor import (
    resumo_vendas, vendas_por_categoria, vendas_por_vendedor,
    vendas_por_produto, vendas_por_mes, comparar_metas,
)
from src.report import gerar_relatorio
from src.mailer import enviar_relatorio

# Extrair + processar
vendas = extrair_vendas()
metas = extrair_metas()
dolar = extrair_cotacao_dolar()

rv = resumo_vendas(vendas)

# Gerar PDF
caminho = gerar_relatorio(
    resumo=rv,
    top_categorias=vendas_por_categoria(vendas),
    top_vendedores=vendas_por_vendedor(vendas),
    top_produtos=vendas_por_produto(vendas),
    vendas_mes=vendas_por_mes(vendas),
    metas_comparativo=comparar_metas(vendas, metas),
    cotacao_dolar=dolar,
)
print(f"📄 PDF gerado: {caminho}")

# Enviar email
print("\n📧 Enviando email...")
sucesso = enviar_relatorio(caminho)

if sucesso:
    print("\n🎉 Confira seu Gmail!")
else:
    print("\n⚠️ Email não enviado. Verifique o .env")
    print("   O PDF foi gerado com sucesso em output/")