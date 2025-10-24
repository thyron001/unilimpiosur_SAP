#!/usr/bin/env python3
"""
Script para crear un usuario administrador en la base de datos
"""
import bcrypt
import psycopg
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def crear_usuario_admin():
    """Crea un usuario administrador con contraseña encriptada"""
    
    # Configuración del usuario
    username = "admin"
    password = "admin123"  # Cambia esta contraseña
    nombre_completo = "Administrador"
    email = "admin@unilimpiosur.com"
    
    # Encriptar contraseña
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    print(f"Usuario: {username}")
    print(f"Contraseña: {password}")
    print(f"Hash generado: {password_hash}")
    
    # Conectar a la base de datos
    try:
        with psycopg.connect() as conn:
            with conn.cursor() as cur:
                # Verificar si el usuario ya existe
                cur.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
                if cur.fetchone():
                    print(f"WARNING: El usuario '{username}' ya existe, actualizando contraseña...")
                    # Actualizar la contraseña del usuario existente
                    cur.execute("""
                        UPDATE usuarios 
                        SET password_hash = %s, nombre_completo = %s, email = %s, activo = %s
                        WHERE username = %s
                        RETURNING id;
                    """, (password_hash, nombre_completo, email, True, username))
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    print(f"SUCCESS: Usuario actualizado con ID: {user_id}")
                    print(f"Puedes iniciar sesion con:")
                    print(f"   Usuario: {username}")
                    print(f"   Contrasena: {password}")
                    return
                
                # Crear el usuario
                cur.execute("""
                    INSERT INTO usuarios (username, password_hash, nombre_completo, email, activo)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (username, password_hash, nombre_completo, email, True))
                
                user_id = cur.fetchone()[0]
                conn.commit()
                
                print(f"SUCCESS: Usuario creado exitosamente con ID: {user_id}")
                print(f"Puedes iniciar sesion con:")
                print(f"   Usuario: {username}")
                print(f"   Contrasena: {password}")
                
    except Exception as e:
        print(f"ERROR: Error al crear usuario: {e}")

if __name__ == "__main__":
    crear_usuario_admin()
