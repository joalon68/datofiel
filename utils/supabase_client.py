import os
import bcrypt
from supabase import create_client
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def registrar_usuario(email: str, password: str) -> dict:
    # Verificar si ya existe
    existing = supabase.table("usuarios").select("id").eq("email", email).execute()
    if existing.data:
        return {"ok": False, "error": "Este email ya está registrado"}
    
    # Hash del password
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    result = supabase.table("usuarios").insert({
        "email": email,
        "password_hash": password_hash,
        "creditos": 50,
        "plan": "free"
    }).execute()
    
    if result.data:
        return {"ok": True, "usuario": result.data[0]}
    return {"ok": False, "error": "Error al registrar"}

def login_usuario(email: str, password: str) -> dict:
    result = supabase.table("usuarios").select("*").eq("email", email).execute()
    
    if not result.data:
        return {"ok": False, "error": "Email no encontrado"}
    
    usuario = result.data[0]
    if not bcrypt.checkpw(password.encode(), usuario["password_hash"].encode()):
        return {"ok": False, "error": "Contraseña incorrecta"}
    
    return {"ok": True, "usuario": usuario}

def obtener_creditos(usuario_id: str) -> int:
    result = supabase.table("usuarios").select("creditos").eq("id", usuario_id).execute()
    return result.data[0]["creditos"] if result.data else 0

def descontar_creditos(usuario_id: str, cantidad: int, herramienta: str, registros: int) -> dict:
    creditos_actuales = obtener_creditos(usuario_id)
    
    if creditos_actuales < cantidad:
        return {"ok": False, "error": f"Créditos insuficientes. Tienes {creditos_actuales} y necesitas {cantidad}"}
    
    # Descontar
    supabase.table("usuarios").update({
        "creditos": creditos_actuales - cantidad
    }).eq("id", usuario_id).execute()
    
    # Registrar transacción
    supabase.table("transacciones").insert({
        "usuario_id": usuario_id,
        "herramienta": herramienta,
        "registros_procesados": registros,
        "creditos_usados": cantidad
    }).execute()
    
    return {"ok": True, "creditos_restantes": creditos_actuales - cantidad}