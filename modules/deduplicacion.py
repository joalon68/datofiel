from rapidfuzz import fuzz
import pandas as pd

def detectar_duplicados(df: pd.DataFrame, col_rut: str = None, col_nombre: str = None) -> pd.DataFrame:
    """
    Detecta duplicados exactos por RUT y duplicados fuzzy por nombre.
    Agrega columnas: es_duplicado, duplicado_de, tipo_duplicado
    """
    df = df.copy()
    df['es_duplicado']   = False
    df['duplicado_de']   = None
    df['tipo_duplicado'] = None

    # ── 1. Duplicados exactos por RUT ──────────────────────────
    if col_rut and col_rut in df.columns:
        ruts = df[col_rut].astype(str).str.strip().str.lower()
        vistos = {}
        for i, rut in enumerate(ruts):
            if rut in ('none', 'nan', ''):
                continue
            if rut in vistos:
                df.at[i, 'es_duplicado']   = True
                df.at[i, 'duplicado_de']   = vistos[rut]
                df.at[i, 'tipo_duplicado'] = 'RUT exacto'
            else:
                vistos[rut] = i

    # ── 2. Duplicados fuzzy por nombre ─────────────────────────
    if col_nombre and col_nombre in df.columns:
        nombres = df[col_nombre].astype(str).str.strip().tolist()
        for i in range(len(nombres)):
            if df.at[i, 'es_duplicado']:
                continue
            for j in range(i + 1, len(nombres)):
                if df.at[j, 'es_duplicado']:
                    continue
                score = fuzz.token_sort_ratio(nombres[i], nombres[j])
                if score >= 90:
                    df.at[j, 'es_duplicado']   = True
                    df.at[j, 'duplicado_de']   = i
                    df.at[j, 'tipo_duplicado'] = f'Nombre similar ({score}%)'

    return df