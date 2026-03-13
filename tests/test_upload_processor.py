"""
Testes do processador de upload.

Valida leitura de arquivos externos, organização automática
para o formato esperado pelo dashboard do SARE e tratamento
específico de metas vindas do upload.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document

from src.upload_processor import (
    construir_metas_demonstrativas,
    dataframe_para_excel_bytes,
    ler_arquivo_upload,
    organizar_planilha_metas,
    organizar_planilha_vendas,
    preparar_upload_metas,
    preparar_upload_vendas,
)


def test_organizar_planilha_coluna_unica_com_ponto_e_virgula():
    """Deve expandir arquivos que vieram inteiros em uma única coluna."""
    df = pd.DataFrame(
        {
            "coluna_unica": [
                "Data Venda;Nome Vendedor;Departamento;Serviço;Grupo;Qtd;Valor;Situação",
                "04/03/2026;Paulo Lavarini;Comercial;Consultoria TI (8h);Serviço;2;2.862,10;Concluída",
                "03/03/2026;Carol Marques;Empresarial;Automação de Processos;Projeto;4;46.466,40;Concluída",
            ]
        }
    )

    organizado = organizar_planilha_vendas(df)

    assert not organizado.empty
    assert list(organizado.columns) == [
        "id",
        "data",
        "vendedor",
        "setor",
        "produto",
        "categoria",
        "quantidade",
        "valor_total",
        "status",
    ]
    assert organizado.iloc[0]["status"] in {"concluida", "pendente", "cancelada"}


def test_ler_upload_txt_estruturado(tmp_path: Path):
    """Deve ler TXT delimitado e devolver DataFrame bruto."""
    arquivo = tmp_path / "vendas.txt"
    arquivo.write_text(
        "Data Venda;Nome Vendedor;Departamento;Serviço;Grupo;Qtd;Valor;Situação\n"
        "04/03/2026;Paulo Lavarini;Comercial;Consultoria TI (8h);Serviço;2;2.862,10;Concluída\n",
        encoding="utf-8",
    )

    bruto = ler_arquivo_upload(arquivo)

    assert not bruto.empty
    assert "Data Venda" in bruto.columns


def test_ler_upload_docx_com_tabela(tmp_path: Path):
    """Deve extrair tabela de um arquivo Word (.docx)."""
    arquivo = tmp_path / "vendas.docx"
    doc = Document()
    tabela = doc.add_table(rows=3, cols=8)
    headers = [
        "Data Venda",
        "Nome Vendedor",
        "Departamento",
        "Serviço",
        "Grupo",
        "Qtd",
        "Valor",
        "Situação",
    ]
    for idx, header in enumerate(headers):
        tabela.rows[0].cells[idx].text = header
    valores1 = [
        "04/03/2026",
        "Paulo Lavarini",
        "Comercial",
        "Consultoria TI (8h)",
        "Serviço",
        "2",
        "2.862,10",
        "Concluída",
    ]
    valores2 = [
        "03/03/2026",
        "Carol Marques",
        "Empresarial",
        "Automação de Processos",
        "Projeto",
        "4",
        "46.466,40",
        "Pendente",
    ]
    for idx, valor in enumerate(valores1):
        tabela.rows[1].cells[idx].text = valor
    for idx, valor in enumerate(valores2):
        tabela.rows[2].cells[idx].text = valor
    doc.save(arquivo)

    bruto, organizado, info = preparar_upload_vendas(arquivo)

    assert not bruto.empty
    assert not organizado.empty
    assert info["extensao"] == ".docx"
    assert "valor_total" in organizado.columns


def test_organizar_planilha_metas_com_coluna_generica():
    """Deve padronizar metas com nomes de colunas mais simples."""
    df = pd.DataFrame(
        {
            "Consultor": ["Ana Pires", "Bruno Costa"],
            "Meta": ["35.000,00", "42.500,00"],
        }
    )

    metas = organizar_planilha_metas(df)

    assert list(metas.columns) == ["Vendedor", "Meta Mensal (R$)"]
    assert metas.iloc[0]["Vendedor"] == "Ana Pires"
    assert metas.iloc[0]["Meta Mensal (R$)"] == 35000.0


def test_construir_metas_demonstrativas_usa_novos_vendedores_do_upload():
    """Deve gerar metas demonstrativas usando os nomes presentes no upload atual."""
    df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-03-03", "2026-03-04", "2026-03-04"]),
            "vendedor": ["Ana Pires", "Bruno Costa", "Ana Pires"],
            "valor_total": [10000.0, 8000.0, 6000.0],
            "status": ["concluida", "concluida", "pendente"],
        }
    )

    metas = construir_metas_demonstrativas(df)

    assert not metas.empty
    assert set(metas["Vendedor"]) == {"Ana Pires", "Bruno Costa"}
    assert metas.attrs["origem_metas"] == "demonstrativa"
    assert (metas["Meta Mensal (R$)"] > 0).all()


def test_preparar_upload_metas_ler_txt(tmp_path: Path):
    """Deve ler um arquivo de metas separado e devolver versão organizada."""
    arquivo = tmp_path / "metas.txt"
    arquivo.write_text(
        "Consultor|Objetivo Mensal\n"
        "Ana Pires|35.000,00\n"
        "Bruno Costa|42.500,00\n",
        encoding="utf-8",
    )

    bruto, organizado, info = preparar_upload_metas(arquivo)

    assert not bruto.empty
    assert not organizado.empty
    assert info["extensao"] == ".txt"
    assert list(organizado.columns) == ["Vendedor", "Meta Mensal (R$)"]


def test_exportar_excel_organizado_retorna_bytes():
    """Deve gerar bytes de planilha para download no dashboard."""
    df = pd.DataFrame(
        {
            "id": [1],
            "data": [pd.Timestamp("2026-03-04")],
            "vendedor": ["Paulo Lavarini"],
            "setor": ["Comercial"],
            "produto": ["Consultoria TI (8h)"],
            "categoria": ["Serviço"],
            "quantidade": [2],
            "valor_total": [2862.10],
            "status": ["concluida"],
        }
    )

    conteudo = dataframe_para_excel_bytes(df)

    assert isinstance(conteudo, bytes)
    assert len(conteudo) > 100
