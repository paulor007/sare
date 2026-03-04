"""
Seed — Popula o banco de dados com dados da TechNova Soluções.

Rode uma vez:
    python -m data.seed

Gera:
    - 8 vendedores
    - 12 produtos
    - 520 vendas em 3 meses
"""

import random
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import criar_tabelas, get_session, Vendedor, Produto, Venda

def seed():
    """Popula o banco com dados."""

    # Cria as tabelas
    criar_tabelas()

    session = get_session()

    # Limpa dados existente (para re-rodar sem duplicar)
    session.query(Venda).delete()
    session.query(Produto).delete()
    session.query(Vendedor).delete()
    session.commit()

    # ══════════════════════════════════════════
    # VENDEDORES
    # ══════════════════════════════════════════

    vendedores = [
        Vendedor(nome="Paulo Lavarini", email="paulo.lavarini@technova.com", departamento="Comercial"),
        Vendedor(nome="João Lavarini", email="joao.lavarini@technova.com", departamento="Comercial"),
        Vendedor(nome="Carol Marques", email="caro.marques@technova.com", departamento="Empresarial"),
        Vendedor(nome="Helena.Lavarini", email="helena.lavarini@technova.com", departamento="Empresarial"),
        Vendedor(nome="Catharina.Lavarini", email="catharina.lavarini@technova.com", departamento="Comercial"),
        Vendedor(nome="Luisa.Lavarini", email="luisa.lavarini@technova.com", departamento="Empresarial"),
        Vendedor(nome="Cleiton.Lavarini", email="cleiton.lavarini@technova.com", departamento="Comercial"),
        Vendedor(nome="Gisele Lavarini", email="gisele.lavarini@technova.com", departamento="Empresarial"),
        Vendedor(nome="Josy Lima", email="josy.lima@technova.com", departamento="Empresarial"),
    ]

    session.add_all(vendedores)
    session.commit()

    # ══════════════════════════════════════════
    # PRODUTOS
    # ══════════════════════════════════════════

    produtos = [
        # Software
        Produto(nome="Licença ERP Empresarial", categoria="Software", preco=4500.00),
        Produto(nome="Licença CRM Pro", categoria="Software", preco=2800.00),
        Produto(nome="Módulo BI Analytics", categoria="Software", preco=3200.00),

        # Serviços
        Produto(nome="Consultoria TI (8h)", categoria="Serviço", preco=1440.00),
        Produto(nome="Treinamento Equipe (16h)", categoria="Serviço", preco=3600.00),
        Produto(nome="Suporte Premium Mensal", categoria="Serviço", preco=890.00),

        # Infraestrutura
        Produto(nome="Servidor Cloud (mês)", categoria="Infraestrutura", preco=650.00),
        Produto(nome="Backup Corporativo (mês)", categoria="Infraestrutura", preco=420.00),
        Produto(nome="Firewall Gerenciado (mês)", categoria="Infraestrutura", preco=780.00),

        # Projetos
        Produto(nome="Desenvolvimento Web", categoria="Projeto", preco=15000.00),
        Produto(nome="App Mobile", categoria="Projeto", preco=22000.00),
        Produto(nome="Automação de Processos", categoria="Projeto", preco=12000.00),
    ]

    session.add_all(produtos)
    session.commit()

    # ══════════════════════════════════════════
    # VENDAS (520 nos últimos 3 meses)
    # ══════════════════════════════════════════

    random.seed(42)  # Resultados reproduzíveis

    status_opcoes = ["concluida", "concluida", "concluida", "concluida", "pendente", "cancelada"]
    vendas = []

    # Pega IDs reais
    ids_vendedores = [v.id for v in vendedores]
    ids_produtos = [p.id for p in produtos]
    precos = {p.id: p.preco for p in produtos}

    for _ in range(520):
        dias_atras = random.randint(0, 90)
        data = datetime.now().date() - timedelta(days=dias_atras)

        vendedor_id = random.choice(ids_vendedores)
        produto_id = random.choice(ids_produtos)
        quantidade = random.randint(1, 5)

        # Variação de ±10% no preço (descontos/negociação)
        preco_base = precos[produto_id]
        variacao = random.uniform(0.90, 1.10)
        valor_unitario = round(preco_base * variacao, 2)
        valor_total = round(valor_unitario * quantidade, 2)

        status = random.choice(status_opcoes)

        vendas.append(Venda(
            data=data,
            vendedor_id=vendedor_id,
            produto_id=produto_id,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
            valor_total=valor_total,
            status=status,
        ))

    session.add_all(vendas)
    session.commit()

    # ══════════════════════════════════════════
    # RESUMO
    # ══════════════════════════════════════════

    total_vendas = session.query(Venda).count()
    total_concluidas = session.query(Venda).filter(Venda.status == "concluida").count()
    total_pendentes = session.query(Venda).filter(Venda.status == "pendente").count()
    total_canceladas = session.query(Venda).filter(Venda.status == "cancelada").count()

    print("=" * 50)
    print("  SEED — TechNova Soluções")
    print("=" * 50)
    print(f"  ✅ {len(vendedores)} vendedores criados")
    print(f"  ✅ {len(produtos)} produtos criados")
    print(f"  ✅ {total_vendas} vendas geradas")
    print(f"     → {total_concluidas} concluídas")
    print(f"     → {total_pendentes} pendentes")
    print(f"     → {total_canceladas} canceladas")
    print("=" * 50)

    session.close()

if __name__ == "__main__":
    seed()
