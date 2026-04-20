import re

def validar_rut(rut: str) -> dict:
    rut = re.sub(r'[^0-9kK]', '', str(rut).strip())
    
    if len(rut) < 2:
        return {"valido": False, "rut_limpio": None}

    cuerpo, dv = rut[:-1], rut[-1].upper()

    if not cuerpo.isdigit():
        return {"valido": False, "rut_limpio": None}

    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo > 7:
            multiplo = 2

    resto = 11 - (suma % 11)
    if resto == 11:
        dv_calculado = '0'
    elif resto == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(resto)

    valido = dv == dv_calculado
    rut_formateado = f"{int(cuerpo):,}".replace(",", ".") + "-" + dv if valido else None
    
    return {"valido": valido, "rut_limpio": rut_formateado}