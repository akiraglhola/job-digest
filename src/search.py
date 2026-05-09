"""
search.py
Responsabilidad: buscar ofertas de trabajo en Adzuna API
y devolver una lista normalizada lista para evaluar
"""
 
import os
import requests
 
# -- Config --
 
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/es/search/1"
 
SEARCH_TERMS = [
    "Data Engineer",
    "Data Scientist",
    "Analytics Engineer",
    "ETL Python",
    "Backend Developer Python",
]
 
 
def _get_credentials() -> tuple[str, str]:
    """Devuelve las credenciales de Adzuna desde las variables de entorno."""
    return os.environ["ADZUNA_APP_ID"], os.environ["ADZUNA_APP_KEY"]
 
 
 
# -- Búsqueda --
 
def search_jobs(query: str, results_per_page: int = 10) -> list[dict]:
    """
    Llama a la API de Adzuna con un término de búsqueda y devuelve
    una lista de ofertas normalizadas.
 
    Args:
        query:     Término de búsqueda (ej. "Data Engineer Spain").
        results_per_page: Número de resultados a recuperar.
 
    Returns:
        Lista de dicts con los campos relevantes de cada oferta.
    """
    app_id, app_key = _get_credentials()

    params = {
        "app_id":           app_id,
        "app_key":          app_key,
        "what":            query,
        "results_per_page": results_per_page,
        "content-type":     "application/json",
        "sort_by":          "date", 
    }
    try:
        resp = requests.get(ADZUNA_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        jobs = resp.json().get("results", [])
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
    Extrae y estandariza los campos relevantes de una oferta raw de Adzuna.
    Limita la descripción a 800 caracteres para no inflar el contexto de Claude.
    """
    return {
        "titulo":      job.get("title", "N/A"),
        "empresa":     job.get("company", {}).get("display_name", "N/A"),
        "ubicacion":   job.get("location", {}).get("display_name", "N/A"),
        "remoto":      False, # Adzuna no tiene campo remoto explícito
        "salario":     _format_salary(job),
        "url":         job.get("redirect_url", "N/A"),
        "descripcion": (job.get("description") or "")[:500],
    }
 
 
def _format_salary(job: dict) -> str:
    min_s = job.get("salary_min")
    max_s = job.get("salary_max")
    if min_s and max_s:
        return f"{int(min_s):,}€ - {int(max_s):,}€"
    if min_s:
        return f"Desde {int(min_s):,}€"
    return "No especificado"