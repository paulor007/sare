"""
Cria planilha Excel com metas trimestrais por vendedor.

Rode uma vez:
    python -m data.seed_metas
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.config import DATA_DIR

def seed_metas():
    """Gera planilha de metas."""

    metas = pd.DataFrame({
        "Vendedor": [
            "Paulo Lavarini", "João Lavarini", "Carol Marques", "Helena.Lavarini",
            "Catharina.Lavarini", "Luisa.Lavarini", "Cleiton.Lavarini", "Gisele Lavarini",
            "Josy Lima",
        ],
        "Meta Jan (R$)": [45000, 38000, 52000, 48000, 42000, 55000, 40000, 50000, 50600],
        "Meta Fev (R$)": [48000, 40000, 55000, 50000, 45000, 58000, 43000, 52000, 54000],
        "Meta Mar (R$)": [50000, 42000, 58000, 52000, 48000, 60000, 45000, 55000, 57000],
        "Meta Trimestre (R$)": [143000, 120000, 165000, 150000, 135000, 173000, 128000, 157000, 168000],
    })

    caminho = DATA_DIR / "metas_vendas.xlsx"
    metas.to_excel(str(caminho), index=False, engine="openpyxl")

    print(f"✅ Planilha de metas criada: {caminho}")
    print(f"   {len(metas)} vendedores com metas trimestrais")

if __name__ == "__main__":
    seed_metas()