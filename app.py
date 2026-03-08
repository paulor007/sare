"""
SARE — Sistema de Automação de Relatórios Empresariais

CLI principal. Ponto de entrada do sistema.
O usuário interage com o SARE por aqui.

Imports:
- click: biblioteca que transforma funções em comandos de terminal.
  @click.group() cria o grupo "pai" (como git).
  @cli.command() adiciona subcomandos (como git add, git commit).
  @click.option() adiciona parâmetros (--horario, --destinatario).
  click.echo() é como print() mas funciona melhor com pipes e encoding.

Comandos:
  python app.py status               → Resumo rápido no terminal
  python app.py gerar                → Gera PDF
  python app.py enviar               → Gera PDF + envia email
  python app.py enviar -d email      → Envia para email específico
  python app.py agendar              → Agenda diário às 08:00
  python app.py agendar -h 14:00     → Agenda diário às 14:00
  python app.py agendar -h 18:00 -i semanal  → Toda segunda às 18h
"""

import click
from datetime import datetime

from src.config import EMPRESA_NOME
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
from src.mailer import enviar_relatorio

def _pipeline():
    """
    Pipeline completo: extrair → processar → retornar dados prontos.

    Centraliza toda a lógica num lugar só. Os comandos (gerar, enviar,
    status) chamam _pipeline() e usam os dados retornados.

    Por que uma função separada?
    - Evita repetição: gerar, enviar e status usam os mesmos dados
    - Se adicionar uma nova fonte de dados, muda só aqui
    - Facilita testar: chama _pipeline() e verifica o retorno
    """
    click.echo(" Extraindo dados...")
    vendas = extrair_vendas()
    metas = extrair_metas()
    dolar = extrair_cotacao_dolar()

    click.echo(" Processando...")
    rv = resumo_vendas(vendas)
    cat = vendas_por_categoria(vendas)
    rank = vendas_por_vendedor(vendas)
    prod = vendas_por_produto(vendas)
    mes = vendas_por_mes(vendas)
    comp = comparar_metas(vendas, metas)

    return {
        "resumo": rv,
        "top_categorias": cat,
        "top_vendedores": rank,
        "top_produtos": prod,
        "vendas_mes": mes,
        "metas_comparativo": comp,
        "cotacao_dolar": dolar,
    }


# ══════════════════════════════════════════
# GRUPO CLI (pai de todos os comandos)
# ══════════════════════════════════════════

@click.group()
def cli():
    """SARE — Sistema de Automação de Relatórios Empresariais"""
    pass

# ══════════════════════════════════════════
# COMANDO: STATUS
# ══════════════════════════════════════════

@cli.command()
def status():
    """ Mostra resumo rápido no terminal."""
    click.echo(f"\n{'═' * 55}")
    click.echo(f"   SARE — {EMPRESA_NOME}")
    click.echo(f"{'═' * 55}")

    dados = _pipeline()
    rv = dados["resumo"]
    dolar = dados["cotacao_dolar"]

    click.echo(f"\n   Faturamento:  R$ {rv['faturamento_total']:>12,.2f}")
    click.echo(f"   Vendas:       {rv['total_vendas']:>6} concluídas")
    click.echo(f"   Pendentes:    {rv['total_pendentes']:>6}")
    click.echo(f"   Canceladas:   {rv['total_canceladas']:>6}")
    click.echo(f"   Ticket médio: R$ {rv['ticket_medio']:>12,.2f}")
    click.echo(f"   Dólar:        R$ {dolar['valor']:>12.2f}")

    click.echo(f"\n   {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    click.echo(f"{'═' * 55}\n")

# ══════════════════════════════════════════
# COMANDO: GERAR
# ══════════════════════════════════════════

@cli.command()
def gerar():
    """ Gera relatório PDF."""
    click.echo(f"\n SARE — {EMPRESA_NOME}")
    click.echo("═" * 55)

    dados = _pipeline()

    click.echo(" Gerando PDF...")
    caminho = gerar_relatorio(**dados)

    click.echo(f"\n Relatório gerado: {caminho}")

# ══════════════════════════════════════════
# COMANDO: ENVIAR
# ══════════════════════════════════════════

@cli.command()
@click.option(
    "--destinatario", "-d",
    default=None,
    help="Email do destinatário (usa .env se não passar)",
)
def enviar(destinatario):
    """ Gera relatório e envia por email."""
    click.echo(f"\n SARE — {EMPRESA_NOME}")
    click.echo("═" * 55)

    dados = _pipeline()

    click.echo(" Gerando PDF...")
    caminho = gerar_relatorio(**dados)

    click.echo(" Enviando email...")
    sucesso = enviar_relatorio(caminho, destinatario)

    if sucesso:
        click.echo("\n Relatório gerado e enviado!")
    else:
        click.echo("\n PDF gerado, mas email falhou.")
        click.echo(f"  PDF salvo em: {caminho}")

# ══════════════════════════════════════════
# COMANDO: AGENDAR
# ══════════════════════════════════════════

@cli.command(name="agendar")
@click.option(
    "--horario", "-h",
    default="08:00",
    help="Horário de execução (formato HH:MM). Padrão: 08:00",
)
@click.option(
    "--intervalo", "-i",
    type=click.Choice(["diario", "semanal"]),
    default="diario",
    help="Frequência: diario (todo dia) ou semanal (toda segunda). Padrão: diario",
)
def agendar_comando(horario, intervalo):
    """ Agenda relatório automático.

    \b
    Exemplos:
      python app.py agendar                    → Diário às 08:00
      python app.py agendar -h 14:00           → Diário às 14:00
      python app.py agendar -h 18:00           → Diário às 18:00
      python app.py agendar -h 09:00 -i semanal → Segunda às 09:00
    """
    click.echo(f"\n SARE — {EMPRESA_NOME}")
    click.echo("═" * 55)
    click.echo(f" Agendando: {intervalo} às {horario}")
    click.echo("   Ctrl+C para parar\n")

    from src.scheduler import agendar
    agendar(horario, intervalo)

# ══════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════

if __name__ == "__main__":
    cli()
    