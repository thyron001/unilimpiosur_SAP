#!/usr/bin/env python3
# borrar_pedidos.py
# Script para borrar todos los pedidos de la base de datos

import os
from dotenv import load_dotenv
import psycopg

# Cargar variables de entorno
load_dotenv()

def obtener_conexion():
    """Crea conexión a PostgreSQL usando variables de entorno"""
    return psycopg.connect()

def borrar_todos_los_pedidos():
    """Borra todos los pedidos y sus items de la base de datos"""
    try:
        with obtener_conexion() as conn:
            with conn.cursor() as cur:
                # Primero contar cuántos pedidos hay
                cur.execute("SELECT COUNT(*) FROM pedidos")
                total_pedidos = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM pedido_items")
                total_items = cur.fetchone()[0]
                
                print(f"📊 Estado actual:")
                print(f"   → Pedidos: {total_pedidos}")
                print(f"   → Items: {total_items}")
                
                if total_pedidos == 0:
                    print("✅ No hay pedidos para borrar.")
                    return
                
                # Confirmar antes de borrar
                respuesta = input(f"\n⚠️  ¿Estás seguro de que quieres borrar TODOS los {total_pedidos} pedidos y {total_items} items? (escribe 'SI' para confirmar): ")
                
                if respuesta != 'SI':
                    print("❌ Operación cancelada.")
                    return
                
                print("\n🗑️  Borrando pedidos...")
                
                # Borrar items primero (por las foreign keys)
                cur.execute("DELETE FROM pedido_items")
                items_borrados = cur.rowcount
                
                # Borrar pedidos
                cur.execute("DELETE FROM pedidos")
                pedidos_borrados = cur.rowcount
                
                # Confirmar cambios
                conn.commit()
                
                print(f"✅ Borrado completado:")
                print(f"   → {pedidos_borrados} pedidos borrados")
                print(f"   → {items_borrados} items borrados")
                
    except Exception as e:
        print(f"❌ Error al borrar pedidos: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🗑️  Script para borrar todos los pedidos")
    print("=" * 50)
    borrar_todos_los_pedidos()
