import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.app.core.config import settings


def _build_transport():
    smtp = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
    smtp.login(settings.smtp_user, settings.smtp_password)
    return smtp


def send_html(
    to: list[str],
    subject: str,
    html: str,
    pdf_bytes: bytes | None = None,
    pdf_filename: str = "relatorio_qtqd.pdf",
) -> None:
    if not to:
        return

    if pdf_bytes:
        msg = MIMEMultipart("mixed")
        body = MIMEMultipart("alternative")
        body.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(body)

        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(pdf_bytes)
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(attachment)
    else:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(html, "html", "utf-8"))

    msg["Subject"] = subject
    msg["From"]    = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"]      = ", ".join(to)

    with _build_transport() as smtp:
        smtp.sendmail(settings.smtp_user, to, msg.as_string())
