from difflib import get_close_matches

COMUNAS_CHILE = {
    "santiago", "providencia", "las condes", "vitacura", "lo barnechea",
    "ñuñoa", "la reina", "macul", "peñalolen", "la florida", "puente alto",
    "maipú", "pudahuel", "renca", "quilicura", "cerrillos", "cerro navia",
    "conchalí", "el bosque", "estación central", "huechuraba", "independencia",
    "la cisterna", "la granja", "la pintana", "lo espejo", "lo prado",
    "pedro aguirre cerda", "san joaquín", "san miguel", "san ramón",
    "valparaíso", "viña del mar", "concón", "quilpué", "villa alemana",
    "concepción", "talcahuano", "san pedro de la paz", "hualpén", "chiguayante",
    "antofagasta", "calama", "iquique", "alto hospicio", "la serena", "coquimbo",
    "rancagua", "talca", "chillán", "temuco", "padre las casas", "valdivia",
    "puerto montt", "osorno", "punta arenas", "arica", "copiapó"
}

def validar_comuna(comuna: str) -> dict:
    comuna_lower = str(comuna).lower().strip()

    if comuna_lower in COMUNAS_CHILE:
        return {"valida": True, "comuna_corregida": comuna.title(), "confianza": 1.0}

    sugerencias = get_close_matches(comuna_lower, COMUNAS_CHILE, n=1, cutoff=0.75)

    if sugerencias:
        return {"valida": False, "comuna_corregida": sugerencias[0].title(), "confianza": 0.85}

    return {"valida": False, "comuna_corregida": None, "confianza": 0.0}