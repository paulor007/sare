"""
SARE — Sistema de Automação de Relatórios Empresariais
CLI principal.
"""

import click
from src.config import EMPRESA_NOME, OUTPUT_DIR

@click.group()
def cli():
    """SARE — Sistema de Automação de Relatórios Empresariais"""
    pass

@cli.command()
def status():
    """Mostra o status do sistema."""
    click.echo(f"{'=' * 50}")
    click.echo(f"  SARE — {EMPRESA_NOME}")
    click.echo(f"{'=' * 50}")
    click.echo(f"  Pasta de saída: {OUTPUT_DIR}")
    click.echo("  Status: Operacional")
    click.echo(f"{'=' * 50}")

if __name__ == "__main__":
    cli()