# procesar_pdf_local.py
# Uso local: lee un PDF de orden de compra, imprime filas + totales + sucursal,
# y guarda el pedido en PostgreSQL (a menos que se use --dry-run).
#
# Requisitos:
#   - Variables de entorno de PostgreSQL (PGHOST, PGUSER, PGPASSWORD, etc.)
#   - NO usa catálogos CSV para emparejar (solo BD). La opción --csv es opcional
#     y sirve para exportar un CSV de auditoría con las asignaciones resultantes.

from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime

from procesamiento_pedidos import (
    extraer_filas_pdf,
    emparejar_filas_con_bd,          # <- emparejador por NOMBRE + unidad (BD)
    imprimir_filas,
    imprimir_filas_emparejadas,
    extraer_sucursal,
    imprimir_resumen_pedido,
)
from persistencia_postgresql import guardar_pedido


# =========================
#  GENERADORES DE ARCHIVOS SAP (ODRF/DRF1)
# =========================

def formatear_fecha_yyyymmdd(fecha: datetime | str | None) -> str:
    """
    Convierte una fecha (datetime o string) al formato YYYYMMDD.
    Si no viene nada, devuelve la fecha de hoy.
    """
    if isinstance(fecha, datetime):
        return fecha.strftime("%Y%m%d")
    if isinstance(fecha, str):
        # Intenta parsear YYYY-MM-DD, DD/MM/YYYY, etc.
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                d = datetime.strptime(fecha.strip(), fmt)
                return d.strftime("%Y%m%d")
            except Exception:
                pass
        f = fecha.strip()
        if len(f) == 8 and f.isdigit():
            return f
    return datetime.now().strftime("%Y%m%d")


def _normalizar_bodega(bodega_val) -> str:
    """
    Normaliza la bodega (WhsCode/U_EXX_ALMACEN).
    Para WhsCode en DRF1 usamos '05' por defecto si está vacío.
    Para U_EXX_ALMACEN en ODRF usamos '5' fijo (según requerimiento).
    """
    if bodega_val is None:
        return ""
    return str(bodega_val).strip().zfill(2)


def _tomar_campo_item(item: dict, claves_posibles: list[str], default=None):
    """
    Toma el primer valor disponible de un ítem probando múltiples nombres de clave.
    """
    for k in claves_posibles:
        if k in item and item[k] not in (None, "", "-"):
            return item[k]
    return default


def generar_archivo_odrf(ruta_salida: str | Path,
                         docentry: int | str,
                         docdate: str,
                         sucursal: str,
                         cardcode_const: str = "CL0190316025001",
                         objtype_const: str = "17",
                         series_const: str = "76",
                         almac_const: str = "5",
                         usar_shpdgd: str = "N") -> None:
    """
    Genera ODRF.txt con las dos líneas de cabecera y una fila de datos.
    Campos separados por tab.
    """
    ruta_salida = Path(ruta_salida)
    lineas: list[str] = []

    # Cabeceras EXACTAS (dos variantes)
    cab1 = "DocEntry\tDocNum\tDocType\tPrinted\tDocDate\tDocDueDate\tCardCode\tDocObjectCode\tSeries\tShipToCode\tU_EXX_ALMACEN\tComments\tUseShpdGoodsAct"
    cab2 = "DocEntry\tDocNum\tDocType\tPrinted\tDocDate\tDocDueDate\tCardCode\tObjType\tSeries\tShipToCode\tU_EXX_ALMACEN\tComments\tUseShpdGd"
    lineas.append(cab1)
    lineas.append(cab2)

    fila = [
        str(docentry),                 # DocEntry
        str(docentry),                 # DocNum
        "dDocument_Items",             # DocType
        "Y",                           # Printed
        docdate,                       # DocDate
        docdate,                       # DocDueDate
        cardcode_const,                # CardCode
        objtype_const,                 # ObjType
        series_const,                  # Series
        (sucursal or "").strip(),      # ShipToCode
        almac_const,                   # U_EXX_ALMACEN
        (sucursal or "").strip(),      # Comments
        usar_shpdgd                    # UseShpdGd
    ]
    lineas.append("\t".join(fila))

    ruta_salida.write_text("\n".join(lineas), encoding="utf-8")
    print(f"✅ Archivo ODRF generado: {ruta_salida}")


def generar_archivo_drf1(ruta_salida: str | Path,
                         docnum: int | str,
                         sucursal: str,
                         items: list[dict],
                         whscode_default: str = "05",
                         usar_shpdgd: str = "N") -> None:
    """
    Genera DRF1.txt con dos líneas de cabecera y tantas filas como ítems.
    Columnas:
    DocNum, ItemCode, Quantity, WhsCode, CogsOcrCo5 (sucursal), UseShpdGd
    """
    ruta_salida = Path(ruta_salida)
    lineas: list[str] = []

    # Cabeceras EXACTAS (dos variantes)
    cab1 = "ParentKey\tItemCode\tPrice\tQuantity\tWarehouseCode\tShipToCode\tUseShpdGoodsAct"
    cab2 = "DocNum\tItemCode\tPrice\tQuantity\tWhsCode\tCogsOcrCo5\tUseShpdGd"
    lineas.append(cab1)
    lineas.append(cab2)

    suc = (sucursal or "").strip()

    for it in items or []:
        sku = _tomar_campo_item(it, ["sku", "SKU", "itemcode", "ItemCode", "codigo", "Código"], default="")
        # Incluir 'cant' (clave que usamos al extraer del PDF)
        qty = _tomar_campo_item(it, ["cantidad", "Cantidad", "quantity", "Quantity", "cant", "Cant"], default=0)
        whs = _tomar_campo_item(it, ["bodega", "Bodega", "whscode", "WhsCode"], default=whscode_default)

        sku = str(sku or "").strip()
        whs = _normalizar_bodega(whs) or whscode_default

        # cantidad segura (entero)
        try:
            qty_num = int(str(qty).strip())
        except Exception:
            try:
                qty_num = round(float(str(qty).replace(",", ".").strip()))
            except Exception:
                qty_num = 0

        fila = [
            str(docnum),          # DocNum / ParentKey
            sku,                  # ItemCode
            "1",                 # Price (fijo 1)
            str(qty_num),         # Quantity
            whs,                  # WhsCode / WarehouseCode
            suc,                  # CogsOcrCo5 / ShipToCode
            usar_shpdgd           # UseShpdGd / UseShpdGoodsAct
        ]
        lineas.append("\t".join(fila))

    ruta_salida.write_text("\n".join(lineas), encoding="utf-8")
    print(f"✅ Archivo DRF1 generado: {ruta_salida}")


def generar_archivos_sap_para_pedido(numero_pedido: int | str,
                                     fecha_pedido: datetime | str | None,
                                     sucursal: str,
                                     items: list[dict],
                                     carpeta_salida: str | Path = ".") -> None:
    """
    Genera ODRF.txt y DRF1.txt juntos en la carpeta indicada.
    """
    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)

    fecha_fmt = formatear_fecha_yyyymmdd(fecha_pedido)

    generar_archivo_odrf(
        ruta_salida=carpeta / "ODRF.txt",
        docentry=numero_pedido,
        docdate=fecha_fmt,
        sucursal=sucursal,
        cardcode_const="CL0190316025001",
        objtype_const="17",
        series_const="76",
        almac_const="5",
        usar_shpdgd="N"
    )

    generar_archivo_drf1(
        ruta_salida=carpeta / "DRF1.txt",
        docnum=numero_pedido,
        sucursal=sucursal,
        items=items,
        whscode_default="05",
        usar_shpdgd="N"
    )


# =========================
#  PROGRAMA PRINCIPAL
# =========================

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
        help="No guarda en la base de datos; solo imprime resultados y genera ODRF/DRF1.",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Ruta opcional para exportar un CSV de auditoría de las asignaciones (SKU/Bodega).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=".",
        help="Carpeta donde guardar ODRF.txt y DRF1.txt (por defecto, carpeta actual).",
    )
    parser.add_argument(
        "--cliente",
        type=str,
        default="Roldan",
        help="Nombre del cliente a usar para emparejar y bodegas (default: Roldan).",
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

    print("\n========== 2) SUCURSAL (DESDE PDF) ==========")
    resumen = extraer_sucursal(pdf_bytes)
    imprimir_resumen_pedido(resumen)

    print("\n========== 3) EMPAREJADO POR NOMBRE (BD) ==========")
    filas_enriquecidas, suc, cliente_id = emparejar_filas_con_bd(
        filas,
        cliente_nombre=args.cliente,
        sucursal_alias=resumen.get("sucursal"),
        sucursal_ruc=resumen.get("ruc")
    )
    imprimir_filas_emparejadas(filas_enriquecidas)

    if args.csv:
        guardar_asignaciones_csv(filas_enriquecidas, args.csv)

    # Preparar payload para persistencia
    if args.fecha:
        try:
            fecha_obj = datetime.fromisoformat(args.fecha)
        except Exception:
            print("⚠️  No se pudo parsear --fecha; se usa el momento actual.")
            fecha_obj = datetime.now()
    else:
        fecha_obj = datetime.now()

    # Verificar si se encontró la sucursal por alias o RUC
    sucursal_alias_pdf = resumen.get("sucursal")
    sucursal_ruc_pdf = resumen.get("ruc")
    if (sucursal_alias_pdf or sucursal_ruc_pdf) and not suc:
        # No se encontró coincidencia en el alias ni en el RUC - marcar como error
        error_msg = []
        if sucursal_alias_pdf:
            error_msg.append(f"alias '{sucursal_alias_pdf}'")
        if sucursal_ruc_pdf:
            error_msg.append(f"RUC '{sucursal_ruc_pdf}'")
        print(f"❌ ERROR: No se encontró sucursal con {' ni '.join(error_msg)} en la base de datos")
        sucursal_txt = f"ERROR: {' ni '.join(error_msg)} no encontrado"
    else:
        # Si encontramos la sucursal en BD, usamos su NOMBRE de sistema; si no, el texto del PDF
        sucursal_txt = suc.get("nombre") if suc else "SUCURSAL DESCONOCIDA"

    # Generar comentario con información del pedido
    comentario_parts = []
    
    # Agregar número de pedido (se asignará después de guardar)
    comentario_parts.append(f"Pedido: [NUMERO_PEDIDO]")
    
    # Agregar orden de compra si está disponible
    orden_compra = resumen.get("orden_compra")
    if orden_compra:
        comentario_parts.append(f"OC: {orden_compra}")
    
    # Agregar placeholder para el encargado de la sucursal (se completará después)
    comentario_parts.append(f"Encargado: [ENCARGADO_SUCURSAL]")
    
    comentario = " | ".join(comentario_parts)

    pedido = {
        "fecha": fecha_obj,
        "sucursal": sucursal_txt,
        "comentario": comentario,
    }

    # ======== DRY-RUN: Solo mostrar información sin grabar en BD ========
    if args.dry_run:
        print("\n🧪 DRY-RUN activado: no se guardará en la base de datos.")
        print(f"   → Cliente ID: {cliente_id}")
        print(f"   → Sucursal ID: {suc.get('id') if suc else None}")
        print(f"   → Sucursal: {sucursal_txt}")
        return

    print("\n========== 4) GUARDANDO EN POSTGRESQL ==========")
    sucursal_id = suc.get("id") if suc else None
    pedido_id, numero_pedido, estado = guardar_pedido(pedido, filas_enriquecidas, cliente_id, sucursal_id)
    print(f"✅ Guardado: pedido_id={pedido_id}, numero_pedido={numero_pedido}, estado={estado}")
    print(f"   → Cliente ID: {cliente_id}")
    print(f"   → Sucursal ID: {sucursal_id}")

    print("\n✅ Procesamiento completado. El pedido está listo para generar archivos SAP desde la interfaz web.")


if __name__ == "__main__":
    main()
