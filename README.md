# SARE — Sistema de Automação de Relatórios Empresariais

> **O problema:** Gestores perdem horas toda semana montando relatórios manualmente — abrindo planilhas, copiando dados, formatando tabelas, enviando por email. É repetitivo, lento e sujeito a erros.
>
> **A solução:** O SARE automatiza o processo inteiro. Extrai dados de onde estiverem, processa, gera um PDF profissional e envia por email — tudo automaticamente, no horário que a empresa escolher.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?logo=pandas)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red)
![ReportLab](https://img.shields.io/badge/ReportLab-PDF-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)

---

## Quem usa e como

| Usuário               | O que faz                                       | Como acessa         |
| --------------------- | ----------------------------------------------- | ------------------- |
| **Diretor Comercial** | Recebe relatório automático toda segunda às 8h  | Email (PDF anexado) |
| **Gestor de Vendas**  | Consulta dashboard, filtra por vendedor/período | Dashboard web       |
| **Administrador**     | Configura horários, emails, gera sob demanda    | CLI ou Dashboard    |

---

## Screenshots

### Dashboard com métricas e gráficos

_(cards de faturamento, vendas, ticket médio + gráficos interativos)_

### Terminal CLI

```
═══════════════════════════════════════════════════════
  SARE — TechNova Soluções
═══════════════════════════════════════════════════════

  Faturamento:  R$ 6,508,570.37
  Vendas:          345 concluídas
  Pendentes:       112
  Ticket médio: R$    18,865.42
  Dólar:        R$         5.29
═══════════════════════════════════════════════════════
```

### Relatório PDF gerado automaticamente

_(cabeçalho com empresa, cards de métricas, tabelas zebradas, rodapé)_

---

## O que o sistema entrega

### Extração multi-fonte

- **Banco SQL** — vendas, vendedores, produtos via SQLAlchemy com JOINs
- **Planilha Excel** — metas por vendedor (importação automática)
- **API pública** — cotação do dólar em tempo real (Banco Central)

### Processamento inteligente

- Faturamento, ticket médio, rankings por vendedor/categoria/produto
- Comparativo metas vs realizado com % de atingimento
- Evolução mensal, filtros por status e período

### Relatório PDF profissional

- Cabeçalho com empresa e data de geração
- Cards de métricas (faturamento, vendas, ticket, dólar)
- 5 tabelas formatadas com zebra e cabeçalho estilizado
- Rodapé automático com timestamp

### Envio automático por email

- Gmail SMTP com corpo HTML profissional
- PDF anexado automaticamente
- Horário 100% configurável pela empresa

### Dashboard interativo

- 4 gráficos Plotly (categorias, mensal, vendedores, produtos)
- Tabela filtrável por status e vendedor
- Export CSV e download de PDF
- Terminal simulado para demonstração

### Agendamento

- Diário ou semanal (ex: toda segunda às 8h, todo dia às 18h)
- Sistema de logs com registro de cada execução
- 13 testes automatizados com Pytest

---

## Arquitetura

```
┌──────────────────────────────────────────────────┐
│                    FONTES DE DADOS                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Banco SQL│  │  Excel   │  │ API Banco    │   │
│  │(SQLAlchemy│  │(Openpyxl)│  │ Central(PTAX)│   │
│  └─────┬────┘  └────┬─────┘  └──────┬───────┘   │
│        └─────────────┼───────────────┘           │
│                      ▼                           │
│              ┌───────────────┐                   │
│              │    PANDAS     │                   │
│              │ (Processador) │                   │
│              └───────┬───────┘                   │
│         ┌────────────┼────────────┐              │
│         ▼            ▼            ▼              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │   PDF    │ │  EMAIL   │ │DASHBOARD │         │
│  │(ReportLab│ │  (SMTP)  │ │(Streamlit│         │
│  └──────────┘ └──────────┘ └──────────┘         │
│                      ▲                           │
│              ┌───────────────┐                   │
│              │  AGENDADOR    │                   │
│              │  (Schedule)   │                   │
│              └───────────────┘                   │
└──────────────────────────────────────────────────┘
```

```
sare/
├── app.py                    ← CLI principal (Click)
├── dashboard.py              ← Dashboard Streamlit
├── src/
│   ├── config.py             ← Configurações centralizadas (.env)
│   ├── database.py           ← Modelos SQLAlchemy (ORM)
│   ├── extractors/
│   │   ├── sql_extractor.py  ← Dados do banco (JOINs)
│   │   ├── excel_extractor.py← Dados de planilhas
│   │   └── api_extractor.py  ← API BCB (dólar, com fallback)
│   ├── processor.py          ← Motor de análise Pandas
│   ├── report.py             ← Gerador PDF (ReportLab)
│   ├── mailer.py             ← Envio email (Gmail SMTP)
│   └── scheduler.py          ← Agendamento + logs
├── data/                     ← Dados demo (SQLite + Excel)
├── output/                   ← PDFs gerados
├── logs/                     ← Logs de execução
└── tests/                    ← 13 testes Pytest
```

---

## Stack Técnica

| Tecnologia         | Para quê    | Por que essa                                     |
| ------------------ | ----------- | ------------------------------------------------ |
| Python 3.12+       | Linguagem   | Mais usada em dados/automação                    |
| Pandas             | Análise     | Padrão da indústria para dados tabulares         |
| SQLAlchemy         | ORM         | Funciona com SQLite, PostgreSQL, MySQL           |
| ReportLab          | PDF         | Nativo, controle total, sem navegador            |
| smtplib            | Email       | Nativo do Python, zero dependências              |
| schedule           | Agendamento | Simples e eficiente                              |
| Click              | CLI         | Gera --help automático                           |
| Streamlit + Plotly | Dashboard   | Python puro vira app web                         |
| Pytest             | Testes      | 13 testes cobrindo extratores, processador e PDF |

---

## Como executar localmente

```bash
# Clone o projeto
git clone <SEU_REPOSITORIO>
cd sare

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual (Windows)
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Popule os dados demo
python data/seed.py
python data/seed_metas.py

# Rode o dashboard
streamlit run dashboard.py
```

## Comandos CLI

```bash
python app.py status                          # Resumo no terminal
python app.py gerar                           # Gera PDF
python app.py enviar                          # Gera + envia email
python app.py enviar -d gestor@empresa.com    # Email específico
python app.py agendar                         # Diário às 08:00
python app.py agendar -h 14:00               # Diário às 14:00
python app.py agendar -h 09:00 -i semanal    # Toda segunda às 9h
```

---

## Cenário Demo

Empresa fictícia **TechNova Soluções** com dados realistas:

- 9 vendedores em 2 departamentos
- 12 produtos em 4 categorias (Software, Serviço, Infraestrutura, Projeto)
- 500+ vendas em 3 meses (concluída, pendente, cancelada)
- Metas mensais e trimestrais por vendedor
- Cotação do dólar em tempo real via API do Banco Central

---

## Funcionalidades implementadas

- [x] Extração de dados de banco SQL

- [x] Importação de metas por Excel

- [x] Consumo de API pública

- [x] Processamento com Pandas

- [x] Geração de PDF profissional

- [x] Envio automático por e-mail

- [x] CLI com Click

- [x] Agendamento diário e semanal

- [x] Dashboard interativo com filtros

- [x] Exportação CSV

- [x] Histórico de execução

- [x] 13 testes automatizados

## Desafios técnicos resolvidos

| Desafio                                   | Solução                                                        |
| ----------------------------------------- | -------------------------------------------------------------- |
| API fora do ar não pode travar o sistema  | Padrão fallback: retorna valor estimado se API falhar          |
| Colunas do banco podem mudar              | Programação defensiva: `_has_columns()` verifica antes de usar |
| Status com acento quebra filtros          | Padronização sem acento + verificação `df['status'].unique()`  |
| Pytest não encontra `src/`                | `conftest.py` na raiz adicionando ao `sys.path`                |
| PDF: título e tabela separados em páginas | `keepWithNext=True` no estilo da seção                         |
| Valores grandes quebram layout dos cards  | Fonte ajustada + largura responsiva                            |

---

## Código-fonte

O código completo está em repositório privado.
Acesso pode ser concedido para avaliação técnica.

**Contato:** [Portfolio](https://paulolavarini-portfolio.netlify.app) | [GitHub](https://github.com/paulor007)

---

## Roadmap

- [x] Extração multi-fonte (SQL + Excel + API)
- [x] Processamento Pandas com programação defensiva
- [x] PDF profissional (ReportLab)
- [x] Email automático (SMTP Gmail)
- [x] CLI com Click (4 comandos)
- [x] Agendamento + Logs
- [x] Dashboard Streamlit + Terminal interativo
- [x] 13 testes Pytest
- [ ] Deploy do dashboard em Streamlit Cloud
- [ ] Login real com autenticação e controle de acesso
- [ ] CRUD completo de vendedores e produtos pela interface
- [ ] Migração do banco SQLite para PostgreSQL
- [ ] Criação de API REST com FastAPI

---

## Autor

**Paulo Lavarini** — Desenvolvedor Python

[![Portfolio](https://img.shields.io/badge/Portfolio-Netlify-00C7B7?logo=netlify)](https://paulolavarini-portfolio.netlify.app)
[![GitHub](https://img.shields.io/badge/GitHub-paulor007-181717?logo=github)](https://github.com/paulor007)
