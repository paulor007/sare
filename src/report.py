"""
Gerador de relatórios PDF profissionais.

Usa ReportLab para criar PDFs com:
- Cabeçalho com nome da empresa e data
- Cards de métricas (faturamento, vendas, ticket médio, dólar)
- Tabelas formatadas com zebra (categorias, vendedores, produtos)
- Evolução mensal
- Metas vs realizado
- Rodapé com timestamp

Tema visual: Steel Blue (#5ba4d9)
"""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)

import pandas as pd

from src.config import EMPRESA_NOME, RELATORIO_TITULO, OUTPUT_DIR


# ══════════════════════════════════════════
# CORES DO TEMA
# ══════════════════════════════════════════

COR_PRIMARIA = colors.HexColor("#5ba4d9")       # Steel blue
COR_CINZA_CLARO = colors.HexColor("#f8fafc")    # Fundo zebra
COR_CINZA_BORDA = colors.HexColor("#e2e8f0")    # Bordas leves
COR_TEXTO = colors.HexColor("#334155")           # Texto principal
COR_TEXTO_LEVE = colors.HexColor("#94a3b8")     # Texto secundário
COR_ESCURO = colors.HexColor("#1e293b")          # Valores grandes


# ══════════════════════════════════════════
# ESTILOS CUSTOMIZADOS
# ══════════════════════════════════════════

def _estilos():
    """
    Cria estilos de texto para o PDF.

    Por que customizar?
    - Os estilos padrão do ReportLab são genéricos
    - Customizando, o PDF fica com identidade visual consistente
    - Todas as seções usam os mesmos estilos → profissional
    """
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TituloRelatorio",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=COR_PRIMARIA,
        spaceAfter=16,
    ))

    styles.add(ParagraphStyle(
        name="Subtitulo",
        fontName="Helvetica",
        fontSize=11,
        textColor=COR_TEXTO_LEVE,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name="SecaoTitulo",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=COR_PRIMARIA,
        spaceBefore=20,
        spaceAfter=10,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        name="TextoNormal",
        fontName="Helvetica",
        fontSize=10,
        textColor=COR_TEXTO,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="MetricaLabel",
        fontName="Helvetica",
        fontSize=8,
        textColor=COR_TEXTO_LEVE,
    ))

    styles.add(ParagraphStyle(
        name="MetricaValor",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=COR_ESCURO,
    ))

    return styles


# ══════════════════════════════════════════
# COMPONENTES REUTILIZÁVEIS
# ══════════════════════════════════════════

def _card_metrica(label: str, valor: str) -> Table:
    """
    Cria um "card" visual com label + valor grande.

    Usado para mostrar métricas principais no topo do relatório.
    Exemplo: [Faturamento | R$ 285.430,00]

    É uma Table do ReportLab estilizada como card.
    """
    styles = _estilos()
    data = [
        [Paragraph(label, styles["MetricaLabel"])],
        [Paragraph(valor, styles["MetricaValor"])],
    ]
    table = Table(data, colWidths=[4.5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.5, COR_CINZA_BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _tabela_formatada(cabecalho: list, dados: list, col_widths=None) -> Table:
    """
    Cria tabela com estilo profissional.

    Características:
    - Cabeçalho com fundo steel blue e texto branco
    - Linhas alternadas (zebra) para facilitar leitura
    - Valores numéricos alinhados à direita
    - Bordas discretas

    Parâmetros:
        cabecalho: lista de strings (["Nome", "Valor", ...])
        dados: lista de listas ([["Item 1", "R$ 100"], ...])
        col_widths: largura de cada coluna em cm (opcional)
    """
    table_data = [cabecalho] + dados
    table = Table(table_data, colWidths=col_widths)

    style_commands = [
        # Cabeçalho
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),

        # Corpo
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),  # Valores à direita

        # Bordas
        ("LINEBELOW", (0, 0), (-1, 0), 1, COR_PRIMARIA),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, COR_CINZA_BORDA),
    ]

    # Zebra: linhas pares com fundo cinza claro
    for i in range(2, len(table_data), 2):
        style_commands.append(
            ("BACKGROUND", (0, i), (-1, i), COR_CINZA_CLARO)
        )

    table.setStyle(TableStyle(style_commands))
    return table


def _df_para_tabela(df: pd.DataFrame, col_widths=None, max_linhas: int = 10) -> Table:
    """
    Converte DataFrame do Pandas em Table do ReportLab.

    Por que limitar linhas?
    - O PDF tem espaço limitado
    - 10 linhas é suficiente para ranking (top 10)
    - Se tiver mais, mostra só os primeiros

    Formata automaticamente:
    - Números float → R$ com 2 casas decimais
    - Números int → sem casas decimais
    """
    if df.empty:
        return Paragraph("<i>Sem dados disponíveis</i>", _estilos()["TextoNormal"])

    # Limitar linhas
    df_limited = df.head(max_linhas)

    # Cabeçalho
    cabecalho = list(df_limited.columns)

    # Dados formatados
    dados = []
    for _, row in df_limited.iterrows():
        linha = []
        for col in df_limited.columns:
            val = row[col]
            if isinstance(val, float):
                linha.append(f"R$ {val:,.2f}")
            else:
                linha.append(str(val))
        dados.append(linha)

    return _tabela_formatada(cabecalho, dados, col_widths)


# ══════════════════════════════════════════
# FUNÇÃO PRINCIPAL — GERAR PDF
# ══════════════════════════════════════════

def gerar_relatorio(
    resumo: dict,
    top_categorias: pd.DataFrame,
    top_vendedores: pd.DataFrame,
    top_produtos: pd.DataFrame,
    vendas_mes: pd.DataFrame,
    metas_comparativo: pd.DataFrame,
    cotacao_dolar: dict,
    comparativo_periodos: dict | None = None,
    insights: pd.DataFrame | None = None,


) -> str:
    """
    Gera relatório PDF completo.

    Recebe dados já processados (do processor.py) e monta o PDF.
    Retorna o caminho do arquivo gerado.

    Seções do PDF:
    1. Cabeçalho (empresa + data)
    2. Cards de métricas (faturamento, vendas, ticket, dólar)
    3. Vendas por Categoria (tabela)
    4. Ranking de Vendedores (tabela)
    5. Top Produtos (tabela)
    6. Evolução Mensal (tabela)
    7. Metas vs Realizado (tabela)
    8. Rodapé (SARE + timestamp)
    """
    styles = _estilos()
    agora = datetime.now()

    # Nome do arquivo com timestamp (nunca sobrescreve)
    nome_arquivo = f"relatorio_{agora.strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho = OUTPUT_DIR / nome_arquivo

    # Criar documento A4 com margens de 2cm
    doc = SimpleDocTemplate(
        str(caminho),
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    elementos = []

    # ── 1. CABEÇALHO ──
    elementos.append(Paragraph(
        RELATORIO_TITULO,
        styles["TituloRelatorio"],
    ))
    elementos.append(Paragraph(
        f"{EMPRESA_NOME}  —  Gerado em {agora.strftime('%d/%m/%Y às %H:%M')}",
        styles["Subtitulo"],
    ))
    elementos.append(HRFlowable(
        width="100%", thickness=1,
        color=COR_PRIMARIA, spaceAfter=20,
    ))

    # ── 2. CARDS DE MÉTRICAS ──
    cards = Table(
        [[
            _card_metrica("Faturamento", f"R$ {resumo['faturamento_total']:,.2f}"),
            _card_metrica("Vendas", f"{resumo['total_vendas']}"),
            _card_metrica("Ticket Médio", f"R$ {resumo['ticket_medio']:,.2f}"),
            _card_metrica("Dólar", f"R$ {cotacao_dolar['valor']:.2f}"),
        ]],
        colWidths=[4.4 * cm] * 4,
    )
    cards.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elementos.append(cards)
    elementos.append(Spacer(1, 10))

    # Info complementar
    info = (
        f"Pendentes: <b>{resumo['total_pendentes']}</b> "
        f"(R$ {resumo.get('valor_pendente', 0):,.2f})  |  "
        f"Canceladas: <b>{resumo['total_canceladas']}</b>  |  "
        f"Dólar em: <b>{cotacao_dolar['data']}</b>"
    )
    elementos.append(Paragraph(info, styles["TextoNormal"]))
    elementos.append(Spacer(1, 10))

    if comparativo_periodos:
        resumo_periodos = (
            f"Comparativo de períodos: <b>{comparativo_periodos.get('periodo_atual_label', 'N/D')}</b> vs "
            f"<b>{comparativo_periodos.get('periodo_anterior_label', 'N/D')}</b> | "
            f"Faturamento: <b>{comparativo_periodos['faturamento']['variacao_pct'] if comparativo_periodos['faturamento']['variacao_pct'] is not None else 0:+.1f}%</b> | "
            f"Ticket: <b>{comparativo_periodos['ticket_medio']['variacao_pct'] if comparativo_periodos['ticket_medio']['variacao_pct'] is not None else 0:+.1f}%</b> | "
            f"Pendências: <b>{comparativo_periodos['pendentes']['variacao_pct'] if comparativo_periodos['pendentes']['variacao_pct'] is not None else 0:+.1f}%</b>"
        )
        elementos.append(Paragraph(resumo_periodos, styles["TextoNormal"]))
        elementos.append(Spacer(1, 12))

    if insights is not None and not insights.empty:
        elementos.append(Paragraph("Alertas e Insights Automáticos", styles["SecaoTitulo"]))
        elementos.append(_df_para_tabela(
            insights[["Severidade", "Tipo", "Insight", "Indicador"]],
            col_widths=[2.7 * cm, 2.9 * cm, 8.6 * cm, 3.3 * cm],
            max_linhas=8,
        ))
        elementos.append(Spacer(1, 15))


    # ── 3. VENDAS POR CATEGORIA ──
    elementos.append(Paragraph("Vendas por Categoria", styles["SecaoTitulo"]))
    elementos.append(_df_para_tabela(
        top_categorias,
        col_widths=[7 * cm, 5 * cm, 5 * cm],
    ))
    elementos.append(Spacer(1, 15))

    # ── 4. RANKING DE VENDEDORES ──
    elementos.append(Paragraph("Ranking de Vendedores", styles["SecaoTitulo"]))
    elementos.append(_df_para_tabela(
        top_vendedores,
        col_widths=[5 * cm, 3.5 * cm, 4.5 * cm, 4 * cm],
    ))
    elementos.append(Spacer(1, 15))

    # ── 5. TOP PRODUTOS ──
    elementos.append(Paragraph("Top Produtos", styles["SecaoTitulo"]))
    elementos.append(_df_para_tabela(
        top_produtos.head(5),
        col_widths=[7 * cm, 5 * cm, 5 * cm],
    ))
    elementos.append(Spacer(1, 15))

    # ── 6. EVOLUÇÃO MENSAL ──
    elementos.append(Paragraph("Evolução Mensal", styles["SecaoTitulo"]))
    elementos.append(_df_para_tabela(
        vendas_mes,
        col_widths=[8.5 * cm, 8.5 * cm],
    ))
    elementos.append(Spacer(1, 15))

    # ── 7. METAS VS REALIZADO ──
    if not metas_comparativo.empty:
        elementos.append(Paragraph("Metas vs Realizado", styles["SecaoTitulo"]))
        elementos.append(_df_para_tabela(
            metas_comparativo,
            col_widths=[4 * cm, 4.5 * cm, 4.5 * cm, 4 * cm],
        ))
        elementos.append(Spacer(1, 15))

    # ── 8. RODAPÉ ──
    elementos.append(HRFlowable(
        width="100%", thickness=0.5,
        color=COR_CINZA_BORDA, spaceAfter=10,
    ))
    elementos.append(Paragraph(
        f"SARE — Sistema de Automação de Relatórios Empresariais  |  "
        f"Gerado automaticamente em {agora.strftime('%d/%m/%Y %H:%M:%S')}",
        ParagraphStyle(
            name="Rodape",
            fontName="Helvetica",
            fontSize=7,
            textColor=COR_TEXTO_LEVE,
            alignment=TA_CENTER,
        ),
    ))

    # ── BUILD ──
    doc.build(elementos)

    return str(caminho)