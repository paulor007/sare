# SARE — Sistema de Automação de Relatórios Empresariais

> **O problema:** Gestores perdem horas toda semana montando relatórios manualmente — abrindo planilhas, copiando dados, formatando tabelas, enviando por email.
>
> **A solução:** O SARE automatiza o processo inteiro. Extrai dados, processa, gera PDF profissional, envia por email e mostra dashboard com alertas — tudo automaticamente.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?logo=pandas)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)
![Tests](https://img.shields.io/badge/Tests-23%20passing-brightgreen)
![Status](https://img.shields.io/badge/Status-Conclu%C3%ADdo-brightgreen)

---

## Números do projeto

| Métrica             | Valor                        |
| ------------------- | ---------------------------- |
| Linhas de código    | 3.045                        |
| Funções             | 36                           |
| Testes Pytest       | 23 passando                  |
| Módulos             | 12                           |
| Formatos de upload  | 4 (.xlsx, .csv, .txt, .docx) |
| Alertas automáticos | 6 tipos                      |

---

## Quem usa e como

| Usuário               | O que faz                                              | Como acessa      |
| --------------------- | ------------------------------------------------------ | ---------------- |
| **Diretor Comercial** | Recebe relatório automático com alertas de queda       | Email (PDF)      |
| **Gestor de Vendas**  | Consulta dashboard, compara períodos, filtra dados     | Dashboard web    |
| **Analista**          | Upload de planilhas, exporta CSV, gera PDF sob demanda | Dashboard web    |
| **Administrador**     | Configura horários, emails, agenda automação           | CLI ou Dashboard |

---

## O que o sistema entrega

### Extração multi-fonte

- **Banco SQL** — vendas, vendedores, produtos via SQLAlchemy com JOINs
- **Planilha Excel** — metas por vendedor com detecção automática de coluna por mês
- **API pública** — cotação do dólar PTAX em tempo real (Banco Central)

### Processamento + Alertas

- Faturamento, ticket médio, rankings por vendedor/categoria/produto
- **Comparação entre períodos** — mês atual vs anterior com variação %
- **6 alertas automáticos** — queda de faturamento, ticket caindo, aumento de pendências, vendedores abaixo da meta, projeção de meta, categoria em crescimento
- Metas inteligentes — detecta coluna correta (Jan/Fev/Mar) conforme o período

### Upload multiformato (novo!)

- Aceita **.xlsx, .csv, .txt, .docx** (com tabelas)
- **Organização automática** de planilhas bagunçadas: colunas diferentes, delimitadores mistos, números como texto, datas mal formatadas
- Upload de metas separado ou geração de metas demonstrativas
- **Persistência** — dados sobrevivem ao refresh da página
- Download da planilha organizada

### Relatório PDF profissional

- Cabeçalho com empresa, cards de métricas, 5 tabelas zebradas
- **Alertas e insights integrados** no PDF
- Rodapé automático com timestamp

### Email automático

- Gmail SMTP com corpo HTML profissional e PDF anexado
- Horário 100% configurável (`-h 08:00`, `-h 14:00`, `-h 18:00`)

### Dashboard interativo

- Header com posicionamento de produto (problema → solução → quem usa)
- 4 gráficos Plotly interativos
- Painel de alertas e insights automáticos
- Tabela filtrável com export CSV e download PDF
- Aba Terminal (simula CLI, gera PDF de verdade)
- Aba Configurações (agendamento, email, período, pipeline)

---

## Arquitetura

```
                    Upload (.xlsx/.csv/.txt/.docx)
                              │
Banco SQL ──┐                 ▼
Excel ──────┤──> Pandas ──> Alertas ──> PDF ──> Email
API BCB ────┘       │                    │
                    ▼                    ▼
              Dashboard          Agendamento
           (com upload)        (diário/semanal)
```

```
sare/
├── app.py                      ← CLI (Click) com alertas
├── dashboard.py                ← Dashboard completo (1.164 linhas)
├── src/
│   ├── config.py               ← Configurações (.env)
│   ├── database.py             ← Modelos SQLAlchemy (ORM)
│   ├── extractors/
│   │   ├── sql_extractor.py    ← Dados do banco (JOINs)
│   │   ├── excel_extractor.py  ← Dados de planilhas
│   │   └── api_extractor.py    ← API BCB (dólar, fallback)
│   ├── processor.py            ← Motor analítico (658 linhas, 18 funções)
│   ├── upload_processor.py     ← Upload multiformato (616 linhas, 18 funções)
│   ├── report.py               ← PDF com insights
│   ├── mailer.py               ← Email SMTP
│   └── scheduler.py            ← Agendamento + logs
├── data/                       ← Dados demo (SQLite + Excel)
├── output/                     ← PDFs gerados
├── logs/                       ← Logs de execução
└── tests/                      ← 23 testes Pytest
```

---

## Stack Técnica

| Tecnologia         | Para quê         | Por quê                                |
| ------------------ | ---------------- | -------------------------------------- |
| Python 3.12+       | Linguagem        | Mais usada em dados/automação          |
| Pandas             | Análise de dados | Padrão da indústria                    |
| SQLAlchemy         | ORM banco        | Funciona com SQLite, PostgreSQL, MySQL |
| Streamlit + Plotly | Dashboard        | Python puro → app web                  |
| ReportLab          | Geração PDF      | Nativo, controle total                 |
| smtplib            | Email            | Nativo Python                          |
| schedule           | Agendamento      | Simples e eficiente                    |
| Click              | CLI              | Gera --help automático                 |
| python-docx        | Upload DOCX      | Lê tabelas de Word                     |
| Pytest             | Testes           | 23 testes automatizados                |

---

## Desafios técnicos resolvidos

| Desafio                                 | Solução                                     |
| --------------------------------------- | ------------------------------------------- |
| API fora do ar trava sistema            | Fallback: retorna valor estimado            |
| Colunas do banco mudam                  | Programação defensiva: `_has_columns()`     |
| Planilha bagunçada de outro sistema     | Upload processor com organização automática |
| Metas com coluna errada (Jan vs Mensal) | Detecção automática por período             |
| Status com acento quebra filtros        | Padronização + verificação `unique()`       |
| Pytest não encontra `src/`              | `conftest.py` na raiz + `sys.path`          |
| Upload perde dados no refresh           | Persistência em `session_state`             |
| PDF: título separado da tabela          | `keepWithNext=True` no estilo               |

---

## Comandos CLI

```bash
python app.py status                         # Resumo + alertas
python app.py gerar                          # Gera PDF com insights
python app.py enviar                         # Gera + envia email
python app.py enviar -d gestor@empresa.com   # Email específico
python app.py agendar                        # Diário às 08:00
python app.py agendar -h 14:00              # Diário às 14:00
python app.py agendar -h 09:00 -i semanal   # Segunda às 9h
```

---

## Roadmap

- [x] Extração multi-fonte (SQL + Excel + API)
- [x] Processamento Pandas com programação defensiva
- [x] Comparação entre períodos + alertas automáticos
- [x] Upload multiformato (.xlsx, .csv, .txt, .docx)
- [x] Organização automática de planilhas
- [x] PDF profissional com insights
- [x] Email automático (SMTP)
- [x] Dashboard completo (1.164 linhas)
- [x] CLI com Click (4 comandos + alertas)
- [x] 23 testes Pytest
- [ ] Deploy Streamlit Cloud
- [ ] Autenticação + perfis (Admin/Gestor/Analista)
- [ ] API REST com FastAPI
- [ ] Migração PostgreSQL

---

## Código-fonte

Repositório público. Clone e rode localmente:

```bash
git clone https://github.com/paulor007/sare.git
cd sare
pip install -r requirements.txt
python data/seed.py          # Popula banco de dados
python data/seed_metas.py    # Gera planilha de metas
streamlit run dashboard.py   # Abre dashboard
python app.py --help         # Comandos CLI
```

[Portfolio](https://paulolavarini-portfolio.netlify.app) | [GitHub](https://github.com/paulor007)

---

## Autor

**Paulo Lavarini** — Desenvolvedor Python

[![Portfolio](https://img.shields.io/badge/Portfolio-Netlify-00C7B7?logo=netlify)](https://paulolavarini-portfolio.netlify.app)
[![GitHub](https://img.shields.io/badge/GitHub-paulor007-181717?logo=github)](https://github.com/paulor007)
