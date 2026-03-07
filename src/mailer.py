"""
Sistema de envio de email via SMTP (Gmail).

Envia relatório PDF como anexo com corpo HTML estilizado.

Por que usar SMTP e não uma API (SendGrid, Mailgun)?
- SMTP é nativo do Python (smtplib) — zero dependências extras
- Gmail é gratuito para até 500 emails/dia
- Para um sistema de relatórios, SMTP é mais que suficiente
- Se precisar escalar, troca para API sem mudar a interface

Segurança:
- Usa TLS (starttls) para criptografar a conexão
- Senha de app em vez da senha normal (mais seguro)
- Credenciais no .env (nunca no código)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime

from src.config import EMAIL_REMETENTE, EMAIL_SENHA, EMAIL_DESTINATARIO, EMPRESA_NOME


def enviar_relatorio(
    caminho_pdf: str,
    destinatario: str = None,
) -> bool:
    """
    Envia relatório PDF por email.

    Parâmetros:
        caminho_pdf: caminho do arquivo PDF gerado
        destinatario: email do destinatário (opcional, usa .env se não passar)

    Retorna:
        True se enviou com sucesso, False se falhou

    Por que retornar bool em vez de levantar exceção?
    - O email é a ÚLTIMA etapa do pipeline
    - Se falhar, o PDF já foi gerado (não perdeu nada)
    - O programa pode informar "PDF gerado, mas email falhou"
    - Melhor UX do que crashar no final
    """

    # ── Validações ──
    if not EMAIL_REMETENTE or not EMAIL_SENHA:
        print(" Credenciais de email não configuradas no .env")
        print("   Configure EMAIL_REMETENTE e EMAIL_SENHA")
        return False

    if destinatario is None:
        destinatario = EMAIL_DESTINATARIO

    if not destinatario:
        print(" Destinatário não configurado")
        print("   Configure EMAIL_DESTINATARIO no .env ou passe como parâmetro")
        return False

    arquivo = Path(caminho_pdf)
    if not arquivo.exists():
        print(f" PDF não encontrado: {caminho_pdf}")
        return False

    # ── Montar email ──
    agora = datetime.now().strftime("%d/%m/%Y")

    msg = MIMEMultipart()
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = destinatario
    msg["Subject"] = f" Relatório {EMPRESA_NOME} — {agora}"

    # Corpo HTML (visual profissional)
    corpo = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #334155; max-width: 600px;">
        <div style="border-bottom: 3px solid #5ba4d9; padding-bottom: 10px; margin-bottom: 20px;">
            <h2 style="color: #5ba4d9; margin: 0;"> Relatório Empresarial</h2>
        </div>

        <p>Olá,</p>

        <p>Segue em anexo o relatório automático da <b>{EMPRESA_NOME}</b>,
        gerado em <b>{agora}</b>.</p>

        <p>Este relatório contém:</p>
        <ul style="color: #64748b;">
            <li>Resumo de faturamento e métricas</li>
            <li>Ranking de vendedores</li>
            <li>Vendas por categoria e produto</li>
            <li>Evolução mensal</li>
            <li>Comparativo metas vs realizado</li>
        </ul>

        <p style="background: #f1f5f9; padding: 12px; border-radius: 6px; font-size: 13px;">
             Este relatório foi gerado automaticamente pelo <b>SARE</b>
            (Sistema de Automação de Relatórios Empresariais).
        </p>

        <hr style="border: 1px solid #e2e8f0; margin-top: 30px;">
        <p style="font-size: 11px; color: #94a3b8;">
            SARE — Desenvolvido por Paulo Lavarini<br>
            Enviado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        </p>
    </body>
    </html>
    """

    msg.attach(MIMEText(corpo, "html"))

    # ── Anexar PDF ──
    with open(arquivo, "rb") as f:
        pdf = MIMEApplication(f.read(), _subtype="pdf")
        pdf.add_header(
            "Content-Disposition", "attachment",
            filename=arquivo.name,
        )
        msg.attach(pdf)

    # ── Enviar ──
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Ativa criptografia TLS
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.send_message(msg)

        print(f" Email enviado para {destinatario}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(" Erro de autenticação.")
        print("   Verifique a senha de app no .env")
        print("   (Não é a senha normal do Gmail — é a senha de 16 chars)")
        return False

    except smtplib.SMTPRecipientsRefused:
        print(f" Destinatário recusado: {destinatario}")
        print("   Verifique se o email está correto")
        return False

    except smtplib.SMTPException as e:
        print(f" Erro SMTP: {e}")
        return False

    except Exception as e:
        print(f" Erro inesperado ao enviar email: {e}")
        return False