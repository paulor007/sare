# ══════════════════════════════════════════════════════════
# COLE ESTE CONTEÚDO NO src/processor.py (substituir tudo)
# ══════════════════════════════════════════════════════════

"""
Processador de dados — motor de análise com Pandas.

Recebe DataFrames dos extratores e gera métricas e resumos.

PROGRAMAÇÃO DEFENSIVA:
- Toda função verifica se as colunas necessárias existem
- Se faltar uma coluna, retorna resultado vazio em vez de quebrar
- Funções helper _has_columns() e _filter_concluidas() evitam repetição

Convenção de status: "concluida", "pendente", "cancelada" (SEM acento)
"""

import pandas as pd


# ══════════════════════════════════════════
# HELPERS (funções auxiliares internas)
# ══════════════════════════════════════════

def _has_columns(df: pd.DataFrame, columns: list) -> bool:
    """
    Verifica se o DataFrame tem todas as colunas necessárias.

    Por que isso existe?
    - Se o extrator SQL mudar e remover uma coluna, o processador
      não quebra — apenas retorna vazio e avisa.
    - Evita KeyError que mata o programa inteiro.
    """
    missing = [col for col in columns if col not in df.columns]
    if missing:
        print(f"⚠️ Colunas ausentes no DataFrame: {missing}")
        print(f"   Colunas disponíveis: {list(df.columns)}")
        return False
    return True


def _filter_by_status(df: pd.DataFrame, status: str) -> pd.DataFrame:
    """
    Filtra DataFrame por status de forma segura.

    Se a coluna 'status' não existir, retorna o DataFrame inteiro
    (assume que todos são válidos).
    """
    if "status" not in df.columns:
        print("⚠️ Coluna 'status' não encontrada — usando todos os registros")
        return df
    return df[df["status"] == status]


# ══════════════════════════════════════════
# FUNÇÕES PRINCIPAIS
# ══════════════════════════════════════════

def resumo_vendas(df_vendas: pd.DataFrame) -> dict:
    """
    Calcula métricas gerais de vendas.

    Retorna dict com:
        faturamento_total, ticket_medio, total_vendas,
        total_pendentes, valor_pendente, total_canceladas
    """
    if df_vendas.empty or not _has_columns(df_vendas, ["valor_total"]):
        return {
            "faturamento_total": 0, "ticket_medio": 0,
            "total_vendas": 0, "total_pendentes": 0,
            "valor_pendente": 0, "total_canceladas": 0,
        }

    concluidas = _filter_by_status(df_vendas, "concluida")
    pendentes = _filter_by_status(df_vendas, "pendente")
    canceladas = _filter_by_status(df_vendas, "cancelada")

    return {
        "faturamento_total": concluidas["valor_total"].sum(),
        "ticket_medio": concluidas["valor_total"].mean() if len(concluidas) > 0 else 0,
        "total_vendas": len(concluidas),
        "total_pendentes": len(pendentes),           # ← len() não sum()!
        "valor_pendente": pendentes["valor_total"].sum(),
        "total_canceladas": len(canceladas),
    }


def vendas_por_categoria(df_vendas: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa vendas concluídas por categoria de produto.

    Retorna DataFrame com: Categoria, Faturamento, Qtd Vendas
    """
    required = ["valor_total", "categoria"]
    if df_vendas.empty or not _has_columns(df_vendas, required):
        return pd.DataFrame(columns=["Categoria", "Faturamento", "Qtd Vendas"])

    concluidas = _filter_by_status(df_vendas, "concluida")  # SEM acento!

    if concluidas.empty:
        return pd.DataFrame(columns=["Categoria", "Faturamento", "Qtd Vendas"])

    grouped = (
        concluidas
        .groupby("categoria")["valor_total"]
        .agg(["sum", "count"])
        .reset_index()
    )
    grouped.columns = ["Categoria", "Faturamento", "Qtd Vendas"]
    grouped = grouped.sort_values("Faturamento", ascending=False)

    return grouped


def vendas_por_vendedor(df_vendas: pd.DataFrame) -> pd.DataFrame:
    """
    Ranking de vendedores por faturamento.

    Retorna DataFrame com: Vendedor, Setor, Faturamento, Qtd Vendas
    """
    required = ["valor_total", "vendedor"]
    if df_vendas.empty or not _has_columns(df_vendas, required):
        return pd.DataFrame(columns=["Vendedor", "Setor", "Faturamento", "Qtd Vendas"])

    concluidas = _filter_by_status(df_vendas, "concluida")

    if concluidas.empty:
        return pd.DataFrame(columns=["Vendedor", "Setor", "Faturamento", "Qtd Vendas"])

    # Setor é opcional (pode não existir no DataFrame)
    group_cols = ["vendedor"]
    if "setor" in concluidas.columns:
        group_cols.append("setor")

    grouped = (
        concluidas
        .groupby(group_cols)["valor_total"]
        .agg(["sum", "count"])
        .reset_index()
    )

    # Montar colunas de saída
    if "setor" in concluidas.columns:
        grouped.columns = ["Vendedor", "Setor", "Faturamento", "Qtd Vendas"]
    else:
        grouped.columns = ["Vendedor", "Faturamento", "Qtd Vendas"]
        grouped["Setor"] = "—"
        grouped = grouped[["Vendedor", "Setor", "Faturamento", "Qtd Vendas"]]

    grouped = grouped.sort_values("Faturamento", ascending=False)

    return grouped


def vendas_por_produto(df_vendas: pd.DataFrame) -> pd.DataFrame:
    """
    Top produtos por faturamento.

    Nota: substituiu vendas_por_cliente porque o modelo de dados
    não tem tabela de clientes. Produto é a próxima informação
    mais relevante para o relatório.

    Retorna DataFrame com: Produto, Faturamento, Qtd Vendas
    """
    required = ["valor_total", "produto"]
    if df_vendas.empty or not _has_columns(df_vendas, required):
        return pd.DataFrame(columns=["Produto", "Faturamento", "Qtd Vendas"])

    concluidas = _filter_by_status(df_vendas, "concluida")

    if concluidas.empty:
        return pd.DataFrame(columns=["Produto", "Faturamento", "Qtd Vendas"])

    grouped = (
        concluidas
        .groupby("produto")["valor_total"]
        .agg(["sum", "count"])
        .reset_index()
    )
    grouped.columns = ["Produto", "Faturamento", "Qtd Vendas"]
    grouped = grouped.sort_values("Faturamento", ascending=False)

    return grouped


def vendas_por_mes(df_vendas: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa vendas concluídas por mês.

    Retorna DataFrame com: Mês, Faturamento
    """
    required = ["valor_total", "data"]
    if df_vendas.empty or not _has_columns(df_vendas, required):
        return pd.DataFrame(columns=["Mês", "Faturamento"])

    concluidas = _filter_by_status(df_vendas, "concluida").copy()

    if concluidas.empty:
        return pd.DataFrame(columns=["Mês", "Faturamento"])

    concluidas["mes"] = concluidas["data"].dt.to_period("M").astype(str)

    grouped = (
        concluidas
        .groupby("mes")["valor_total"]
        .sum()
        .reset_index()
    )
    grouped.columns = ["Mês", "Faturamento"]

    return grouped


def comparar_metas(df_vendas: pd.DataFrame, df_metas: pd.DataFrame) -> pd.DataFrame:
    """
    Compara faturamento real vs metas por vendedor.

    Retorna DataFrame com: Vendedor, Meta, Real, Atingimento (%)
    """
    # Verificar se metas tem as colunas necessárias
    if df_metas.empty or not _has_columns(df_metas, ["Vendedor", "Meta Mensal (R$)"]):
        return pd.DataFrame(columns=["Vendedor", "Meta", "Real", "Atingimento (%)"])

    ranking = vendas_por_vendedor(df_vendas)

    if ranking.empty:
        return pd.DataFrame(columns=["Vendedor", "Meta", "Real", "Atingimento (%)"])

    metas = df_metas[["Vendedor", "Meta Mensal (R$)"]].copy()
    metas.columns = ["Vendedor", "Meta"]

    resultado = metas.merge(
        ranking[["Vendedor", "Faturamento"]],
        on="Vendedor",
        how="left",
    )
    resultado = resultado.rename(columns={"Faturamento": "Real"})
    resultado["Real"] = resultado["Real"].fillna(0)

    resultado["Atingimento (%)"] = (
        (resultado["Real"] / resultado["Meta"]) * 100
    ).round(1)

    resultado = resultado.sort_values("Atingimento (%)", ascending=False)

    return resultado