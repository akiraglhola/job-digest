"""
digest.py
Punto de entrada del proyecto. Orquesta el flujo completo:
  1. Busca ofertas en Adzuna
  2. Evalua el encaje con la API de Claude
  3. Envia el resultado por email via Gmail SMTP
"""

from src.search import collect_jobs
from src.evaluate import evaluate_jobs
from src.notify import build_html_email, build_subject, send_email


def main() -> None:
    print("[INFO] Iniciando Job Digest...")

    # buscar ofertas
    jobs = collect_jobs(max_per_term=3)
    if not jobs:
        print("[WARN] No se encontraron ofertas. Abortando.")
        return

    # evaluar con Claude y generar carta de presentacion
    print("[INFO] Evaluando ofertas con Claude...")
    result = evaluate_jobs(jobs)

    # construir y enviar el email
    print("[INFO] Enviando email...")
    html    = build_html_email(result)
    subject = build_subject(result)
    send_email(html, subject)

    oferta = result["oferta"]
    score  = result["diagnostico"]["puntuacion_encaje"]
    print(f"[OK] Digest enviado: {oferta['titulo']} @ {oferta['empresa']} ({score}/100)")


if __name__ == "__main__":
    main()