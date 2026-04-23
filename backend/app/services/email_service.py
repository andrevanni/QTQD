import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.app.core.config import settings


def _build_transport():
    smtp = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
    smtp.login(settings.smtp_user, settings.smtp_password)
    return smtp


def send_html(to: list[str], subject: str, html: str) -> None:
    if not to:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"]      = ", ".join(to)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with _build_transport() as smtp:
        smtp.sendmail(settings.smtp_user, to, msg.as_string())
