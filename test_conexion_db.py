#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos
"""
import os
import psycopg
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_conexion():
    """Prueba la conexión a la base de datos"""
    
    print("=== VERIFICANDO VARIABLES DE ENTORNO ===")
    print(f"PGHOST: {os.getenv('PGHOST', 'NO DEFINIDO')}")
    print(f"PGPORT: {os.getenv('PGPORT', 'NO DEFINIDO')}")
    print(f"PGDATABASE: {os.getenv('PGDATABASE', 'NO DEFINIDO')}")
    print(f"PGUSER: {os.getenv('PGUSER', 'NO DEFINIDO')}")
    print(f"PGPASSWORD: {'***' if os.getenv('PGPASSWORD') else 'NO DEFINIDO'}")
    print()
    
    print("=== PROBANDO CONEXION ===")
    try:
        # Intentar conectar usando las variables de entorno
        with psycopg.connect() as conn:
            with conn.cursor() as cur:
                # Probar una consulta simple
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"SUCCESS: Conectado a PostgreSQL")
                print(f"Version: {version}")
                print()
                
                # Probar consulta a la tabla usuarios
                cur.execute("SELECT COUNT(*) FROM usuarios;")
                count = cur.fetchone()[0]
                print(f"SUCCESS: Tabla usuarios encontrada")
                print(f"Total usuarios: {count}")
                print()
                
                # Listar usuarios
                cur.execute("SELECT id, username, nombre_completo, activo FROM usuarios;")
                usuarios = cur.fetchall()
                print("Usuarios en la base de datos:")
                for user in usuarios:
                    print(f"  ID: {user[0]}, Usuario: {user[1]}, Nombre: {user[2]}, Activo: {user[3]}")
                
    except Exception as e:
        print(f"ERROR: No se pudo conectar a la base de datos")
        print(f"Error: {e}")
        print()
        print("POSIBLES SOLUCIONES:")
        print("1. Verificar que PGHOST sea el nombre correcto del servicio de BD en Dokploy")
        print("2. Verificar que PGPASSWORD sea la contraseña correcta")
        print("3. Verificar que PGDATABASE sea el nombre correcto de la base de datos")
        print("4. Verificar que el servicio de BD esté ejecutándose en Dokploy")

if __name__ == "__main__":
    test_conexion()
