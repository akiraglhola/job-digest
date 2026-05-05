"""
search.py
Responsabilidad: buscar ofertas de trabajo en JSearch (RapidAPI)
y devolver una lista normalizada lista para evaluar
"""
 
import os
import requests
 
# -- Config --
 
JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
 
SEARCH_TERMS = [
    "Data Engineer Spain",
    "Data Scientist Spain",
    "Analytics Engineer Spain",
    "ETL Python Spain",
    "Backend Developer Python Spain",
]
 
 
def _get_headers() -> dict:
    return {
        "X-RapidAPI-Key":  os.environ["RAPIDAPI_KEY"],
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
 
 
# -- Búsqueda --
 
def search_jobs(query: str, num_pages: int = 1) -> list[dict]:
    """
    Llama a JSearch con un término de búsqueda y devuelve
    una lista de ofertas normalizadas.
 
    Args:
        query:     Término de búsqueda (ej. "Data Engineer Spain").
        num_pages: Número de páginas a recuperar (10 resultados por página).
 
    Returns:
        Lista de dicts con los campos relevantes de cada oferta.
    """
    params = {
        "query":            query,
        "page":             "1",
        "num_pages":        str(num_pages),
        "date_posted":      "month",
    }
    try:
        resp = requests.get(
            JSEARCH_URL,
            headers=_get_headers(),
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        jobs = resp.json().get("data", [])
        return [_normalize(job) for job in jobs]
 
    except requests.exceptions.Timeout:
        print(f"[WARN] Timeout al buscar '{query}'")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"[WARN] HTTP error al buscar '{query}': {e}")
        return []
    except Exception as e:
        print(f"[WARN] Error inesperado al buscar '{query}': {e}")
        return []
 
 
def collect_jobs(max_per_term: int = 5) -> list[dict]:
    """
    Itera sobre todos los SEARCH_TERMS, elimina duplicados por URL
    y devuelve una lista única de ofertas.
 
    Args:
        max_per_term: Máximo de ofertas a coger por término de búsqueda.
 
    Returns:
        Lista deduplicada de ofertas normalizadas.
    """
    all_jobs: list[dict] = []
    seen_urls: set[str] = set()
 
    for term in SEARCH_TERMS:
        jobs = search_jobs(term)
        for job in jobs[:max_per_term]:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_jobs.append(job)
 
    print(f"[INFO] Ofertas únicas recogidas: {len(all_jobs)}")
    return all_jobs
 
 
# -- Normalización --
 
def _normalize(job: dict) -> dict:
    """
    Extrae y estandariza los campos relevantes de una oferta raw de JSearch.
    Limita la descripción a 800 caracteres para no inflar el contexto de Claude.
    """
    return {
        "titulo":      job.get("job_title", "N/A"),
        "empresa":     job.get("employer_name", "N/A"),
        "ubicacion":   _format_location(job),
        "remoto":      job.get("job_is_remote", False),
        "salario":     _format_salary(job),
        "url":         job.get("job_apply_link") or job.get("job_google_link", "N/A"),
        "descripcion": (job.get("job_description") or "")[:800],
    }
 
 
def _format_location(job: dict) -> str:
    city    = job.get("job_city", "")
    country = job.get("job_country", "")
    return f"{city}, {country}".strip(", ") or "N/A"
 
 
def _format_salary(job: dict) -> str:
    min_s = job.get("job_min_salary")
    max_s = job.get("job_max_salary")
    if min_s and max_s:
        return f"{int(min_s):,}€ – {int(max_s):,}€"
    if min_s:
        return f"Desde {int(min_s):,}€"
    return "No especificado"