#!/usr/bin/env python3
"""
Script para verificar un usuario y su contraseña
"""
import bcrypt
import psycopg
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_usuario():
    """Verifica un usuario y su contraseña"""
    
    username = "admin"
    password = "admin123"
    
    try:
        with psycopg.connect() as conn:
            with conn.cursor() as cur:
                # Buscar el usuario
                cur.execute("""
                    SELECT id, username, password_hash, nombre_completo, email, activo
                    FROM usuarios WHERE username = %s
                """, (username,))
                
                row = cur.fetchone()
                if not row:
                    print(f"ERROR: Usuario '{username}' no encontrado")
                    return
                
                user_id, username_db, password_hash, nombre_completo, email, activo = row
                
                print(f"Usuario encontrado:")
                print(f"  ID: {user_id}")
                print(f"  Username: {username_db}")
                print(f"  Nombre: {nombre_completo}")
                print(f"  Email: {email}")
                print(f"  Activo: {activo}")
                
                # Verificar contraseña
                if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    print(f"SUCCESS: La contraseña es correcta")
                else:
                    print(f"ERROR: La contraseña es incorrecta")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verificar_usuario()
