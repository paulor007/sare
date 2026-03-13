"""
Agendador de tarefas + Sistema de logs.

Imports explicados:
- schedule: biblioteca que agenda tarefas de forma legível
  schedule.every().day.at("08:00") = "todo dia às 8h"
  Muito mais simples que cron jobs ou APScheduler.

- logging: sistema de logs nativo do Python.
  Melhor que print() porque:
  1. Salva em arquivo permanente (print só aparece no terminal)
  2. Tem níveis: INFO, WARNING, ERROR (print é tudo igual)
  3. Mostra data/hora automaticamente
  4. Pode desligar sem apagar código (level=WARNING ignora INFO)

- time: nativo, usado para time.sleep() no loop do agendador.
  O loop verifica a cada 60 segundos se tem tarefa para rodar.
"""

import schedule
import time
import logging
from datetime import datetime

from src.config import LOGS_DIR

def configurar_logs():
    """
    Configura sistema de logging.

    Cria 2 handlers (destinos do log):
    1. FileHandler: salva em arquivo (logs/sare_YYYYMM.log)
    2. StreamHandler: mostra no terminal (para ver em tempo real)

    O arquivo de log é mensal (sare_202603.log) para não ficar gigante.

    Format: "2026-03-07 08:00:01 [INFO] Relatório gerado"
    """
    log_file = LOGS_DIR / f"sare_{datetime.now().strftime('%Y%m')}.log"

    # Limpa handlers anteriores (evita duplicação se chamar 2x)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    logging.basicConfig(
       level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler(),
        ], 
    )

    return logging.getLogger("sare")

def tarefa_gerar_relatorio():
    """
    Tarefa agendada: pipeline completo (extrair → processar → PDF → email).

    Por que importar dentro da função (e não no topo)?
    - Evita importação circular: scheduler importa extractors que importa config...
    - Imports no topo rodam na hora que o módulo é carregado
    - Imports dentro da função rodam só quando a tarefa executa
    - Se algo mudar entre execuções, pega a versão mais recente
    """
    logger = logging.getLogger("sare")

    try:
        logger.info(" Iniciando geração automática de relatório...")

        from src.extractors import extrair_vendas, extrair_metas, extrair_cotacao_dolar
        from src.processor import (
            resumo_vendas, vendas_por_categoria, vendas_por_vendedor,
            vendas_por_produto, vendas_por_mes, comparar_metas,
            comparar_periodos, gerar_alertas_insights,
        )
        from src.report import gerar_relatorio
        from src.mailer import enviar_relatorio

        # ── Extrair ──
        logger.info(" Extraindo dados...")
        vendas = extrair_vendas()
        metas = extrair_metas()
        dolar = extrair_cotacao_dolar()

        # ── Processar ──
        logger.info(" Processando...")
        rv = resumo_vendas(vendas)
        comp = comparar_metas(vendas, metas)
        comparativo = comparar_periodos(vendas)
        insights = gerar_alertas_insights(vendas, metas)

        # ── Gerar PDF ──
        logger.info(" Gerando PDF...")
        caminho = gerar_relatorio(
            resumo=rv,
            top_categorias=vendas_por_categoria(vendas),
            top_vendedores=vendas_por_vendedor(vendas),
            top_produtos=vendas_por_produto(vendas),
            vendas_mes=vendas_por_mes(vendas),
            metas_comparativo=comp,
            comparativo_periodos=comparativo,
            insights=insights,
            cotacao_dolar=dolar,
        )
        logger.info(f" PDF gerado: {caminho}")

        # ── Enviar email ──
        logger.info(" Enviando email...")
        if enviar_relatorio(caminho):
            logger.info(" Relatório gerado e enviado com sucesso!")
        else:
            logger.warning(" PDF gerado, mas email não enviado (verifique .env)")

    except Exception as e:
        logger.error(f" Erro na geração automática: {e}", exc_info=True)

def agendar(horario: str = "08:00", intervalo: str = "diario"):
    """
    Agenda execução automática do pipeline.

    Parâmetros:
        horario: "HH:MM" (ex: "08:00", "14:30")
        intervalo: "diario" ou "semanal" (segunda-feira)

    O loop while True verifica a cada 60 segundos se tem tarefa
    para executar. Ctrl+C para parar.
    """
    logger = configurar_logs()

    if intervalo == "diario":
        schedule.every().day.at(horario).do(tarefa_gerar_relatorio)
        logger.info(f" Agendado: todo dia às {horario}")
    elif intervalo == "semanal":
        schedule.every().monday.at(horario).do(tarefa_gerar_relatorio)
        logger.info(f" Agendado: toda segunda às {horario}")
    else:
        logger.error(f"Intervalo inválido: {intervalo}. Use 'diario' ou 'semanal'.")
        return
    
    logger.info(" Aguardando próxima execução... (Ctrl+C para parar)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60) # Verifica a cada minuto
    except KeyboardInterrupt:
        logger.info(" Agendamento parado pelo usuário.")