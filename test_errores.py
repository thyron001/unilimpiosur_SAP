#!/usr/bin/env python3
# test_errores.py
# Script para probar la funcionalidad de pedidos con errores

import sys
from datetime import datetime
from persistencia_postgresql import guardar_pedido

def test_pedido_con_errores():
    """Crea un pedido de prueba con productos que tienen errores"""
    
    # Simular un pedido con algunos productos sin SKU o bodega
    items_con_errores = [
        {
            "desc": "PRODUCTO SIN SKU",
            "sku": None,  # Sin SKU - ERROR
            "bodega": "7",
            "cant": 2,
            "puni": 10.50,
            "ptotal": 21.00
        },
        {
            "desc": "PRODUCTO SIN BODEGA", 
            "sku": "TEST001",
            "bodega": None,  # Sin bodega - ERROR
            "cant": 1,
            "puni": 5.25,
            "ptotal": 5.25
        },
        {
            "desc": "PRODUCTO CORRECTO",
            "sku": "TEST002", 
            "bodega": "7",
            "cant": 3,
            "puni": 15.00,
            "ptotal": 45.00
        },
        {
            "desc": "OTRO PRODUCTO SIN SKU",
            "sku": "",  # SKU vacío - ERROR
            "bodega": "1",
            "cant": 1,
            "puni": 8.75,
            "ptotal": 8.75
        }
    ]
    
    pedido = {
        "fecha": datetime.now(),
        "sucursal": "SUCURSAL DE PRUEBA CON ERRORES"
    }
    
    print("🧪 Creando pedido de prueba con errores...")
    print("Productos:")
    for i, item in enumerate(items_con_errores, 1):
        error_indicators = []
        if not item.get("sku"):
            error_indicators.append("SIN SKU")
        if not item.get("bodega"):
            error_indicators.append("SIN BODEGA")
        
        error_text = f" ❌ ({', '.join(error_indicators)})" if error_indicators else " ✅"
        print(f"  {i}. {item['desc']}{error_text}")
    
    try:
        pedido_id, numero_pedido, estado = guardar_pedido(
            pedido, 
            items_con_errores, 
            cliente_id=1, 
            sucursal_id=1
        )
        
        print(f"\n✅ Pedido creado exitosamente:")
        print(f"   → ID: {pedido_id}")
        print(f"   → Número: {numero_pedido}")
        print(f"   → Estado: {estado}")
        
        if estado == "con_errores":
            print("   → El pedido se asignó correctamente al estado 'con_errores'")
        else:
            print("   → ⚠️  El pedido debería estar en estado 'con_errores'")
            
        return pedido_id
        
    except Exception as e:
        print(f"❌ Error al crear el pedido: {e}")
        return None

if __name__ == "__main__":
    test_pedido_con_errores()
