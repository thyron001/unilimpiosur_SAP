#!/usr/bin/env python3
# verificar_emparejamiento.py
# Script para verificar emparejamiento de productos de PDFs con la base de datos
# 
# Extrae productos de todos los PDFs en la carpeta 'pedidos',
# revisa si están emparejados con los Alias de la BD,
# y genera un CSV con los resultados (emparejados y no emparejados).

from __future__ import annotations

import csv
from pathlib import Path
from datetime import datetime

from procesamiento_pedidos import (
    extraer_filas_pdf,
    emparejar_filas_con_bd,
    extraer_sucursal,
)


def verificar_emparejamiento_pedidos(
    carpeta_pedidos: str | Path = "pedidos",
    cliente_nombre: str = "Roldan",
    archivo_salida: str | None = None
) -> None:
    """
    Procesa todos los PDFs de la carpeta especificada y genera un CSV
    con los productos emparejados y no emparejados.
    
    Args:
        carpeta_pedidos: Ruta a la carpeta con los PDFs
        cliente_nombre: Nombre del cliente para emparejamiento
        archivo_salida: Nombre del archivo CSV de salida (opcional)
    """
    carpeta = Path(carpeta_pedidos)
    
    if not carpeta.exists() or not carpeta.is_dir():
        raise SystemExit(f"❌ La carpeta '{carpeta}' no existe o no es un directorio válido.")
    
    # Buscar todos los PDFs en la carpeta
    pdfs = sorted(carpeta.glob("*.pdf"))
    
    if not pdfs:
        print(f"⚠️  No se encontraron archivos PDF en la carpeta '{carpeta}'")
        return
    
    print(f"\n📁 Carpeta: {carpeta}")
    print(f"📄 PDFs encontrados: {len(pdfs)}")
    print("=" * 80)
    
    # Preparar resultados
    resultados_emparejados = []
    resultados_no_emparejados = []
    
    total_productos = 0
    total_emparejados = 0
    total_no_emparejados = 0
    
    # Procesar cada PDF
    for idx, pdf_path in enumerate(pdfs, 1):
        print(f"\n[{idx}/{len(pdfs)}] Procesando: {pdf_path.name}")
        print("-" * 80)
        
        try:
            # Leer PDF
            pdf_bytes = pdf_path.read_bytes()
            
            # Extraer filas del PDF
            filas = extraer_filas_pdf(pdf_bytes)
            
            if not filas:
                print(f"  ⚠️  No se detectaron productos en {pdf_path.name}")
                continue
            
            print(f"  ✓ Productos detectados: {len(filas)}")
            
            # Extraer información de sucursal
            resumen = extraer_sucursal(pdf_bytes)
            sucursal_alias = resumen.get("sucursal")
            sucursal_ruc = resumen.get("ruc")
            sucursal_encargado = resumen.get("encargado")
            orden_compra = resumen.get("orden_compra")
            
            print(f"  Sucursal: {sucursal_alias or 'N/A'}")
            print(f"  RUC: {sucursal_ruc or 'N/A'}")
            print(f"  Orden: {orden_compra or 'N/A'}")
            
            # Emparejar con la BD
            filas_enriquecidas, suc, cliente_id = emparejar_filas_con_bd(
                filas,
                cliente_nombre=cliente_nombre,
                sucursal_alias=sucursal_alias,
                sucursal_ruc=sucursal_ruc,
                sucursal_encargado=sucursal_encargado
            )
            
            # Clasificar resultados
            emparejados_pdf = 0
            no_emparejados_pdf = 0
            
            for fila in filas_enriquecidas:
                resultado = {
                    "archivo_pdf": pdf_path.name,
                    "orden_compra": orden_compra or "-",
                    "sucursal_pdf": sucursal_alias or "-",
                    "ruc_pdf": sucursal_ruc or "-",
                    "sucursal_bd": suc.get("nombre") if suc else "-",
                    "unidad": fila.get("uni") or "-",
                    "descripcion": fila.get("desc") or "-",
                    "cantidad": fila.get("cant") or "-",
                    "sku": fila.get("sku") or "-",
                    "bodega": fila.get("bodega") or "-",
                    "tipo_emparejado": fila.get("tipo_emparejado") or "-",
                    "score": fila.get("score_nombre") or 0.0,
                }
                
                if fila.get("sku"):
                    resultados_emparejados.append(resultado)
                    emparejados_pdf += 1
                else:
                    resultados_no_emparejados.append(resultado)
                    no_emparejados_pdf += 1
            
            total_productos += len(filas_enriquecidas)
            total_emparejados += emparejados_pdf
            total_no_emparejados += no_emparejados_pdf
            
            print(f"  ✓ Emparejados: {emparejados_pdf}")
            print(f"  ✗ No emparejados: {no_emparejados_pdf}")
            
        except Exception as e:
            print(f"  ❌ Error al procesar {pdf_path.name}: {e}")
            continue
    
    # Generar archivo de salida
    if archivo_salida is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_salida = carpeta / f"verificacion_emparejamiento_{timestamp}.csv"
    else:
        archivo_salida = Path(archivo_salida)
    
    # Escribir CSV con todos los resultados (emparejados primero, luego no emparejados)
    with open(archivo_salida, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = [
            "estado",
            "archivo_pdf",
            "orden_compra",
            "sucursal_pdf",
            "ruc_pdf",
            "sucursal_bd",
            "unidad",
            "descripcion",
            "cantidad",
            "sku",
            "bodega",
            "tipo_emparejado",
            "score"
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Escribir emparejados
        for resultado in resultados_emparejados:
            writer.writerow({
                "estado": "EMPAREJADO",
                **resultado
            })
        
        # Escribir no emparejados
        for resultado in resultados_no_emparejados:
            writer.writerow({
                "estado": "NO EMPAREJADO",
                **resultado
            })
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN GENERAL")
    print("=" * 80)
    print(f"Total de PDFs procesados: {len(pdfs)}")
    print(f"Total de productos: {total_productos}")
    print(f"✓ Emparejados: {total_emparejados} ({total_emparejados/total_productos*100:.1f}%)" if total_productos > 0 else "✓ Emparejados: 0")
    print(f"✗ No emparejados: {total_no_emparejados} ({total_no_emparejados/total_productos*100:.1f}%)" if total_productos > 0 else "✗ No emparejados: 0")
    print(f"\n✅ Archivo CSV generado: {archivo_salida}")
    print("\n💡 El archivo contiene:")
    print("   - Productos EMPAREJADOS (con SKU y bodega de la BD)")
    print("   - Productos NO EMPAREJADOS (sin SKU, necesitan ser agregados a la BD)")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verifica emparejamiento de productos de PDFs con la base de datos."
    )
    parser.add_argument(
        "--carpeta",
        type=str,
        default="pedidos",
        help="Carpeta con los PDFs a procesar (default: pedidos)"
    )
    parser.add_argument(
        "--cliente",
        type=str,
        default="Roldan",
        help="Nombre del cliente para emparejamiento (default: Roldan)"
    )
    parser.add_argument(
        "--salida",
        type=str,
        default=None,
        help="Nombre del archivo CSV de salida (default: auto-generado con timestamp)"
    )
    
    args = parser.parse_args()
    
    verificar_emparejamiento_pedidos(
        carpeta_pedidos=args.carpeta,
        cliente_nombre=args.cliente,
        archivo_salida=args.salida
    )


if __name__ == "__main__":
    main()





