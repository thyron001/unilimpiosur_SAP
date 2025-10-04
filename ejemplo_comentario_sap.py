#!/usr/bin/env python3
# ejemplo_comentario_sap.py
# Script de ejemplo para demostrar cómo se genera el comentario SAP

def generar_comentario_ejemplo(almacen: str, ciudad: str, orden_compra: str, encargado: str) -> str:
    """
    Genera un comentario de ejemplo según el formato SAP
    
    Formato: [Código SAP] | [URBANO] | Orden de compra: [XXX] | Encargado: [XXX]
    """
    comentarios_partes = []
    
    # 1. Código SAP (almacén)
    comentarios_partes.append(str(almacen))
    
    # 2. "URBANO" si la ciudad NO es Cuenca
    if ciudad and ciudad.upper() != "CUENCA":
        comentarios_partes.append("URBANO")
    
    # 3. Número de orden de compra con etiqueta
    if orden_compra:
        comentarios_partes.append(f"Orden de compra: {orden_compra}")
    
    # 4. Nombre del encargado con etiqueta
    if encargado:
        comentarios_partes.append(f"Encargado: {encargado}")
    
    # Unir todas las partes con pipe separado por espacios
    return " | ".join(comentarios_partes)


# ============================================
# EJEMPLOS DE USO
# ============================================

print("=" * 80)
print("EJEMPLOS DE GENERACIÓN DE COMENTARIOS SAP")
print("=" * 80)
print()

# Ejemplo 1: Pedido de Quito con todos los datos
print("📋 Ejemplo 1: Pedido de Quito (completo)")
print("-" * 80)
comentario1 = generar_comentario_ejemplo(
    almacen="10",
    ciudad="Quito",
    orden_compra="OS-0-0-4887",
    encargado="Gabriel Parra"
)
print(f"  Ciudad:         Quito")
print(f"  Código SAP:     10")
print(f"  Orden Compra:   OS-0-0-4887")
print(f"  Encargado:      Gabriel Parra")
print()
print(f"  ✅ Comentario:  '{comentario1}'")
print()

# Ejemplo 2: Pedido de Cuenca con todos los datos
print("📋 Ejemplo 2: Pedido de Cuenca (completo)")
print("-" * 80)
comentario2 = generar_comentario_ejemplo(
    almacen="20",
    ciudad="Cuenca",
    orden_compra="OS-0-0-5123",
    encargado="María López"
)
print(f"  Ciudad:         Cuenca")
print(f"  Código SAP:     20")
print(f"  Orden Compra:   OS-0-0-5123")
print(f"  Encargado:      María López")
print()
print(f"  ✅ Comentario:  '{comentario2}'")
print(f"  ℹ️  Nota: NO incluye 'URBANO' porque la ciudad es Cuenca")
print()

# Ejemplo 3: Pedido de Guayaquil sin orden de compra
print("📋 Ejemplo 3: Pedido de Guayaquil (sin orden de compra)")
print("-" * 80)
comentario3 = generar_comentario_ejemplo(
    almacen="30",
    ciudad="Guayaquil",
    orden_compra="",
    encargado="Pedro García"
)
print(f"  Ciudad:         Guayaquil")
print(f"  Código SAP:     30")
print(f"  Orden Compra:   (no disponible)")
print(f"  Encargado:      Pedro García")
print()
print(f"  ✅ Comentario:  '{comentario3}'")
print()

# Ejemplo 4: Pedido con datos mínimos
print("📋 Ejemplo 4: Pedido con datos mínimos")
print("-" * 80)
comentario4 = generar_comentario_ejemplo(
    almacen="5",
    ciudad="",
    orden_compra="",
    encargado=""
)
print(f"  Ciudad:         (no disponible)")
print(f"  Código SAP:     5")
print(f"  Orden Compra:   (no disponible)")
print(f"  Encargado:      (no disponible)")
print()
print(f"  ✅ Comentario:  '{comentario4}'")
print()

# Ejemplo 5: Pedido de Quito sin encargado
print("📋 Ejemplo 5: Pedido de Quito (sin encargado)")
print("-" * 80)
comentario5 = generar_comentario_ejemplo(
    almacen="15",
    ciudad="Quito",
    orden_compra="OS-0-0-7890",
    encargado=""
)
print(f"  Ciudad:         Quito")
print(f"  Código SAP:     15")
print(f"  Orden Compra:   OS-0-0-7890")
print(f"  Encargado:      (no disponible)")
print()
print(f"  ✅ Comentario:  '{comentario5}'")
print()

# Ejemplo 6: Verificar que la comparación de ciudad es case-insensitive
print("📋 Ejemplo 6: Verificación case-insensitive (CUENCA en mayúsculas)")
print("-" * 80)
comentario6 = generar_comentario_ejemplo(
    almacen="25",
    ciudad="CUENCA",  # En mayúsculas
    orden_compra="OS-0-0-6543",
    encargado="Ana Rodríguez"
)
print(f"  Ciudad:         CUENCA (mayúsculas)")
print(f"  Código SAP:     25")
print(f"  Orden Compra:   OS-0-0-6543")
print(f"  Encargado:      Ana Rodríguez")
print()
print(f"  ✅ Comentario:  '{comentario6}'")
print(f"  ℹ️  Nota: Tampoco incluye 'URBANO' (comparación case-insensitive)")
print()

print("=" * 80)
print("RESUMEN")
print("=" * 80)
print()
print("✅ Formato correcto implementado:")
print("   [Código SAP] | [URBANO*] | Orden de compra: [XXX*] | Encargado: [XXX*]")
print()
print("   * Campos opcionales según disponibilidad")
print("   * URBANO solo si ciudad ≠ Cuenca")
print("   * Separador: ' | ' (pipe con espacios)")
print()
print("=" * 80)

