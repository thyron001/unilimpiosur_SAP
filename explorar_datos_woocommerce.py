#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para explorar en detalle los datos de WooCommerce
Sistema UnilimpioSur SAP
"""

import os
import json
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

def explorar_orden_completa(wcapi, orden_id):
    """Explora todos los datos de una orden específica"""
    print(f"\n🔍 EXPLORANDO ORDEN #{orden_id} EN DETALLE")
    print("=" * 60)
    
    try:
        response = wcapi.get(f"orders/{orden_id}")
        if response.status_code == 200:
            orden = response.json()
            
            print(f"📋 INFORMACIÓN BÁSICA:")
            print(f"   ID: {orden.get('id')}")
            print(f"   Número: {orden.get('number')}")
            print(f"   Estado: {orden.get('status')}")
            print(f"   Moneda: {orden.get('currency')}")
            print(f"   Total: ${orden.get('total')}")
            print(f"   Subtotal: ${orden.get('subtotal')}")
            print(f"   Impuestos: ${orden.get('total_tax')}")
            print(f"   Envío: ${orden.get('shipping_total')}")
            print(f"   Descuento: ${orden.get('discount_total')}")
            
            print(f"\n📅 FECHAS:")
            print(f"   Creada: {orden.get('date_created')}")
            print(f"   Modificada: {orden.get('date_modified')}")
            print(f"   Completada: {orden.get('date_completed')}")
            print(f"   Pagada: {orden.get('date_paid')}")
            
            print(f"\n👤 INFORMACIÓN DEL CLIENTE:")
            billing = orden.get('billing', {})
            print(f"   Nombre: {billing.get('first_name')} {billing.get('last_name')}")
            print(f"   Empresa: {billing.get('company')}")
            print(f"   Email: {billing.get('email')}")
            print(f"   Teléfono: {billing.get('phone')}")
            print(f"   Dirección 1: {billing.get('address_1')}")
            print(f"   Dirección 2: {billing.get('address_2')}")
            print(f"   Ciudad: {billing.get('city')}")
            print(f"   Estado: {billing.get('state')}")
            print(f"   Código Postal: {billing.get('postcode')}")
            print(f"   País: {billing.get('country')}")
            
            print(f"\n🚚 INFORMACIÓN DE ENVÍO:")
            shipping = orden.get('shipping', {})
            print(f"   Nombre: {shipping.get('first_name')} {shipping.get('last_name')}")
            print(f"   Empresa: {shipping.get('company')}")
            print(f"   Dirección 1: {shipping.get('address_1')}")
            print(f"   Dirección 2: {shipping.get('address_2')}")
            print(f"   Ciudad: {shipping.get('city')}")
            print(f"   Estado: {shipping.get('state')}")
            print(f"   Código Postal: {shipping.get('postcode')}")
            print(f"   País: {shipping.get('country')}")
            
            print(f"\n📦 PRODUCTOS EN LA ORDEN:")
            line_items = orden.get('line_items', [])
            for i, item in enumerate(line_items, 1):
                print(f"   {i}. {item.get('name')}")
                print(f"      ID: {item.get('id')}")
                print(f"      SKU: {item.get('sku', 'Sin SKU')}")
                print(f"      Cantidad: {item.get('quantity')}")
                print(f"      Precio unitario: ${item.get('price')}")
                print(f"      Total: ${item.get('total')}")
                print(f"      Impuestos: ${item.get('total_tax')}")
                print(f"      Producto ID: {item.get('product_id')}")
                print(f"      Variación ID: {item.get('variation_id')}")
                if item.get('meta_data'):
                    print(f"      Metadatos: {len(item.get('meta_data'))} elemento(s)")
                print()
            
            print(f"\n💰 INFORMACIÓN DE PAGO:")
            print(f"   Método de pago: {orden.get('payment_method')}")
            print(f"   Título del método: {orden.get('payment_method_title')}")
            print(f"   ID de transacción: {orden.get('transaction_id')}")
            
            print(f"\n🚚 INFORMACIÓN DE ENVÍO:")
            shipping_lines = orden.get('shipping_lines', [])
            for i, shipping in enumerate(shipping_lines, 1):
                print(f"   {i}. {shipping.get('method_title')}")
                print(f"      Total: ${shipping.get('total')}")
                print(f"      Impuestos: ${shipping.get('total_tax')}")
            
            print(f"\n🏷️ MÉTODOS DE ENVÍO:")
            for i, method in enumerate(orden.get('shipping_lines', []), 1):
                print(f"   {i}. {method.get('method_title')} - ${method.get('total')}")
            
            print(f"\n📝 NOTAS:")
            notes = orden.get('customer_note', '')
            if notes:
                print(f"   Nota del cliente: {notes}")
            
            print(f"\n🔗 METADATOS:")
            meta_data = orden.get('meta_data', [])
            if meta_data:
                for meta in meta_data:
                    print(f"   {meta.get('key')}: {meta.get('value')}")
            else:
                print("   Sin metadatos adicionales")
            
            # Guardar JSON completo para análisis
            with open(f"orden_{orden_id}_completa.json", "w", encoding="utf-8") as f:
                json.dump(orden, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Datos completos guardados en: orden_{orden_id}_completa.json")
            
            return orden
        else:
            print(f"❌ Error al obtener orden: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def explorar_producto_completo(wcapi, producto_id):
    """Explora todos los datos de un producto específico"""
    print(f"\n🔍 EXPLORANDO PRODUCTO #{producto_id} EN DETALLE")
    print("=" * 60)
    
    try:
        response = wcapi.get(f"products/{producto_id}")
        if response.status_code == 200:
            producto = response.json()
            
            print(f"📦 INFORMACIÓN BÁSICA:")
            print(f"   ID: {producto.get('id')}")
            print(f"   Nombre: {producto.get('name')}")
            print(f"   SKU: {producto.get('sku', 'Sin SKU')}")
            print(f"   Slug: {producto.get('slug')}")
            print(f"   Estado: {producto.get('status')}")
            print(f"   Tipo: {producto.get('type')}")
            print(f"   Precio regular: ${producto.get('regular_price', '0.00')}")
            print(f"   Precio de venta: ${producto.get('sale_price', 'N/A')}")
            print(f"   Precio actual: ${producto.get('price', '0.00')}")
            
            print(f"\n📊 INVENTARIO:")
            print(f"   Stock: {producto.get('stock_quantity', 'N/A')}")
            print(f"   Estado de stock: {producto.get('stock_status')}")
            print(f"   Gestión de stock: {producto.get('manage_stock')}")
            print(f"   Stock bajo: {producto.get('low_stock_amount', 'N/A')}")
            print(f"   Stock backorders: {producto.get('backorders')}")
            
            print(f"\n📝 DESCRIPCIÓN:")
            descripcion = producto.get('short_description', '')
            if descripcion:
                print(f"   Corta: {descripcion[:100]}...")
            descripcion_larga = producto.get('description', '')
            if descripcion_larga:
                print(f"   Larga: {descripcion_larga[:100]}...")
            
            print(f"\n🏷️ CATEGORÍAS:")
            categorias = producto.get('categories', [])
            for cat in categorias:
                print(f"   - {cat.get('name')} (ID: {cat.get('id')})")
            
            print(f"\n🏪 ATRIBUTOS:")
            atributos = producto.get('attributes', [])
            for attr in atributos:
                print(f"   - {attr.get('name')}: {', '.join(attr.get('options', []))}")
            
            print(f"\n📅 FECHAS:")
            print(f"   Creado: {producto.get('date_created')}")
            print(f"   Modificado: {producto.get('date_modified')}")
            print(f"   En venta desde: {producto.get('date_on_sale_from')}")
            print(f"   En venta hasta: {producto.get('date_on_sale_to')}")
            
            print(f"\n🔗 METADATOS:")
            meta_data = producto.get('meta_data', [])
            if meta_data:
                for meta in meta_data:
                    print(f"   {meta.get('key')}: {meta.get('value')}")
            else:
                print("   Sin metadatos adicionales")
            
            # Guardar JSON completo para análisis
            with open(f"producto_{producto_id}_completo.json", "w", encoding="utf-8") as f:
                json.dump(producto, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Datos completos guardados en: producto_{producto_id}_completo.json")
            
            return producto
        else:
            print(f"❌ Error al obtener producto: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Función principal"""
    print("=" * 60)
    print("🔍 EXPLORADOR DE DATOS WOOCOMMERCE - UNILIMPIOSUR SAP")
    print("=" * 60)
    
    # Cargar configuración
    url, consumer_key, consumer_secret = cargar_configuracion()
    if not url:
        return
    
    # Crear cliente
    wcapi = crear_cliente_woocommerce(url, consumer_key, consumer_secret)
    if not wcapi:
        return
    
    # Obtener una orden reciente para explorar
    try:
        response = wcapi.get("orders", params={"per_page": 1, "page": 1})
        if response.status_code == 200:
            ordenes = response.json()
            if ordenes:
                orden_id = ordenes[0].get('id')
                explorar_orden_completa(wcapi, orden_id)
            else:
                print("❌ No hay órdenes para explorar")
        else:
            print(f"❌ Error al obtener órdenes: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Obtener un producto para explorar
    try:
        response = wcapi.get("products", params={"per_page": 1, "page": 1})
        if response.status_code == 200:
            productos = response.json()
            if productos:
                producto_id = productos[0].get('id')
                explorar_producto_completo(wcapi, producto_id)
            else:
                print("❌ No hay productos para explorar")
        else:
            print(f"❌ Error al obtener productos: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
