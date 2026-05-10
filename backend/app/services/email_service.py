import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.app.core.config import settings

try:
    import resend as resend_lib
    resend_lib.api_key = settings.resend_api_key
    _HAS_RESEND = bool(settings.resend_api_key)
except ImportError:
    _HAS_RESEND = False


def _send_via_resend(to: list[str], subject: str, html: str) -> None:
    resend_lib.Emails.send({
        "from": f"{settings.smtp_from_name} <{settings.smtp_user}>",
        "to": to,
        "subject": subject,
        "html": html,
    })


def _send_via_smtp(to: list[str], subject: str, html: str, pdf_bytes: bytes | None = None, pdf_filename: str = "relatorio_qtqd.pdf") -> None:
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

    ctx = ssl.create_default_context()
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ctx) as smtp:
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_user, to, msg.as_string())
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ctx)
            smtp.ehlo()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_user, to, msg.as_string())


def send_html(
    to: list[str],
    subject: str,
    html: str,
    pdf_bytes: bytes | None = None,
    pdf_filename: str = "relatorio_qtqd.pdf",
) -> None:
    if not to:
        return

    if _HAS_RESEND and not pdf_bytes:
        try:
            _send_via_resend(to, subject, html)
            return
        except Exception:
            pass

    _send_via_smtp(to, subject, html, pdf_bytes, pdf_filename)
