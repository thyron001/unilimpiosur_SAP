#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extraer campos específicos de pedidos de WooCommerce
Sistema UnilimpioSur SAP
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from woocommerce import API

def cargar_configuracion():
    """Carga las variables de entorno desde .env"""
    load_dotenv()
    
    url = os.getenv("WOOCOMMERCE_URL")
    consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
    consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")
    
    if not all([url, consumer_key, consumer_secret]):
        print("❌ Error: Faltan variables de entorno de WooCommerce")
        return None, None, None
    
    return url, consumer_key, consumer_secret

def crear_cliente_woocommerce(url, consumer_key, consumer_secret):
    """Crea el cliente de WooCommerce"""
    try:
        wcapi = API(
            url=url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3"
        )
        return wcapi
    except Exception as e:
        print(f"❌ Error al crear cliente WooCommerce: {e}")
        return None

def extraer_campos_pedido(orden):
    """Extrae los campos específicos de un pedido"""
    billing = orden.get('billing', {})
    
    # Extraer información básica del pedido
    datos_pedido = {
        'numero_orden': orden.get('number', ''),
        'fecha_creacion': orden.get('date_created', ''),
        'billing_first_name': billing.get('first_name', ''),
        'billing_company': billing.get('company', ''),
        'billing_address_1': billing.get('address_1', ''),
        'billing_address_2': billing.get('address_2', ''),
        'billing_phone': billing.get('phone', ''),
        'productos': []
    }
    
    # Extraer productos (SKU y cantidad)
    line_items = orden.get('line_items', [])
    for item in line_items:
        producto = {
            'sku': item.get('sku', ''),
            'cantidad': item.get('quantity', 0),
            'nombre': item.get('name', ''),
            'precio': item.get('price', 0)
        }
        datos_pedido['productos'].append(producto)
    
    return datos_pedido

def formatear_fecha(fecha_iso):
    """Formatea la fecha ISO a formato legible"""
    if not fecha_iso:
        return "N/A"
    try:
        fecha = datetime.fromisoformat(fecha_iso.replace('Z', '+00:00'))
        return fecha.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return fecha_iso

def mostrar_pedido_formateado(datos_pedido, numero_pedido=None):
    """Muestra un pedido con formato legible"""
    if numero_pedido:
        print(f"\n📋 PEDIDO #{numero_pedido}")
    else:
        print(f"\n📋 PEDIDO #{datos_pedido['numero_orden']}")
    
    print("=" * 50)
    
    print(f"🆔 Número de Orden: {datos_pedido['numero_orden']}")
    print(f"📅 Fecha de Creación: {formatear_fecha(datos_pedido['fecha_creacion'])}")
    
    print(f"\n👤 INFORMACIÓN DEL CLIENTE:")
    print(f"   Nombre: {datos_pedido['billing_first_name']}")
    print(f"   Empresa: {datos_pedido['billing_company']}")
    print(f"   Teléfono: {datos_pedido['billing_phone']}")
    print(f"   Dirección 1: {datos_pedido['billing_address_1']}")
    print(f"   Dirección 2: {datos_pedido['billing_address_2']}")
    
    print(f"\n📦 PRODUCTOS:")
    if datos_pedido['productos']:
        for i, producto in enumerate(datos_pedido['productos'], 1):
            print(f"   {i}. SKU: {producto['sku']} | Cantidad: {producto['cantidad']} | {producto['nombre']}")
    else:
        print("   Sin productos")

def obtener_pedidos_especificos(wcapi, limite=10, estado=None):
    """Obtiene pedidos con los campos específicos solicitados"""
    print(f"🔍 Obteniendo {limite} pedidos de WooCommerce...")
    
    params = {
        "per_page": limite,
        "page": 1,
        "orderby": "date",
        "order": "desc"
    }
    
    if estado:
        params["status"] = estado
    
    try:
        response = wcapi.get("orders", params=params)
        if response.status_code == 200:
            ordenes = response.json()
            print(f"✅ Se obtuvieron {len(ordenes)} pedidos")
            
            pedidos_procesados = []
            
            for orden in ordenes:
                datos_pedido = extraer_campos_pedido(orden)
                pedidos_procesados.append(datos_pedido)
                mostrar_pedido_formateado(datos_pedido)
            
            return pedidos_procesados
        else:
            print(f"❌ Error al obtener pedidos: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def obtener_pedido_por_id(wcapi, orden_id):
    """Obtiene un pedido específico por ID"""
    print(f"🔍 Obteniendo pedido #{orden_id}...")
    
    try:
        response = wcapi.get(f"orders/{orden_id}")
        if response.status_code == 200:
            orden = response.json()
            datos_pedido = extraer_campos_pedido(orden)
            mostrar_pedido_formateado(datos_pedido)
            return datos_pedido
        else:
            print(f"❌ Error al obtener pedido: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def exportar_a_csv(pedidos, nombre_archivo="pedidos_woocommerce.csv"):
    """Exporta los pedidos a un archivo CSV"""
    import csv
    
    print(f"\n💾 Exportando {len(pedidos)} pedidos a {nombre_archivo}...")
    
    with open(nombre_archivo, 'w', newline='', encoding='utf-8') as archivo:
        writer = csv.writer(archivo)
        
        # Escribir encabezados
        writer.writerow([
            'numero_orden', 'fecha_creacion', 'billing_first_name', 'billing_company',
            'billing_address_1', 'billing_address_2', 'billing_phone',
            'sku', 'cantidad', 'nombre_producto', 'precio'
        ])
        
        # Escribir datos
        for pedido in pedidos:
            # Si no hay productos, escribir una fila con datos básicos
            if not pedido['productos']:
                writer.writerow([
                    pedido['numero_orden'],
                    formatear_fecha(pedido['fecha_creacion']),
                    pedido['billing_first_name'],
                    pedido['billing_company'],
                    pedido['billing_address_1'],
                    pedido['billing_address_2'],
                    pedido['billing_phone'],
                    '', '', '', ''
                ])
            else:
                # Escribir una fila por cada producto
                for producto in pedido['productos']:
                    writer.writerow([
                        pedido['numero_orden'],
                        formatear_fecha(pedido['fecha_creacion']),
                        pedido['billing_first_name'],
                        pedido['billing_company'],
                        pedido['billing_address_1'],
                        pedido['billing_address_2'],
                        pedido['billing_phone'],
                        producto['sku'],
                        producto['cantidad'],
                        producto['nombre'],
                        producto['precio']
                    ])
    
    print(f"✅ Archivo {nombre_archivo} creado exitosamente")

def main():
    """Función principal"""
    print("=" * 60)
    print("🛒 EXTRACTOR DE PEDIDOS WOOCOMMERCE - UNILIMPIOSUR SAP")
    print("=" * 60)
    print("Campos extraídos:")
    print("  - billing_first_name")
    print("  - billing_company") 
    print("  - billing_address_1")
    print("  - billing_address_2")
    print("  - billing_phone")
    print("  - SKU, cantidad")
    print("  - numero de orden")
    print("  - fecha de creacion")
    print("=" * 60)
    
    # Cargar configuración
    url, consumer_key, consumer_secret = cargar_configuracion()
    if not url:
        return
    
    # Crear cliente
    wcapi = crear_cliente_woocommerce(url, consumer_key, consumer_secret)
    if not wcapi:
        return
    
    # Menú de opciones
    while True:
        print(f"\n📋 OPCIONES:")
        print("1. Obtener últimos 10 pedidos")
        print("2. Obtener pedidos por estado (generado)")
        print("3. Obtener pedido específico por ID")
        print("4. Exportar pedidos a CSV")
        print("5. Salir")
        
        opcion = input("\nSelecciona una opción (1-5): ").strip()
        
        if opcion == "1":
            pedidos = obtener_pedidos_especificos(wcapi, limite=10)
            
        elif opcion == "2":
            pedidos = obtener_pedidos_especificos(wcapi, limite=20, estado="generado")
            
        elif opcion == "3":
            orden_id = input("Ingresa el ID de la orden: ").strip()
            if orden_id.isdigit():
                pedido = obtener_pedido_por_id(wcapi, int(orden_id))
                if pedido:
                    pedidos = [pedido]
                else:
                    pedidos = []
            else:
                print("❌ ID inválido")
                pedidos = []
                
        elif opcion == "4":
            if 'pedidos' in locals() and pedidos:
                exportar_a_csv(pedidos)
            else:
                print("❌ Primero debes obtener pedidos (opción 1, 2 o 3)")
                
        elif opcion == "5":
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
