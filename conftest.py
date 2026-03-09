"""
Configuração do Pytest.

POR QUE ESSE ARQUIVO EXISTE?
Quando o Pytest roda os testes em tests/, ele não sabe onde fica src/.
O Python procura módulos nas pastas do sys.path, e a raiz do projeto
NÃO está lá por padrão quando o Pytest roda.

O QUE ELE FAZ?
Adiciona a raiz do projeto ao sys.path ANTES de rodar qualquer teste.
Assim, "from src.extractors import ..." funciona normalmente.

QUANDO DÁ ESSE ERRO (ModuleNotFoundError: No module named 'src'):
1. Verifique se conftest.py existe na RAIZ (não dentro de tests/)
2. Verifique se src/__init__.py existe
3. Verifique se está rodando pytest da pasta RAIZ do projeto

OUTROS ERROS COMUNS DO PYTEST:
- "collected 0 items": arquivos de teste não começam com test_
- "fixture not found": conftest.py no lugar errado
- "ImportError": módulo não instalado no venv (pip install)
"""

import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).parent))