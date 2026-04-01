"""
Processador de dados — motor de análise com Pandas.

Recebe DataFrames dos extratores e gera métricas e resumos.

PROGRAMAÇÃO DEFENSIVA:
- Toda função verifica se as colunas necessárias existem
- Se faltar uma coluna, retorna resultado vazio em vez de quebrar
- Funções helper _has_columns() e _filter_concluidas() evitam repetição

Convenção de status: "concluida", "pendente", "cancelada" (SEM acento)
"""
from __future__ import annotations
from typing import Any

import pandas as pd
import logging

logger = logging.getLogger("sare.processor")

MESES_PT_ABREV = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}

SEVERIDADE_ORDEM = {
    "Crítica": 0,
    "Atenção": 1,
    "Oportunidade": 2,
    "Informativo": 3, 
}
# ══════════════════════════════════════════
# HELPERS (funções auxiliares internas)
# ══════════════════════════════════════════

def _has_columns(df: pd.DataFrame, columns: list[str]) -> bool:
    """
    Verifica se o DataFrame tem todas as colunas necessárias.

    Por que isso existe?
    - Se o extrator SQL mudar e remover uma coluna, o processador
      não quebra — apenas retorna vazio e avisa.
    - Evita KeyError que mata o programa inteiro.
    """
    missing = [col for col in columns if col not in df.columns]
    if missing:
        logger.warning(" Colunas ausentes no DataFrame: %s", missing)
        logger.debug("  Colunas disponíveis: %s", list(df.columns))
        return False
    return True


def _filter_by_status(df: pd.DataFrame, status: str) -> pd.DataFrame:
    """
    Filtra DataFrame por status de forma segura.

    Se a coluna 'status' não existir, retorna o DataFrame inteiro
    (assume que todos são válidos).
    """
    if "status" not in df.columns:
        logger.warning(" Coluna 'status' não encontrada — usando todos os registros")
        return df
    return df[df["status"] == status]

def _normalizar_datas(df: pd.DataFrame) -> pd.DataFrame:
    """Garante coluna data em datetime quando existir."""
    if df.empty or "data" not in df.columns:
        return df
    if pd.api.types.is_datetime64_any_dtype(df["data"]):
        return df
    copia = df.copy()
    copia["data"] = pd.to_datetime(copia["data"], errors="coerce")
    return copia

def _periodos_disponiveis(df_vendas: pd.DataFrame) -> list[pd.Period]:
    """Retorna períodos mensais ordenados presentes no DataFrame."""
    df = _normalizar_datas(df_vendas)
    if df.empty or not _has_columns(df, ["data"]):
        return []

    datas = df["data"].dropna()
    if datas.empty:
        return []

    return sorted(datas.dt.to_period("M").unique().tolist())

def _formatar_periodo(periodo: pd.Period | None) -> str:
    """
    Formata um período mensal no padrão MM/AAAA.

    Se o período for None, retorna 'N/D' para indicar ausência
    de referência temporal válida.
    """
    if periodo is None:
        return "N/D"
    return periodo.to_timestamp().strftime("%m/%Y")


def _periodo_atual_e_anterior(
    df_vendas: pd.DataFrame,
) -> tuple[pd.Period | None, pd.Period | None]:
    """
    Obtém o período mensal mais recente e o imediatamente anterior.

    Se não houver datas válidas no DataFrame, retorna (None, None).
    Se houver apenas um período disponível, o anterior será None.
    """
    periodos = _periodos_disponiveis(df_vendas)
    if not periodos:
        return None, None
    atual = periodos[-1]
    anterior = periodos[-2] if len(periodos) >= 2 else None
    return atual, anterior

def _resumo_do_periodo(df_vendas: pd.DataFrame, periodo: pd.Period | None) -> dict[str, Any]:
    """
    Gera o resumo de vendas considerando apenas o período informado.

    Se o período for None, retorna um resumo vazio para manter
    compatibilidade com as funções de comparação.
    """
    if periodo is None:
        return resumo_vendas(pd.DataFrame())

    df = _normalizar_datas(df_vendas)
    filtrado = df[df["data"].dt.to_period("M") == periodo]
    return resumo_vendas(filtrado)

def _variacao_percentual(valor_atual: float, valor_anterior: float) -> float | None:
    """
    Calcula a variação percentual entre o valor atual e o anterior.

    Se o valor anterior for zero ou inexistente, retorna:
    - 0.0 quando ambos forem zero;
    - None quando não for possível calcular uma base comparável.
    """
    if valor_anterior in (None, 0):
        if valor_atual == 0:
            return 0.0
        return None
    return round(((valor_atual - valor_anterior) / valor_anterior) * 100, 1)

def _meta_coluna_referencia(
    df_metas: pd.DataFrame,
    data_referencia: pd.Timestamp | None,
) -> tuple[str | None, str]:
    """Escolhe a coluna de meta mais adequada para a data de referência."""
    if df_metas.empty:
        return None, "N/D"

    if data_referencia is None:
        data_referencia = pd.Timestamp.now().normalize()

    mes_nome = MESES_PT_ABREV.get(data_referencia.month)
    coluna_mensal = f"Meta {mes_nome} (R$)" if mes_nome else None

    if coluna_mensal and coluna_mensal in df_metas.columns:
        return coluna_mensal, f"{mes_nome}/{data_referencia.year}"

    if "Meta Mensal (R$)" in df_metas.columns:
        return "Meta Mensal (R$)", f"{data_referencia.strftime('%m/%Y')}"

    candidatas = [
        col for col in df_metas.columns
        if col.startswith("Meta ") and col.endswith("(R$)") and "Trimestre" not in col
    ]
    if candidatas:
        return candidatas[0], candidatas[0].replace("Meta ", "").replace(" (R$)", "")

    if "Meta Trimestre (R$)" in df_metas.columns:
        trimestre = ((data_referencia.month - 1) // 3) + 1
        return "Meta Trimestre (R$)", f"T{trimestre}/{data_referencia.year}"

    return None, "N/D"

def _adicionar_alerta(
    alertas: list[dict[str, str]],
    severidade: str,
    tipo: str,
    insight: str,
    indicador: str,
) -> None:
    """
    Adiciona um alerta estruturado à lista de alertas.

    Cada alerta é armazenado como dicionário padronizado para facilitar
    ordenação, exibição em tabela e reaproveitamento no dashboard e no PDF.
    """
    alertas.append(
        {
            "Severidade": severidade,
            "Tipo": tipo,
            "Insight": insight,
            "Indicador": indicador,
        }
    )

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

    concluidas = _filter_by_status(df_vendas, "concluida") 

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
    if df_metas.empty or "Vendedor" not in df_metas.columns:
        return pd.DataFrame(columns=["Vendedor", "Meta", "Real", "Atingimento (%)"])

    df_vendas = _normalizar_datas(df_vendas)
    data_referencia = None
    if not df_vendas.empty and "data" in df_vendas.columns:
        datas_validas = df_vendas["data"].dropna()
        if not datas_validas.empty:
            data_referencia = datas_validas.max()

    meta_coluna, meta_label = _meta_coluna_referencia(df_metas, data_referencia)
    if not meta_coluna or meta_coluna not in df_metas.columns:
        return pd.DataFrame(columns=["Vendedor", "Meta", "Real", "Atingimento (%)"])

    vendas_referencia = df_vendas.copy()
    if data_referencia is not None and not vendas_referencia.empty and "data" in vendas_referencia.columns:
        if "Trimestre" in meta_coluna:
            trimestre = data_referencia.quarter
            vendas_referencia = vendas_referencia[
                (vendas_referencia["data"].dt.year == data_referencia.year)
                & (vendas_referencia["data"].dt.quarter == trimestre)
            ]
        else:
            vendas_referencia = vendas_referencia[
                (vendas_referencia["data"].dt.year == data_referencia.year)
                & (vendas_referencia["data"].dt.month == data_referencia.month)
            ]

    ranking = vendas_por_vendedor(vendas_referencia)
    metas = df_metas[["Vendedor", meta_coluna]].copy()
    metas.columns = ["Vendedor", "Meta"]

    resultado = metas.merge(
        ranking[["Vendedor", "Faturamento"]] if not ranking.empty else pd.DataFrame(columns=["Vendedor", "Faturamento"]),
        on="Vendedor",
        how="left",
    )
    resultado = resultado.rename(columns={"Faturamento": "Real"})
    resultado["Meta"] = pd.to_numeric(resultado["Meta"], errors="coerce").fillna(0.0)
    resultado["Real"] = pd.to_numeric(resultado["Real"], errors="coerce").fillna(0.0)
    resultado["Atingimento (%)"] = resultado.apply(
        lambda row: round((row["Real"] / row["Meta"]) * 100, 1) if row["Meta"] > 0 else 0.0,
        axis=1,
    )
    resultado = resultado.sort_values("Atingimento (%)", ascending=False)
    resultado.attrs["meta_coluna"] = meta_coluna
    resultado.attrs["meta_label"] = meta_label

    return resultado

def comparar_periodos(df_vendas: pd.DataFrame) -> dict[str, Any]:
    """
    Compara os indicadores do período mais recente com o mês imediatamente anterior.

    A função normaliza a coluna de datas, identifica os dois últimos períodos
    mensais disponíveis e gera um comparativo de faturamento, ticket médio,
    total de pendências e quantidade de vendas.

    Se não houver períodos válidos no DataFrame, retorna uma estrutura padrão
    com valores zerados para manter compatibilidade com dashboard, PDF e demais
    pontos do sistema que consomem esse resultado.

    Também sinaliza se o período atual é parcial, isto é, se os dados ainda
    não cobrem o mês completo até o último dia disponível.
    """
    df_vendas = _normalizar_datas(df_vendas)
    atual, anterior = _periodo_atual_e_anterior(df_vendas)

    if atual is None:
        return {
            "periodo_atual": "N/D",
            "periodo_anterior": "N/D",
            "periodo_atual_label": "N/D",
            "periodo_anterior_label": "N/D",
            "parcial_atual": False,
            "data_referencia": None,
            "faturamento": {"atual": 0.0, "anterior": 0.0, "variacao_pct": 0.0},
            "ticket_medio": {"atual": 0.0, "anterior": 0.0, "variacao_pct": 0.0},
            "pendentes": {"atual": 0.0, "anterior": 0.0, "variacao_pct": 0.0},
            "vendas": {"atual": 0.0, "anterior": 0.0, "variacao_pct": 0.0},
        }

    atual_resumo = _resumo_do_periodo(df_vendas, atual)
    anterior_resumo = _resumo_do_periodo(df_vendas, anterior)

    datas_validas = df_vendas["data"].dropna() if "data" in df_vendas.columns else pd.Series(dtype="datetime64[ns]")
    data_referencia = datas_validas.max() if not datas_validas.empty else None
    parcial_atual = bool(
        data_referencia is not None
        and data_referencia.to_period("M") == atual
        and data_referencia.day < data_referencia.days_in_month
    )

    label_atual = _formatar_periodo(atual)
    if parcial_atual and data_referencia is not None:
        label_atual = f"{label_atual} (até {data_referencia.strftime('%d/%m')})"

    return {
        "periodo_atual": _formatar_periodo(atual),
        "periodo_anterior": _formatar_periodo(anterior),
        "periodo_atual_label": label_atual,
        "periodo_anterior_label": _formatar_periodo(anterior),
        "parcial_atual": parcial_atual,
        "data_referencia": data_referencia.strftime("%d/%m/%Y") if data_referencia is not None else None,
        "faturamento": {
            "atual": atual_resumo["faturamento_total"],
            "anterior": anterior_resumo["faturamento_total"],
            "variacao_pct": _variacao_percentual(
                atual_resumo["faturamento_total"],
                anterior_resumo["faturamento_total"],
            ),
        },
        "ticket_medio": {
            "atual": atual_resumo["ticket_medio"],
            "anterior": anterior_resumo["ticket_medio"],
            "variacao_pct": _variacao_percentual(
                atual_resumo["ticket_medio"],
                anterior_resumo["ticket_medio"],
            ),
        },
        "pendentes": {
            "atual": float(atual_resumo["total_pendentes"]),
            "anterior": float(anterior_resumo["total_pendentes"]),
            "variacao_pct": _variacao_percentual(
                float(atual_resumo["total_pendentes"]),
                float(anterior_resumo["total_pendentes"]),
            ),
        },
        "vendas": {
            "atual": float(atual_resumo["total_vendas"]),
            "anterior": float(anterior_resumo["total_vendas"]),
            "variacao_pct": _variacao_percentual(
                float(atual_resumo["total_vendas"]),
                float(anterior_resumo["total_vendas"]),
            ),
        },
    }

def gerar_alertas_insights(df_vendas: pd.DataFrame, df_metas: pd.DataFrame, limite: int = 6) -> pd.DataFrame:
    """
    Gera alertas automáticos e insights gerenciais com base nos dados de vendas e metas.

    A função analisa o comparativo entre períodos, o atingimento de metas e o
    desempenho por categoria para identificar situações relevantes, como queda
    de faturamento, aumento de pendências, vendedores abaixo da meta, risco de
    não atingir o objetivo consolidado e oportunidades de crescimento.

    Os alertas são retornados em formato tabular, com severidade, tipo,
    descrição do insight e indicador resumido, permitindo reaproveitamento
    no dashboard, no PDF e em outros pontos do sistema.

    Se nenhuma condição relevante for encontrada, retorna um alerta informativo
    indicando estabilidade dos principais indicadores.
    """
    df_vendas = _normalizar_datas(df_vendas)
    comparativo = comparar_periodos(df_vendas)
    metas = comparar_metas(df_vendas, df_metas)
    alertas: list[dict[str, str]] = []

    faturamento_var = comparativo["faturamento"]["variacao_pct"]
    if faturamento_var is not None and faturamento_var <= -10:
        _adicionar_alerta(
            alertas,
            "Crítica" if faturamento_var <= -20 else "Atenção",
            "Faturamento",
            f"Faturamento de {comparativo['periodo_atual_label']} caiu {abs(faturamento_var):.1f}% versus {comparativo['periodo_anterior_label']}.",
            f"{faturamento_var:+.1f}%",
        )

    ticket_var = comparativo["ticket_medio"]["variacao_pct"]
    if ticket_var is not None and ticket_var <= -5:
        _adicionar_alerta(
            alertas,
            "Atenção",
            "Ticket médio",
            f"Ticket médio está em queda: {comparativo['periodo_atual_label']} ficou {abs(ticket_var):.1f}% abaixo de {comparativo['periodo_anterior_label']}.",
            f"{ticket_var:+.1f}%",
        )

    pend_var = comparativo["pendentes"]["variacao_pct"]
    if pend_var is not None and pend_var >= 10:
        _adicionar_alerta(
            alertas,
            "Crítica" if pend_var >= 25 else "Atenção",
            "Pendências",
            f"Volume de pendências aumentou {pend_var:.1f}% em {comparativo['periodo_atual_label']}.",
            f"{pend_var:+.1f}%",
        )

    if not metas.empty:
        abaixo_meta = metas[metas["Atingimento (%)"] < 100].sort_values("Atingimento (%)")
        meta_label = metas.attrs.get("meta_label", "período atual")

        criticos = abaixo_meta[abaixo_meta["Atingimento (%)"] < 80]
        if not criticos.empty:
            pior = criticos.iloc[0]
            _adicionar_alerta(
                alertas,
                "Crítica",
                "Meta",
                f"{len(criticos)} vendedor(es) estão abaixo de 80% da meta de {meta_label}. Pior caso: {pior['Vendedor']} com {pior['Atingimento (%)']:.1f}%.",
                f"{pior['Atingimento (%)']:.1f}%",
            )
        elif not abaixo_meta.empty:
            pior = abaixo_meta.iloc[0]
            _adicionar_alerta(
                alertas,
                "Atenção",
                "Meta",
                f"Ainda há vendedor(es) abaixo da meta de {meta_label}. Menor atingimento: {pior['Vendedor']} com {pior['Atingimento (%)']:.1f}%.",
                f"{pior['Atingimento (%)']:.1f}%",
            )

        data_ref = None
        if comparativo["data_referencia"]:
            data_ref = pd.to_datetime(comparativo["data_referencia"], dayfirst=True, errors="coerce")

        if data_ref is not None and not pd.isna(data_ref):
            faturamento_atual = comparativo["faturamento"]["atual"]
            dias_passados = max(data_ref.day, 1)
            projeção_mes = (faturamento_atual / dias_passados) * data_ref.days_in_month
            meta_total = float(metas["Meta"].sum())
            if meta_total > 0:
                proj_pct = (projeção_mes / meta_total) * 100
                if proj_pct < 95:
                    _adicionar_alerta(
                        alertas,
                        "Atenção",
                        "Projeção",
                        f"No ritmo atual, o mês projeta {proj_pct:.1f}% da meta consolidada de {meta_label}.",
                        f"{proj_pct:.1f}% da meta",
                    )
                elif proj_pct >= 105:
                    _adicionar_alerta(
                        alertas,
                        "Oportunidade",
                        "Projeção",
                        f"No ritmo atual, a equipe projeta superar a meta consolidada de {meta_label} em {proj_pct - 100:.1f}%.",
                        f"{proj_pct:.1f}% da meta",
                    )

    atual, anterior = _periodo_atual_e_anterior(df_vendas)
    if atual is not None and anterior is not None and _has_columns(df_vendas, ["categoria", "valor_total", "data"]):
        concluidas = _filter_by_status(df_vendas, "concluida").copy()
        concluidas["periodo"] = concluidas["data"].dt.to_period("M")
        categorias = (
            concluidas.groupby(["periodo", "categoria"])["valor_total"].sum().reset_index()
            .pivot(index="categoria", columns="periodo", values="valor_total")
            .fillna(0)
        )
        if atual in categorias.columns and anterior in categorias.columns:
            crescimento = (categorias[atual] - categorias[anterior]).sort_values(ascending=False)
            melhores = crescimento[crescimento > 0]
            if not melhores.empty:
                categoria = melhores.index[0]
                ganho = melhores.iloc[0]
                base = categorias.loc[categoria, anterior]
                ganho_pct = ((ganho / base) * 100) if base > 0 else None
                indicador = f"R$ {ganho:,.2f}" if ganho_pct is None else f"+{ganho_pct:.1f}%"
                insight = (
                    f"Categoria {categoria} lidera o crescimento em {comparativo['periodo_atual_label']}, "
                    f"com ganho de R$ {ganho:,.2f} sobre {comparativo['periodo_anterior_label']}."
                )
                _adicionar_alerta(
                    alertas,
                    "Oportunidade",
                    "Categoria",
                    insight,
                    indicador,
                )

    if not alertas:
        _adicionar_alerta(
            alertas,
            "Informativo",
            "Monitoramento",
            "Sem alertas críticos no período selecionado. Os principais indicadores estão estáveis.",
            "Estável",
        )

    alertas_df = pd.DataFrame(alertas)
    alertas_df["ordem"] = alertas_df["Severidade"].map(SEVERIDADE_ORDEM).fillna(99)
    alertas_df = alertas_df.sort_values(["ordem", "Tipo", "Insight"]).drop(columns="ordem")

    return alertas_df.head(limite).reset_index(drop=True)