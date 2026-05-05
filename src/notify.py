"""
notify.py
Responsabilidad: construir el email HTML con el resultado del digest
y enviarlo via SMTP usando Gmail.
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# -- Construcción del email --

def build_html_email(result: dict) -> str:
    """
    Construye el cuerpo del email en HTML a partir del resultado
    devuelto por evaluate.evaluate_jobs.

    Args:
        result: Dict con las claves oferta, diagnostico y carta_presentacion.

    Returns:
        String con el HTML completo del email.
    """
    oferta     = result["oferta"]
    diag       = result["diagnostico"]
    carta      = result["carta_presentacion"]
    fecha      = datetime.now().strftime("%d/%m/%Y")
    puntuacion = diag["puntuacion_encaje"]

    # Color del badge según la puntuación de encaje
    if puntuacion >= 70:
        color = "#27ae60"
    elif puntuacion >= 50:
        color = "#e67e22"
    else:
        color = "#e74c3c"

    # Mostramos remoto o ubicación según corresponda
    ubicacion_tag = "Remoto" if oferta.get("remoto") else oferta["ubicacion"]

    puntos_fuertes = "".join(f"<li>{p}</li>" for p in diag["puntos_fuertes"])
    puntos_debiles = "".join(f"<li>{p}</li>" for p in diag["puntos_debiles"])

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: 'Helvetica Neue', Arial, sans-serif;
      background: #f4f6f8;
      margin: 0;
      padding: 20px;
      color: #2c3e50;
    }}
    .container {{
      max-width: 640px;
      margin: 0 auto;
      background: #fff;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    }}
    .header {{
      background: #1a1a2e;
      color: #fff;
      padding: 28px 32px;
    }}
    .header h1 {{
      margin: 0;
      font-size: 22px;
      font-weight: 700;
    }}
    .header p {{
      margin: 6px 0 0;
      font-size: 13px;
      opacity: 0.7;
    }}
    .section {{
      padding: 24px 32px;
      border-bottom: 1px solid #eef0f3;
    }}
    .section:last-child {{
      border-bottom: none;
    }}
    .label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: #7f8c8d;
      margin-bottom: 8px;
    }}
    .job-title {{
      font-size: 20px;
      font-weight: 700;
      color: #1a1a2e;
    }}
    .job-meta {{
      font-size: 14px;
      color: #555;
      margin-top: 6px;
    }}
    .apply-btn {{
      display: inline-block;
      margin-top: 14px;
      padding: 10px 22px;
      background: #2980b9;
      color: #fff;
      border-radius: 6px;
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
    }}
    .score {{
      display: inline-block;
      padding: 6px 18px;
      border-radius: 20px;
      background: {color};
      color: #fff;
      font-size: 20px;
      font-weight: 700;
    }}
    .resumen {{
      margin-top: 12px;
      font-size: 14px;
      line-height: 1.7;
      color: #444;
    }}
    ul {{
      margin: 10px 0;
      padding-left: 18px;
      font-size: 14px;
      line-height: 1.9;
    }}
    .carta {{
      background: #f8f9fa;
      border-left: 4px solid #2980b9;
      padding: 16px 20px;
      font-size: 14px;
      line-height: 1.7;
      white-space: pre-wrap;
      border-radius: 0 6px 6px 0;
    }}
    .footer {{
      background: #f8f9fa;
      padding: 14px 32px;
      font-size: 12px;
      color: #95a5a6;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">

    <div class="header">
      <h1>Job Digest Diario</h1>
      <p>La mejor oferta del dia — {fecha}</p>
    </div>

    <div class="section">
      <div class="label">Oferta seleccionada</div>
      <div class="job-title">{oferta['titulo']}</div>
      <div class="job-meta">
        {oferta['empresa']} &nbsp;|&nbsp; {ubicacion_tag} &nbsp;|&nbsp; {oferta['salario']}
      </div>
      <a href="{oferta['url']}" class="apply-btn">Ver oferta y aplicar</a>
    </div>

    <div class="section">
      <div class="label">Diagnostico de encaje</div>
      <div class="score">{puntuacion}/100</div>
      <p class="resumen">{diag['resumen']}</p>
      <ul>{puntos_fuertes}</ul>
      <ul>{puntos_debiles}</ul>
    </div>

    <div class="section">
      <div class="label">Carta de presentacion</div>
      <div class="carta">{carta}</div>
    </div>

    <div class="footer">
      Generado automaticamente · Claude API + JSearch (RapidAPI) · {fecha}
    </div>

  </div>
</body>
</html>"""


def build_subject(result: dict) -> str:
    """
    Construye el asunto del email con el título, empresa y puntuación.

    Args:
        result: Dict con las claves oferta y diagnostico.

    Returns:
        String con el asunto del email.
    """
    oferta = result["oferta"]
    score  = result["diagnostico"]["puntuacion_encaje"]
    fecha  = datetime.now().strftime("%d/%m")
    return f"Job Digest {fecha} — {oferta['titulo']} @ {oferta['empresa']} ({score}/100)"


# -- Envío --

def send_email(html_body: str, subject: str) -> None:
    """
    Envía el email HTML via SMTP usando Gmail.
    Requiere que GMAIL_USER y GMAIL_APP_PASSWORD estén definidas
    como variables de entorno.

    Args:
        html_body: Contenido HTML del email.
        subject:   Asunto del email.

    Raises:
        smtplib.SMTPException: Si el envío falla.
    """
    gmail_user     = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_user
    msg["To"]      = gmail_user

    msg.attach(MIMEText(html_body, "html"))

    # Puerto 465 con SSL directo, sin STARTTLS
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, gmail_user, msg.as_string())

    print("[INFO] Email enviado correctamente.")