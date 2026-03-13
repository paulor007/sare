"""
Extrator de dados de APIs externas.

Consome API pública do Banco Central do Brasil (PTAX).
Retorna cotação do dólar (compra e venda).

Por que ter um fallback?
- A API pode estar fora do ar
- O computador pode estar sem internet
- O sistema não pode parar por causa de um dado complementar
- O fallback garante que o relatório é gerado mesmo assim

Timeout de 10 segundos: se a API não responder em 10s, desiste.
"""

import requests
from datetime import datetime, timedelta

from src.config import BCB_API_URL

def extrair_cotacao_dolar() -> dict:
    """
    Busca cotação atual do dólar (PTAX) na API do Banco Central.

    A API PTAX retorna cotações em formato OData.
    Precisamos montar a URL com a data correta.

    Retorna dict com:
        - data: string "DD/MM/YYYY"
        - valor: float (ex: 5.83)

    Em caso de erro, retorna fallback com valor estimado.
    """
    try:
        # Monta URL com data de hoje (ou ontem se for fim de semana)
        hoje = datetime.now()

        # BCB não tem cotação em fim de semana, tenta últimos 5 dias
        for dias_atras in range(5):
            data = hoje - timedelta(days=dias_atras)
            data_formatada = data.strftime("%m-%d-%Y")

            url = (
                f"{BCB_API_URL}/CotacaoDolarDia(dataCotacao=@dataCotacao)"
                f"?@dataCotacao='{data_formatada}'"
                f"&$top=1&$format=json"
            )

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            dados = response.json()
            valores = dados.get("value", [])

            if valores:
                cotacao = valores[0]
                return {
                    "data": data.strftime("%d/%m/%Y"),
                    "valor": round(cotacao.get("cotacaoCompra", 0), 2),
                    "origem": "BCB/PTAX",
                    "modo": "oficial_diaria",
                }
            
        # Se não achou em 5 dias, retorna fallback
        return _fallback("Sem cotação nos últimos 5 dias")
    
    except requests.Timeout:
        return _fallback("Timeout (API demorou mais de 10s)")
    except requests.ConnectionError:
        return _fallback("Sem conexão com a internet")
    except requests.RequestException as e:
        return _fallback(f"Erro na requisição: {e}")
    except Exception as e:
        return _fallback(f"Erro inesperado: {e}")
    
def _fallback(motivo: str) -> dict:
    """
    Retorna valor padrão quando a API falha.

    Por que não levantar exceção?
    - O dólar é um dado COMPLEMENTAR no relatório
    - Não faz sentido impedir o relatório inteiro por isso
    - Melhor mostrar um valor estimado do que nada
    """
    print(f" Cotação dólar (fallback): {motivo}")
    return {
        "data": datetime.now().strftime("%d/%m/%Y"),
        "valor": 5.26, # Valor estimado (atualizar periodicamente)
    }