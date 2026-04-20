import re

PATRONES_DEPTO = r'(depto?\.?|departamento|of\.?|oficina|casa|block|bl\.?)\s*[\w\-]+'

def parsear_direccion(direccion: str) -> dict:
    direccion = str(direccion).strip()

    depto_match = re.search(PATRONES_DEPTO, direccion, re.IGNORECASE)
    depto = depto_match.group(0) if depto_match else None
    if depto:
        direccion = direccion.replace(depto, '').strip()

    numero_match = re.search(r'\b(\d+)\b', direccion)
    numero = numero_match.group(0) if numero_match else None

    calle = re.sub(r'\b\d+\b', '', direccion).strip().strip(',')

    return {"calle": calle, "numero": numero, "depto_oficina": depto}