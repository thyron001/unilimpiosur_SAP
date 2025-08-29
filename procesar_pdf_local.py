# procesar_pdf_local.py
# Uso local: lee un PDF de orden de compra, imprime filas + totales + sucursal,
# y guarda el pedido en PostgreSQL (a menos que se use --dry-run).
#
# Requisitos:
#   - Variables de entorno de PostgreSQL (PGHOST, PGUSER, PGPASSWORD, etc.)
#   - Catalogo CSV (ruta en env PRODUCT_CSV o "productos_roldan.csv" por defecto)

from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime

from procesamiento_pedidos import (
    extraer_filas_pdf,
    emparejar_filas_con_catalogo,
    imprimir_filas,
    imprimir_filas_emparejadas,
    extraer_sucursal_y_totales,
    imprimir_resumen_pedido,
    guardar_asignaciones_csv,
)
from persistencia_postgresql import guardar_pedido


def main():
    parser = argparse.ArgumentParser(
        description="Procesa un PDF local de orden de compra: imprime información y guarda en PostgreSQL."
    )
    parser.add_argument("pdf", type=str, help="Ruta al archivo PDF a procesar.")
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha del pedido en ISO-8601 (ej. 2025-08-29T10:30:00). Si no se indica, se usa ahora.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No guarda en la base de datos; solo imprime resultados.",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Ruta opcional para exportar un CSV de las asignaciones (SKU/bodega).",
    )

    args = parser.parse_args()
    ruta_pdf = Path(args.pdf)

    if not ruta_pdf.exists() or ruta_pdf.suffix.lower() != ".pdf":
        raise SystemExit(f"❌ No se encontró un PDF válido en: {ruta_pdf}")

    # Leer bytes del PDF
    pdf_bytes = ruta_pdf.read_bytes()

    print("\n========== 1) FILAS DETECTADAS EN EL PDF ==========")
    filas = extraer_filas_pdf(pdf_bytes)
    imprimir_filas(filas)

    print("\n========== 2) EMPAREJADO CON CATÁLOGO (SKU/BODEGA) ==========")
    filas_enriquecidas = emparejar_filas_con_catalogo(filas)
    imprimir_filas_emparejadas(filas_enriquecidas)

    if args.csv:
        guardar_asignaciones_csv(filas_enriquecidas, args.csv)

    print("\n========== 3) SUCURSAL Y TOTALES ==========")
    resumen = extraer_sucursal_y_totales(pdf_bytes)
    imprimir_resumen_pedido(resumen)

    # Preparar payload para persistencia
    if args.fecha:
        try:
            fecha_obj = datetime.fromisoformat(args.fecha)
        except Exception:
            print("⚠️  No se pudo parsear --fecha; se usa el momento actual.")
            fecha_obj = datetime.now()
    else:
        fecha_obj = datetime.now()

    pedido = {
        "fecha": fecha_obj,
        "sucursal": resumen.get("sucursal"),
        "subtotal_bruto": resumen.get("subtotal_bruto"),
        "descuento": resumen.get("descuento"),
        "subtotal_neto": resumen.get("subtotal_neto"),
        "iva_0": resumen.get("iva_0"),
        "iva_15": resumen.get("iva_15"),
        "total": resumen.get("total"),
    }

    if args.dry_run:
        print("\n🧪 DRY-RUN activado: no se guardará en la base de datos.")
        return

    print("\n========== 4) GUARDANDO EN POSTGRESQL ==========")
    pedido_id, numero_pedido = guardar_pedido(pedido, filas_enriquecidas)
    print(f"✅ Guardado: pedido_id={pedido_id}, numero_pedido={numero_pedido}")


if __name__ == "__main__":
    main()
