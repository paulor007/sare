"""
SARE — Dashboard Interativo + Terminal + Configurações.

Interface visual completa para o portfolio.
- Filtros globais
- Perfil de visualização
- Status operacional
- Histórico de execução
- Configurações salváveis em session_state

Rodar: streamlit run dashboard.py
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.config import (
    DB_PATH,
    EMAIL_DESTINATARIO,
    EMAIL_REMETENTE,
    EMPRESA_NOME,
    OUTPUT_DIR,
)

from src.extractors import extrair_vendas, extrair_metas, extrair_cotacao_dolar
from src.processor import (
    resumo_vendas,
    vendas_por_categoria,
    vendas_por_vendedor,
    vendas_por_produto,
    vendas_por_mes,
    comparar_metas,
    comparar_periodos,
    gerar_alertas_insights,
)
from src.report import gerar_relatorio
from src.upload_processor import (
    preparar_upload_vendas,
    preparar_upload_metas,
    construir_metas_demonstrativas,
    dataframe_para_excel_bytes,
)


# ══════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ══════════════════════════════════════════

st.set_page_config(
    page_title=f"SARE — {EMPRESA_NOME}",
    page_icon="🏢",
    layout="wide",
)

PERSIST_DIR = Path("data/uploads")
PERSIST_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_VENDAS_PATH = PERSIST_DIR / "vendas_upload_atual.pkl"
UPLOAD_METAS_PATH = PERSIST_DIR / "metas_upload_atual.pkl"
UPLOAD_META_INFO_PATH = PERSIST_DIR / "upload_info.txt"

# ══════════════════════════════════════════
# ESTADO DA SESSÃO
# ══════════════════════════════════════════

def init_session_state() -> None:
    """Inicializa configurações e histórico local da sessão."""
    if "perfil_usuario" not in st.session_state:
        st.session_state.perfil_usuario = "Gestor"

    if "cfg_horario" not in st.session_state:
        st.session_state.cfg_horario = datetime.strptime("08:00", "%H:%M").time()

    if "cfg_intervalo" not in st.session_state:
        st.session_state.cfg_intervalo = "Diário"

    if "cfg_email_remetente" not in st.session_state:
        st.session_state.cfg_email_remetente = EMAIL_REMETENTE or "relatorios@technova.com"

    if "cfg_email_destinatario" not in st.session_state:
        st.session_state.cfg_email_destinatario = EMAIL_DESTINATARIO or "diretor@technova.com"

    if "cfg_periodo" not in st.session_state:
        st.session_state.cfg_periodo = "Últimos 90 dias"

    if "cfg_formato" not in st.session_state:
        st.session_state.cfg_formato = "PDF + Email"

    if "cfg_secoes" not in st.session_state:
        st.session_state.cfg_secoes = [
            "Resumo executivo",
            "Vendas por categoria",
            "Ranking vendedores",
            "Top produtos",
            "Evolução mensal",
            "Metas vs realizado",
        ]

    if "historico_execucoes" not in st.session_state:
        st.session_state.historico_execucoes = []

    if "ultima_execucao" not in st.session_state:
        st.session_state.ultima_execucao = {
            "status": "Sistema iniciado",
            "tipo": "boot",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "detalhe": "Dashboard carregado com sucesso.",
        }


init_session_state()

# ══════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════

def registrar_evento(tipo: str, status: str, detalhe: str) -> None:
    """Registra evento no histórico local da interface."""
    evento = {
        "tipo": tipo,
        "status": status,
        "detalhe": detalhe,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    st.session_state.ultima_execucao = evento
    st.session_state.historico_execucoes.insert(0, evento)
    st.session_state.historico_execucoes = st.session_state.historico_execucoes[:12]


@st.cache_data(ttl=300)
def carregar_dados():
    """Carrega dados brutos e aplica processamento inicial com cache."""
    vendas = extrair_vendas()
    metas = extrair_metas()
    dolar = extrair_cotacao_dolar()
    return vendas, metas, dolar


def normalizar_datas(df: pd.DataFrame) -> pd.DataFrame:
    """Garante parsing seguro da coluna data."""
    if df.empty:
        return df

    df = df.copy()
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df


def aplicar_filtros_globais(
    vendas_df: pd.DataFrame,
    periodo_label: str,
    status_list: list[str],
    vendedores_list: list[str],
    categorias_list: list[str],
) -> pd.DataFrame:
    """Aplica filtros globais ao DataFrame de vendas."""
    if vendas_df.empty:
        return vendas_df

    df = vendas_df.copy()
    hoje = pd.Timestamp.now().normalize()

    if "data" in df.columns and pd.api.types.is_datetime64_any_dtype(df["data"]):
        if periodo_label == "Últimos 30 dias":
            data_inicio = hoje - pd.Timedelta(days=30)
            df = df[df["data"] >= data_inicio]
        elif periodo_label == "Últimos 60 dias":
            data_inicio = hoje - pd.Timedelta(days=60)
            df = df[df["data"] >= data_inicio]
        elif periodo_label == "Últimos 90 dias":
            data_inicio = hoje - pd.Timedelta(days=90)
            df = df[df["data"] >= data_inicio]
        elif periodo_label == "Mês atual":
            inicio_mes = hoje.replace(day=1)
            df = df[df["data"] >= inicio_mes]
        elif periodo_label == "Trimestre atual":
            mes_inicio = ((hoje.month - 1) // 3) * 3 + 1
            inicio_tri = pd.Timestamp(year=hoje.year, month=mes_inicio, day=1)
            df = df[df["data"] >= inicio_tri]
        elif periodo_label == "Tudo":
            pass

    if "status" in df.columns and status_list:
        df = df[df["status"].isin(status_list)]

    if "vendedor" in df.columns and vendedores_list:
        df = df[df["vendedor"].isin(vendedores_list)]

    if "categoria" in df.columns and categorias_list:
        df = df[df["categoria"].isin(categorias_list)]

    return df


def processar_dados(vendas_filtradas: pd.DataFrame, metas_df: pd.DataFrame) -> dict:
    """Gera blocos processados a partir das vendas filtradas."""
    return {
        "resumo": resumo_vendas(vendas_filtradas),
        "categorias": vendas_por_categoria(vendas_filtradas),
        "vendedores": vendas_por_vendedor(vendas_filtradas),
        "produtos": vendas_por_produto(vendas_filtradas),
        "mensal": vendas_por_mes(vendas_filtradas),
        "metas_comp": comparar_metas(vendas_filtradas, metas_df),
        "comparativo": comparar_periodos(vendas_filtradas),
        "insights": gerar_alertas_insights(vendas_filtradas, metas_df),
    }


def obter_ultima_geracao_pdf() -> str:
    """Retorna timestamp do PDF mais recente na pasta output."""
    try:
        arquivos = list(Path(OUTPUT_DIR).glob("relatorio_*.pdf"))
        if not arquivos:
            return "Nenhum PDF gerado ainda"
        ultimo = max(arquivos, key=lambda arq: arq.stat().st_mtime)
        return datetime.fromtimestamp(ultimo.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "Não foi possível ler a pasta output"


def status_fonte(ativo: bool) -> str:
    return "🟢 Online" if ativo else "🔴 Indisponível"


def salvar_upload_persistido(vendas_df: pd.DataFrame, metas_df: pd.DataFrame, fonte_dados: str, fonte_metas: str) -> None:
    """Salva o upload atual em disco para manter a fonte após refresh do Streamlit."""
    vendas_df.to_pickle(UPLOAD_VENDAS_PATH)
    metas_df.to_pickle(UPLOAD_METAS_PATH)
    UPLOAD_META_INFO_PATH.write_text(f"{fonte_dados}\n{fonte_metas}", encoding="utf-8")


def carregar_upload_persistido() -> tuple[pd.DataFrame, pd.DataFrame, str, str] | None:
    """Carrega upload persistido em disco quando existir."""
    if not UPLOAD_VENDAS_PATH.exists() or not UPLOAD_METAS_PATH.exists():
        return None

    vendas_df = pd.read_pickle(UPLOAD_VENDAS_PATH)
    metas_df = pd.read_pickle(UPLOAD_METAS_PATH)
    fonte_dados = "Upload persistido"
    fonte_metas = "Upload persistido"

    if UPLOAD_META_INFO_PATH.exists():
        linhas = UPLOAD_META_INFO_PATH.read_text(encoding="utf-8").splitlines()
        if len(linhas) >= 1 and linhas[0].strip():
            fonte_dados = linhas[0].strip()
        if len(linhas) >= 2 and linhas[1].strip():
            fonte_metas = linhas[1].strip()

    return vendas_df, metas_df, fonte_dados, fonte_metas


def limpar_upload_persistido() -> None:
    """Remove arquivos persistidos de upload e restaura a base demo."""
    for caminho in [UPLOAD_VENDAS_PATH, UPLOAD_METAS_PATH, UPLOAD_META_INFO_PATH]:
        if caminho.exists():
            caminho.unlink()


def pode_ver_terminal(perfil: str) -> bool:
    return perfil in {"Administrador", "Gestor"}


def pode_ver_config(perfil: str) -> bool:
    return perfil in {"Administrador", "Gestor"}


def visao_perfil(perfil: str) -> str:
    descricoes = {
        "Diretor": "Visão executiva com foco em indicadores e resultado final.",
        "Gestor": "Visão gerencial com análises, exportações e operação do relatório.",
        "Analista": "Visão analítica com exploração de dados e filtros.",
        "Administrador": "Visão completa do sistema, terminal e configurações.",
    }
    return descricoes.get(perfil, "Visão padrão do sistema.")

# ══════════════════════════════════════════
# CARREGAR DADOS
# ══════════════════════════════════════════

try:
    vendas_raw, metas_raw, dolar = carregar_dados()
    vendas_raw = normalizar_datas(vendas_raw)
    metas_raw = metas_raw.copy()
except Exception as e:
    st.error(f"Erro ao carregar dados do SARE: {e}")
    st.stop()

upload_bruto = None
upload_info = None
fonte_dados_label = "Banco SQL (seed/demo)"
fonte_metas_label = "Excel padrão do projeto"

persistido = carregar_upload_persistido()
if persistido is not None:
    vendas_persistidas, metas_persistidas, fonte_dados_persistida, fonte_metas_persistida = persistido
    vendas_raw = normalizar_datas(vendas_persistidas)
    metas_raw = metas_persistidas.copy()
    fonte_dados_label = fonte_dados_persistida
    fonte_metas_label = fonte_metas_persistida

status_fontes = {
    "Banco SQL": DB_PATH.exists(),
    "Excel de metas": not metas_raw.empty,
    "API BCB": bool(dolar and dolar.get("valor")),
    "Output PDF": Path(OUTPUT_DIR).exists(),
}

# ══════════════════════════════════════════
# HEADER — POSICIONAMENTO DO PRODUTO
# ══════════════════════════════════════════

st.markdown(f"""
<div style="background: linear-gradient(135deg, #0b0f19 0%, #131a2b 100%);
    border: 1px solid #1e293b; border-radius: 12px; padding: 30px; margin-bottom: 24px;">
    <h1 style="color: #5ba4d9; margin: 0; font-size: 2rem;">
        🏢 SARE — Sistema de Automação de Relatórios Empresariais
    </h1>
    <p style="color: #94a3b8; margin: 8px 0 16px 0; font-size: 1.1rem;">
        Automação completa: extrai dados de múltiplas fontes, processa, gera PDF profissional
        e envia por email — tudo no horário que a empresa escolher.
    </p>
    <div style="display: flex; gap: 24px; flex-wrap: wrap;">
        <div style="background: #1e293b; padding: 8px 16px; border-radius: 8px;">
            <span style="color: #5ba4d9; font-weight: bold;">📥 Problema</span>
            <span style="color: #e2e8f0;"> — Gestores perdem horas montando relatórios manualmente</span>
        </div>
        <div style="background: #1e293b; padding: 8px 16px; border-radius: 8px;">
            <span style="color: #4ade80; font-weight: bold;">✅ Solução</span>
            <span style="color: #e2e8f0;"> — SARE automatiza extração → análise → PDF → email</span>
        </div>
        <div style="background: #1e293b; padding: 8px 16px; border-radius: 8px;">
            <span style="color: #f59e0b; font-weight: bold;">👥 Perfil</span>
            <span style="color: #e2e8f0;"> — {st.session_state.perfil_usuario}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════

with st.sidebar:
    st.markdown(f"## 🏢 {EMPRESA_NOME}")
    st.caption("Sistema de Automação de Relatórios")

    perfil = st.selectbox(
        "Perfil de visualização",
        ["Diretor", "Gestor", "Analista", "Administrador"],
        index=["Diretor", "Gestor", "Analista", "Administrador"].index(
            st.session_state.perfil_usuario
        ),
        help="Simulação de perfis para demonstrar níveis de acesso no produto.",
    )
    st.session_state.perfil_usuario = perfil
    st.info(visao_perfil(perfil))

    st.divider()
    st.markdown("### 📤 Upload de dados")
    arquivo_upload = st.file_uploader(
        "Enviar arquivo de vendas",
        type=["xlsx", "csv", "txt", "docx"],
        help=(
            "Aceita arquivos .xlsx, .csv, .txt e .docx. "
            "O SARE tenta organizar a estrutura automaticamente antes de atualizar o dashboard."
        ),
        key="upload_vendas",
    )
    arquivo_metas = st.file_uploader(
        "Enviar metas para comparação com o realizado (opcional)",
        type=["xlsx", "csv", "txt", "docx"],
        help=(
            "Envie um arquivo separado de metas para comparar com o realizado. "
            "Se você não enviar, o SARE cria metas demonstrativas com base nos vendedores do upload atual."
        ),
        key="upload_metas",
    )

    if st.button("🧹 Voltar para dados demo", use_container_width=True):
        limpar_upload_persistido()
        st.success("Uploads removidos. O dashboard voltou para a base demo do projeto.")
        st.rerun()

    if arquivo_upload is not None:
        try:
            upload_bruto, vendas_upload, upload_info = preparar_upload_vendas(arquivo_upload)
            vendas_raw = normalizar_datas(vendas_upload)
            fonte_dados_label = f"Upload: {upload_info['nome_arquivo']}"

            data_ref = None
            if not vendas_raw.empty and "data" in vendas_raw.columns:
                datas_validas = vendas_raw["data"].dropna()
                if not datas_validas.empty:
                    data_ref = datas_validas.max()

            metas_info = None
            if arquivo_metas is not None:
                _, metas_upload, metas_info = preparar_upload_metas(arquivo_metas, data_referencia=data_ref)
                metas_raw = metas_upload.copy()
                fonte_metas_label = f"Upload: {metas_info['nome_arquivo']}"
            else:
                metas_raw = construir_metas_demonstrativas(vendas_raw)
                fonte_metas_label = "Metas demonstrativas geradas a partir do upload atual"

            salvar_upload_persistido(vendas_raw, metas_raw, fonte_dados_label, fonte_metas_label)

            st.success(f"Arquivo importado: {upload_info['nome_arquivo']}")
            st.caption(
                f"{upload_info['linhas_organizadas']} registro(s) prontos para análise "
                f"a partir de {upload_info['extensao']}."
            )
            st.caption(f"Fonte atual das metas: {fonte_metas_label}")
            if fonte_metas_label.startswith("Metas demonstrativas"):
                st.warning(
                    "Como nenhum arquivo de metas foi enviado, o SARE gerou metas demonstrativas "
                    "com os vendedores do upload atual para evitar misturar nomes antigos com dados novos."
                )
            st.download_button(
                "📥 Baixar planilha organizada",
                dataframe_para_excel_bytes(vendas_raw),
                file_name=f"vendas_organizadas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Não foi possível importar o arquivo enviado: {e}")

    st.caption(f"Fonte atual dos dados: {fonte_dados_label}")
    st.caption(f"Fonte atual das metas: {fonte_metas_label}")

    st.divider()
    st.markdown("### 🔎 Filtros globais")

    opcoes_periodo = [
        "Últimos 30 dias",
        "Últimos 60 dias",
        "Últimos 90 dias",
        "Mês atual",
        "Trimestre atual",
        "Tudo", 
    ]
    periodo_padrao = (
        st.session_state.cfg_periodo
        if st.session_state.cfg_periodo in opcoes_periodo
        else "Últimos 90 dias"
    )

    periodo_global = st.selectbox(
        "Período",
        opcoes_periodo,
        index=opcoes_periodo.index(periodo_padrao),
    )

    status_opcoes = (
        sorted(vendas_raw["status"].dropna().unique().tolist())
        if "status" in vendas_raw.columns
        else []
    )
    vendedor_opcoes = (
        sorted(vendas_raw["vendedor"].dropna().unique().tolist())
        if "vendedor" in vendas_raw.columns
        else []
    )
    categoria_opcoes = (
        sorted(vendas_raw["categoria"].dropna().unique().tolist())
        if "categoria" in vendas_raw.columns
        else []
    )

    status_global = st.multiselect(
        "Status",
        status_opcoes,
        default=status_opcoes,
    )
    vendedor_global = st.multiselect(
        "Vendedor",
        vendedor_opcoes,
        default=[],
    )
    categoria_global = st.multiselect(
        "Categoria",
        categoria_opcoes,
        default=[],
    )

    st.divider()

    vendas_filtradas = aplicar_filtros_globais(
        vendas_raw,
        periodo_label=periodo_global,
        status_list=status_global,
        vendedores_list=vendedor_global,
        categorias_list=categoria_global,
    )
    dados = processar_dados(vendas_filtradas, metas_raw)
    rv = dados["resumo"]

    st.metric(
        "💵 Dólar",
        f"R$ {dolar['valor']:.2f}",
        help=(
            f"Cotação em {dolar['data']}"
            + (f" • {dolar.get('origem')}" if dolar.get('origem') else "")
        ),
    )
    st.metric("💰 Faturamento", f"R$ {rv['faturamento_total']:,.2f}")
    st.metric("📦 Vendas concluídas", f"{rv['total_vendas']}")
    st.metric("⏳ Pendentes", f"{rv['total_pendentes']}")

    st.divider()
    st.caption("SARE — Desenvolvido por Paulo Lavarini")
    st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ══════════════════════════════════════════
# STATUS OPERACIONAL
# ══════════════════════════════════════════

st.subheader("📡 Status Operacional do Sistema")

col_st1, col_st2, col_st3, col_st4 = st.columns(4)
col_st1.metric("Banco SQL", status_fonte(status_fontes["Banco SQL"]))
col_st2.metric("Excel de metas", status_fonte(status_fontes["Excel de metas"]))
col_st3.metric("API BCB", status_fonte(status_fontes["API BCB"]))
col_st4.metric("Output PDF", status_fonte(status_fontes["Output PDF"]))

col_last1, col_last2, col_last3 = st.columns(3)
col_last1.info(f"**Última execução:** {st.session_state.ultima_execucao['timestamp']}")
col_last2.info(f"**Status atual:** {st.session_state.ultima_execucao['status']}")

proxima_exec = datetime.combine(datetime.today(), st.session_state.cfg_horario)
if proxima_exec < datetime.now():
    proxima_exec += timedelta(days=1 if st.session_state.cfg_intervalo == "Diário" else 7)

col_last3.info(f"**Próxima execução:** {proxima_exec.strftime('%d/%m/%Y %H:%M')}")

st.divider()

# ══════════════════════════════════════════
# AÇÕES RÁPIDAS
# ══════════════════════════════════════════

st.subheader("⚡ Ações rápidas")

acao1, acao2, acao3, acao4 = st.columns(4)

with acao1:
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        registrar_evento("refresh", "Dados atualizados", "Cache limpo e recarga solicitada.")
        st.rerun()

with acao2:
    if st.button("📄 Gerar PDF agora", use_container_width=True):
        try:
            with st.spinner("Gerando relatório PDF..."):
                caminho = gerar_relatorio(
                    resumo=dados["resumo"],
                    top_categorias=dados["categorias"],
                    top_vendedores=dados["vendedores"],
                    top_produtos=dados["produtos"],
                    vendas_mes=dados["mensal"],
                    metas_comparativo=dados["metas_comp"],
                    cotacao_dolar=dolar,
                    comparativo_periodos=dados["comparativo"],
                    insights=dados["insights"],
                )
            registrar_evento("pdf", "Sucesso", f"PDF gerado em {caminho}")
            st.success(f"Relatório gerado com sucesso: {Path(caminho).name}")

            with open(caminho, "rb") as f:
                st.download_button(
                    "📥 Baixar PDF gerado",
                    f.read(),
                    file_name=Path(caminho).name,
                    mime="application/pdf",
                    use_container_width=True,
                )
        except Exception as e:
            registrar_evento("pdf", "Erro", str(e))
            st.error(f"Falha ao gerar PDF: {e}")

with acao3:
    csv_export = vendas_filtradas.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Exportar CSV filtrado",
        csv_export,
        file_name=f"vendas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with acao4:
    if st.button("📊 Ver status rápido", use_container_width=True):
        detalhe = (
            f"Faturamento R$ {rv['faturamento_total']:,.2f} | "
            f"Concluídas {rv['total_vendas']} | "
            f"Pendentes {rv['total_pendentes']}"
        )
        registrar_evento("status", "Consulta rápida", detalhe)
        st.toast("Resumo operacional atualizado.")

st.divider()

# ══════════════════════════════════════════
# ABAS PRINCIPAIS (3 abas)
# ══════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Dashboard", "🖥️ Terminal", "⚙️ Configurações", "🕘 Histórico"]
)


# ══════════════════════════════════════════
# ABA 1: DASHBOARD
# ══════════════════════════════════════════

with tab1:
    st.title("📊 Dashboard de Vendas")
    st.caption(
        f"{EMPRESA_NOME} — visão filtrada por {periodo_global.lower()} | Fonte atual: {fonte_dados_label}"
    )

    with st.expander("ℹ️ Como interpretar este dashboard"):
        st.markdown(
            "**O que o SARE faz:** integra dados, organiza informações e transforma isso em indicadores, gráficos, PDF e alertas gerenciais.\n\n"
            "**Ticket médio:** é o valor médio por venda concluída. Fórmula: faturamento total ÷ quantidade de vendas concluídas.\n\n"
            "**Alertas e insights automáticos:** ficam logo abaixo do resumo executivo e destacam quedas, riscos, pendências e oportunidades detectadas nos dados.\n\n"
            "**Upload inteligente:** ao enviar um arquivo .xlsx, .csv, .txt ou .docx, o SARE tenta organizar a estrutura e recalcula o dashboard automaticamente."
        )

    if upload_info is not None and upload_bruto is not None:
        st.success(f"Dashboard alimentado pelo arquivo: {upload_info['nome_arquivo']}")
        with st.expander("🔍 Prévia do arquivo importado e da versão organizada"):
            prev1, prev2 = st.columns(2)
            with prev1:
                st.markdown("**Arquivo recebido**")
                st.dataframe(upload_bruto.head(10), use_container_width=True, hide_index=True)
            with prev2:
                st.markdown("**Dados organizados pelo SARE**")
                preview_org = vendas_raw.copy()
                if "data" in preview_org.columns:
                    preview_org["data"] = preview_org["data"].dt.strftime("%d/%m/%Y")
                st.dataframe(preview_org.head(10), use_container_width=True, hide_index=True)

    if vendas_filtradas.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Faturamento", f"R$ {rv['faturamento_total']:,.2f}")
        col2.metric("📦 Vendas", f"{rv['total_vendas']}")
        col3.metric("🎫 Ticket Médio", f"R$ {rv['ticket_medio']:,.2f}")
        col4.metric("💵 Dólar", f"R$ {dolar['valor']:.2f}")

        if perfil in {"Diretor", "Gestor"}:
            st.info(
                f"Resumo executivo: {rv['total_vendas']} vendas concluídas, "
                f"faturamento total de R$ {rv['faturamento_total']:,.2f} "
                f"e ticket médio de R$ {rv['ticket_medio']:,.2f}."
            )

        comparativo = dados["comparativo"]
        insights = dados["insights"]

        st.subheader("🧠 Alertas e Insights Automáticos")
        st.caption(
            "Esta seção fica logo abaixo do resumo executivo e mostra automaticamente exceções, riscos e oportunidades encontradas nos dados filtrados."
        )
        ci1, ci2, ci3 = st.columns(3)
        var_fat = comparativo["faturamento"]["variacao_pct"]
        var_ticket = comparativo["ticket_medio"]["variacao_pct"]
        var_pend = comparativo["pendentes"]["variacao_pct"]
        ci1.metric(
            "Faturamento vs período anterior",
            f"R$ {comparativo['faturamento']['atual']:,.2f}",
            delta=(f"{var_fat:+.1f}%" if var_fat is not None else "N/D"),
        )
        ci2.metric(
            "Ticket médio vs período anterior",
            f"R$ {comparativo['ticket_medio']['atual']:,.2f}",
            delta=(f"{var_ticket:+.1f}%" if var_ticket is not None else "N/D"),
        )
        ci3.metric(
            "Pendências vs período anterior",
            f"{int(comparativo['pendentes']['atual'])}",
            delta=(f"{var_pend:+.1f}%" if var_pend is not None else "N/D"),
            delta_color="inverse",
        )
        st.caption(
            f"Comparativo entre {comparativo['periodo_atual_label']} e {comparativo['periodo_anterior_label']}."
        )
        if not insights.empty:
            st.dataframe(insights, use_container_width=True, hide_index=True)
        else:
            st.info("Sem insights automáticos para os filtros selecionados.")

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Vendas por Categoria")
            cat = dados["categorias"]
            if not cat.empty:
                fig_cat = px.pie(
                    cat,
                    values="Faturamento",
                    names="Categoria",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig_cat.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    height=360,
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("Sem dados de categorias para este filtro.")

        with col_right:
            st.subheader("Evolução Mensal")
            mes = dados["mensal"]
            if not mes.empty:
                fig_mes = go.Figure(
                    go.Bar(
                        x=mes["Mês"],
                        y=mes["Faturamento"],
                        marker_color="#5ba4d9",
                        text=mes["Faturamento"].apply(lambda v: f"R$ {v:,.0f}"),
                        textposition="outside",
                    )
                )
                fig_mes.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
                    height=360,
                )
                st.plotly_chart(fig_mes, use_container_width=True)
            else:
                st.info("Sem dados mensais para este filtro.")

        st.divider()

        col_left2, col_right2 = st.columns(2)

        with col_left2:
            st.subheader("Ranking de Vendedores")
            rank = dados["vendedores"]
            if not rank.empty:
                fig_rank = go.Figure(
                    go.Bar(
                        x=rank["Faturamento"],
                        y=rank["Vendedor"],
                        orientation="h",
                        marker_color="#5ba4d9",
                        text=rank["Faturamento"].apply(lambda v: f"R$ {v:,.0f}"),
                        textposition="outside",
                    )
                )
                fig_rank.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    yaxis=dict(autorange="reversed"),
                    height=420,
                )
                st.plotly_chart(fig_rank, use_container_width=True)
            else:
                st.info("Sem dados de vendedores.")

        with col_right2:
            st.subheader("Top Produtos")
            prod = dados["produtos"].head(8)
            if not prod.empty:
                fig_prod = go.Figure(
                    go.Bar(
                        x=prod["Faturamento"],
                        y=prod["Produto"],
                        orientation="h",
                        marker_color="#4ade80",
                        text=prod["Faturamento"].apply(lambda v: f"R$ {v:,.0f}"),
                        textposition="outside",
                    )
                )
                fig_prod.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    yaxis=dict(autorange="reversed"),
                    height=420,
                )
                st.plotly_chart(fig_prod, use_container_width=True)
            else:
                st.info("Sem dados de produtos.")

        if perfil != "Diretor":
            st.divider()
            st.subheader("Metas vs Realizado")
            comp = dados["metas_comp"]
            if not comp.empty:
                st.dataframe(
                    comp.style.format(
                        {
                            "Meta": "R$ {:,.2f}",
                            "Real": "R$ {:,.2f}",
                            "Atingimento (%)": "{:.1f}%",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Sem dados de metas para este filtro.")

        st.divider()
        st.subheader("📋 Tabela de Vendas")

        tabela_exibicao = vendas_filtradas.copy()
        if "data" in tabela_exibicao.columns:
            tabela_exibicao["data"] = tabela_exibicao["data"].dt.strftime("%d/%m/%Y")

        st.dataframe(tabela_exibicao, use_container_width=True, hide_index=True)
        st.caption(f"Exibindo {len(vendas_filtradas)} registros após filtros globais.")


# ══════════════════════════════════════════
# ABA 2: TERMINAL INTERATIVO
# ══════════════════════════════════════════

with tab2:
    if not pode_ver_terminal(perfil):
        st.info("O terminal fica disponível apenas para Gestor e Administrador nesta demonstração.")
    else:
        st.title("🖥️ Terminal SARE")
        st.caption("Simule comandos do SARE como se estivesse no terminal")

        comando = st.selectbox(
            "Selecione um comando:",
            [
                "python app.py --help",
                "python app.py status",
                "python app.py gerar",
                "python app.py agendar --help",
            ],
        )

        if st.button("▶ Executar", type="primary"):
            output = ""

            if comando == "python app.py --help":
                output = """Usage: app.py [OPTIONS] COMMAND [ARGS]...

🏢 SARE — Sistema de Automação de Relatórios Empresariais

Options:
  --help  Show this message and exit.

Commands:
  agendar  ⏰ Agenda relatório automático.
  enviar   📧 Gera relatório e envia por email.
  gerar    📄 Gera relatório PDF.
  status   📊 Mostra resumo rápido no terminal."""

                registrar_evento("terminal", "Sucesso", "Comando de ajuda executado.")

            elif comando == "python app.py status":
                output = f"""

═══════════════════════════════════════════════════════
  🏢 SARE — {EMPRESA_NOME}
═══════════════════════════════════════════════════════

  💰 Faturamento:  R$ {rv['faturamento_total']:>12,.2f}
  📦 Vendas:       {rv['total_vendas']:>6} concluídas
  ⏳ Pendentes:    {rv['total_pendentes']:>6}
  ❌ Canceladas:   {rv['total_canceladas']:>6}
  🎫 Ticket médio: R$ {rv['ticket_medio']:>12,.2f}
  💵 Dólar:        R$ {dolar['valor']:>12.2f}

  🧠 Insight:      {dados['insights'].iloc[0]['Insight'] if not dados['insights'].empty else 'Sem alertas relevantes'}
  🔎 Filtro atual: {periodo_global}
  ⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
═══════════════════════════════════════════════════════
"""
                registrar_evento("terminal", "Sucesso", "Comando status executado.")

            elif comando == "python app.py gerar":
                try:
                    caminho = gerar_relatorio(
                        resumo=dados["resumo"],
                        top_categorias=dados["categorias"],
                        top_vendedores=dados["vendedores"],
                        top_produtos=dados["produtos"],
                        vendas_mes=dados["mensal"],
                        metas_comparativo=dados["metas_comp"],
                        cotacao_dolar=dolar,
                        comparativo_periodos=dados["comparativo"],
                        insights=dados["insights"],
                    )
                    output = f"""📥 Extraindo dados...
🔄 Processando...
📄 Gerando PDF...

✅ Relatório gerado: {caminho}"""
                    registrar_evento("terminal", "Sucesso", f"PDF gerado via terminal: {caminho}")

                    with open(caminho, "rb") as f:
                        st.download_button(
                            "📥 Baixar PDF",
                            f.read(),
                            file_name=Path(caminho).name,
                            mime="application/pdf",
                        )
                except Exception as e:
                    output = f"❌ Erro ao gerar relatório: {e}"
                    registrar_evento("terminal", "Erro", str(e))

            elif comando == "python app.py agendar --help":
                intervalo_cli = "diario" if st.session_state.cfg_intervalo == "Diário" else "semanal"
                output = f"""Usage: app.py agendar [OPTIONS]

⏰ Agenda relatório automático.

Exemplos:
  python app.py agendar                    → Diário às 08:00
  python app.py agendar -h 14:00           → Diário às 14:00
  python app.py agendar -h 18:00           → Diário às 18:00
  python app.py agendar -h 09:00 -i semanal → Segunda às 09:00

Configuração simulada atual:
  python app.py agendar --horario {st.session_state.cfg_horario.strftime('%H:%M')} --intervalo {intervalo_cli}

Options:
  -h, --horario TEXT                Horário (HH:MM). Padrão: 08:00
  -i, --intervalo [diario|semanal]  Frequência. Padrão: diario
  --help                            Show this message and exit."""
                registrar_evento("terminal", "Sucesso", "Ajuda do agendamento executada.")

            st.code(output, language="bash")

        st.divider()
        st.markdown(
            """
**Sobre o Terminal:**
- Simulação interativa do CLI do SARE.
- O comando `gerar` realmente cria o PDF usando os dados filtrados do dashboard.
- Em produção, essa interface seria usada por admin/dev/ops.
"""
        )

# ══════════════════════════════════════════
# ABA 3: CONFIGURAÇÕES
# ══════════════════════════════════════════

with tab3:
    if not pode_ver_config(perfil):
        st.info("A aba de configurações fica disponível apenas para Gestor e Administrador nesta demonstração.")
    else:
        st.title("⚙️ Configurações do SARE")
        st.caption("Configurações locais da demo — salvas na sessão do Streamlit")

        with st.form("form_configuracoes"):
            st.subheader("⏰ Agendamento de Relatórios")
            col_cfg1, col_cfg2 = st.columns(2)

            with col_cfg1:
                horario = st.time_input(
                    "Horário de envio",
                    value=st.session_state.cfg_horario,
                    help="Horário em que o relatório será gerado e enviado automaticamente",
                )

            with col_cfg2:
                intervalo = st.selectbox(
                    "Frequência",
                    ["Diário", "Semanal (Segunda-feira)"],
                    index=0 if st.session_state.cfg_intervalo == "Diário" else 1,
                )

            st.subheader("📧 Configurações de Email")
            col_email1, col_email2 = st.columns(2)

            with col_email1:
                email_remetente = st.text_input(
                    "Email remetente (sistema)",
                    value=st.session_state.cfg_email_remetente,
                    help="Email que aparece como remetente do relatório",
                )

            with col_email2:
                email_destinatario = st.text_input(
                    "Email destinatário (gestor)",
                    value=st.session_state.cfg_email_destinatario,
                    help="Quem recebe o relatório automático",
                )

            st.subheader("📄 Configurações do Relatório")
            col_rel1, col_rel2 = st.columns(2)

            with col_rel1:
                periodo_cfg = st.selectbox(
                    "Período padrão do relatório",
                    [
                        "Últimos 30 dias",
                        "Últimos 60 dias",
                        "Últimos 90 dias",
                        "Mês atual",
                        "Trimestre atual",
                        "Tudo",
                    ],
                    index=[
                        "Últimos 30 dias",
                        "Últimos 60 dias",
                        "Últimos 90 dias",
                        "Mês atual",
                        "Trimestre atual",
                        "Tudo",
                    ].index(
                        st.session_state.cfg_periodo
                        if st.session_state.cfg_periodo
                        in [
                            "Últimos 30 dias",
                            "Últimos 60 dias",
                            "Últimos 90 dias",
                            "Mês atual",
                            "Trimestre atual",
                            "Tudo",
                        ]
                        else "Últimos 90 dias"
                    ),
                )

            with col_rel2:
                formato = st.selectbox(
                    "Formato de saída",
                    ["PDF (ReportLab)", "PDF + Email", "CSV"],
                    index=["PDF (ReportLab)", "PDF + Email", "CSV"].index(
                        st.session_state.cfg_formato
                    ),
                )

            incluir = st.multiselect(
                "Seções do relatório",
                [
                    "Resumo executivo",
                    "Vendas por categoria",
                    "Ranking vendedores",
                    "Top produtos",
                    "Evolução mensal",
                    "Metas vs realizado",
                ],
                default=st.session_state.cfg_secoes,
            )

            salvar_cfg = st.form_submit_button("💾 Salvar configurações", type="primary")

        if salvar_cfg:
            st.session_state.cfg_horario = horario
            st.session_state.cfg_intervalo = intervalo
            st.session_state.cfg_email_remetente = email_remetente
            st.session_state.cfg_email_destinatario = email_destinatario
            st.session_state.cfg_periodo = periodo_cfg
            st.session_state.cfg_formato = formato
            st.session_state.cfg_secoes = incluir

            registrar_evento(
                "config",
                "Configurações salvas",
                f"Agendamento {intervalo} às {horario.strftime('%H:%M')} | Destinatário {email_destinatario}",
            )
            st.success("Configurações salvas com sucesso nesta sessão.")

        intervalo_cli = "diario" if "Diário" in st.session_state.cfg_intervalo else "semanal"

        st.info(
            f"📋 Configuração atual: relatório será gerado **{st.session_state.cfg_intervalo.lower()}** "
            f"às **{st.session_state.cfg_horario.strftime('%H:%M')}** e enviado para "
            f"**{st.session_state.cfg_email_destinatario}**."
        )

        st.markdown(
            f"""
```bash
# Comando equivalente no terminal:
python app.py agendar --horario {st.session_state.cfg_horario.strftime('%H:%M')} --intervalo {intervalo_cli}

"""
)

    st.divider()
    st.subheader("🔧 Informações do Sistema")

    col_sys1, col_sys2, col_sys3 = st.columns(3)

    with col_sys1:
        st.markdown("**Versão**")
        st.code("SARE v1.1.0")

    with col_sys2:
        st.markdown("**Banco de dados**")
        st.code(f"SQLite — {len(vendas_raw)} vendas")

    with col_sys3:
        st.markdown("**Último PDF detectado**")
        st.code(obter_ultima_geracao_pdf())

    st.divider()
st.subheader("🔄 Pipeline do Sistema")

pipeline = """
┌─────────┐   ┌─────────┐   ┌─────────┐
│Banco SQL│   │  Excel  │   │API BCB  │
└────┬────┘   └────┬────┘   └────┬────┘
     └─────────────┼─────────────┘
                   ▼
            ┌─────────────┐
            │   PANDAS    │ ← Processamento
            └──────┬──────┘
      ┌────────────┼────────────┐
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│   PDF    │ │  EMAIL   │ │DASHBOARD │
│ReportLab │ │   SMTP   │ │Streamlit │
└──────────┘ └──────────┘ └──────────┘
"""

st.code(pipeline, language="text")
    
# ══════════════════════════════════════════
# ABA 4: Histórico
# ══════════════════════════════════════════

with tab4:
    st.title("🕘 Histórico de Execuções")
    st.caption("Log visual da sessão atual do dashboard")

    historico = st.session_state.historico_execucoes
    if not historico:
        st.info("Ainda não há eventos registrados nesta sessão.")
    else:
        hist_df = pd.DataFrame(historico)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

        ultimo = st.session_state.ultima_execucao
        st.success(
            f"Último evento: {ultimo['tipo']} | {ultimo['status']} | {ultimo['timestamp']}"
        )


