"""
evaluate.py
Responsabilidad: evaluar las ofertas de trabajo con la API de Claude,
seleccionar la mejor según el perfil de la persona candidata y generar
un diagnóstico de encaje y una carta de presentación.
"""

import os
import json
import requests


# -- Perfil de la persona candidata --

def _build_profile() -> str:
    """
    Construye el perfil de la persona candidata a partir
    de las variables de entorno. Esto permite personalizar el digest
    sin modificar el código.
    """
    min_salary = os.environ.get("MIN_SALARY", "30000")
    locations  = os.environ.get("LOCATIONS", "España, remoto")
    roles      = os.environ.get("ROLES", "Data Engineer, Data Scientist, Analytics Engineer")
    tech_stack = os.environ.get("TECH_STACK", "Python, PySpark, ETL, SQL, Kafka, Ruby on Rails, Scikit-learn")

    return f"""
- Roles objetivo: {roles}
- Stack técnico: {tech_stack}
- Ubicación: {locations}
- Salario mínimo: {min_salary}€ brutos anuales
"""


# -- Prompt --

def _build_prompt(jobs: list[dict], profile: str) -> str:
    """
    Construye el prompt que se envía a Claude.
    Usa XML tags para separar claramente las ofertas del perfil,
    que es el formato recomendado por Anthropic para contextos estructurados.
    """
    jobs_text = json.dumps(jobs, ensure_ascii=False, indent=2)

    return f"""
Eres una persona experta en selección de talento técnico. Analiza las siguientes ofertas de trabajo:

<ofertas>
{jobs_text}
</ofertas>

Perfil de la persona candidata:
<perfil>
{profile}
</perfil>

Instrucciones:
1. Elige la oferta que MEJOR encaja con el perfil (prioriza stack técnico, ubicación/remoto y salario).
2. Responde ÚNICAMENTE con un JSON válido con esta estructura exacta (sin texto extra, sin markdown):

{{
  "oferta": {{
    "titulo": "...",
    "empresa": "...",
    "url": "...",
    "salario": "...",
    "ubicacion": "...",
    "remoto": true
  }},
  "diagnostico": {{
    "puntuacion_encaje": 85,
    "puntos_fuertes": ["punto 1", "punto 2", "punto 3"],
    "puntos_debiles": ["punto 1", "punto 2"],
    "resumen": "Párrafo breve explicando por qué esta oferta encaja con el perfil."
  }},
  "carta_presentacion": "Carta de presentación personalizada lista para copiar y pegar. Tono profesional pero cercano. Menciona el stack relevante de la persona candidata que encaja con la oferta. 3-4 párrafos."
}}
"""


# -- Llamada a la API --

def evaluate_jobs(jobs: list[dict]) -> dict:
    """
    Envía las ofertas a Claude para que seleccione la mejor,
    genere un diagnóstico de encaje y una carta de presentación.

    Args:
        jobs: Lista de ofertas normalizadas (output de search.collect_jobs).

    Returns:
        Dict con las claves: oferta, diagnostico, carta_presentacion.

    Raises:
        ValueError: Si la respuesta de Claude no es un JSON válido.
        requests.HTTPError: Si la llamada a la API falla.
    """
    profile = _build_profile()
    prompt  = _build_prompt(jobs, profile)

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key":         os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
        },
        json={
            "model":      "claude-sonnet-4-5",
            "max_tokens": 2000,
            "messages":   [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )

    # Muestra el error completo antes de lanzar la excepción
    if not response.ok:
        print(f"[ERROR] Status: {response.status_code}")
        print(f"[ERROR] Respuesta: {response.text}")
    response.raise_for_status()

    raw = response.json()["content"][0]["text"].strip()
    return _parse_response(raw)


# -- Parseo de la respuesta --

def _parse_response(raw: str) -> dict:
    """
    Limpia la respuesta de Claude y la parsea como JSON.
    Claude a veces añade backticks aunque se le pida que no lo haga,
    por lo que los eliminamos antes de parsear.
    """
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        raise ValueError(
            f"La respuesta de Claude no es un JSON válido: {e}\nRespuesta raw:\n{raw}"
        )