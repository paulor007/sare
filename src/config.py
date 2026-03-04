"""
Configurações centralizadas do SARE.

Carrega variáveis de ambiente e define constantes.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Carrega .env se existir
load_dotenv()

# ── Diretórios ──
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR =  ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
LOGS_DIR = ROOT_DIR / "logs"

# Garante que as pastas existem
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ── Banco de Dados ──
DB_PATH = DATA_DIR / "sare.db"
DB_URL = f"sqlite:///{DB_PATH}"

# ── Email ──
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "")
EMAIL_SENHA = os.getenv("EMAIL_SENHA", "")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO", "")

# ── Empresa ──
EMPRESA_NOME = os.getenv("EMPRESA_NOME", "TechNova Soluções")
RELATORIO_TITULO = os.getenv("RELATORIO_TITULO", "Relatório Mensal de Vendas")

# ── API Banco Central ──
BCB_API_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"