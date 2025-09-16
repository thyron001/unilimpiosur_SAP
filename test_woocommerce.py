#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la conexión con WooCommerce desde terminal
Sistema UnilimpioSur SAP
"""

import os
import sys
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
        print("Verifica que el archivo .env contenga:")
        print("  - WOOCOMMERCE_URL")
        print("  - WOOCOMMERCE_CONSUMER_KEY")
        print("  - WOOCOMMERCE_CONSUMER_SECRET")
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

def probar_conexion(wcapi):
    """Prueba la conexión con WooCommerce"""
    print("🔌 Probando conexión con WooCommerce...")
    
    try:
        response = wcapi.get("system_status")
        if response.status_code == 200:
            print("✅ Conexión exitosa con WooCommerce!")
            data = response.json()
            print(f"   📊 Versión WooCommerce: {data.get('environment', {}).get('version', 'N/A')}")
            print(f"   🌐 URL: {data.get('settings', {}).get('url', 'N/A')}")
            return True
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def obtener_productos(wcapi, limite=5):
    """Obtiene productos de WooCommerce"""
    print(f"\n📦 Obteniendo {limite} productos de WooCommerce...")
    
    try:
        response = wcapi.get("products", params={"per_page": limite, "page": 1})
        if response.status_code == 200:
            productos = response.json()
            print(f"✅ Se obtuvieron {len(productos)} productos:")
            
            for i, producto in enumerate(productos, 1):
                print(f"\n   {i}. {producto.get('name', 'Sin nombre')}")
                print(f"      ID: {producto.get('id')}")
                print(f"      SKU: {producto.get('sku', 'Sin SKU')}")
                print(f"      Precio: ${producto.get('price', '0.00')}")
                print(f"      Stock: {producto.get('stock_quantity', 'N/A')}")
                print(f"      Estado: {producto.get('status', 'N/A')}")
            
            return productos
        else:
            print(f"❌ Error al obtener productos: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def obtener_ordenes(wcapi, limite=3):
    """Obtiene órdenes de WooCommerce"""
    print(f"\n📋 Obteniendo {limite} órdenes de WooCommerce...")
    
    try:
        response = wcapi.get("orders", params={"per_page": limite, "page": 1})
        if response.status_code == 200:
            ordenes = response.json()
            print(f"✅ Se obtuvieron {len(ordenes)} órdenes:")
            
            for i, orden in enumerate(ordenes, 1):
                billing = orden.get('billing', {})
                print(f"\n   {i}. Orden #{orden.get('id')}")
                print(f"      Cliente: {billing.get('first_name', '')} {billing.get('last_name', '')}")
                print(f"      Email: {billing.get('email', 'N/A')}")
                print(f"      Total: ${orden.get('total', '0.00')}")
                print(f"      Estado: {orden.get('status', 'N/A')}")
                print(f"      Fecha: {orden.get('date_created', 'N/A')}")
                print(f"      Productos: {len(orden.get('line_items', []))} item(s)")
            
            return ordenes
        else:
            print(f"❌ Error al obtener órdenes: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Función principal"""
    print("=" * 60)
    print("🛒 TEST DE INTEGRACIÓN WOOCOMMERCE - UNILIMPIOSUR SAP")
    print("=" * 60)
    
    # Cargar configuración
    url, consumer_key, consumer_secret = cargar_configuracion()
    if not url:
        sys.exit(1)
    
    print(f"🌐 URL: {url}")
    print(f"🔑 Consumer Key: {consumer_key[:10]}...")
    print(f"🔐 Consumer Secret: {consumer_secret[:10]}...")
    
    # Crear cliente
    wcapi = crear_cliente_woocommerce(url, consumer_key, consumer_secret)
    if not wcapi:
        sys.exit(1)
    
    # Probar conexión
    if not probar_conexion(wcapi):
        print("\n❌ No se pudo establecer conexión con WooCommerce")
        sys.exit(1)
    
    # Obtener productos
    productos = obtener_productos(wcapi, 5)
    
    # Obtener órdenes
    ordenes = obtener_ordenes(wcapi, 3)
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    
    if productos:
        print(f"📦 Productos encontrados: {len(productos)}")
    if ordenes:
        print(f"📋 Órdenes encontradas: {len(ordenes)}")
    
    print("\n🎉 La integración con WooCommerce está funcionando correctamente!")

if __name__ == "__main__":
    main()
