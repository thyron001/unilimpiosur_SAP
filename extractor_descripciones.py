#!/usr/bin/env python3
"""
extractor_descripciones.py
Script independiente que extrae SOLO la columna de descripciones de productos
desde un PDF de orden de compra e imprime los nombres en terminal.

Requisitos:
- pdfplumber (pip install pdfplumber)
- pathlib
- re
"""

import re
import sys
from pathlib import Path
from typing import List

try:
    import pdfplumber
except ImportError:
    print("❌ Error: Necesitas instalar pdfplumber con: pip install pdfplumber")
    sys.exit(1)


class ExtractorDescripcionesCorrecto:
    """Extractor específico basado en la estructura exacta de tabla del PDF."""

    # Unidades válidas que indican inicio de producto
    UNIDADES_PRODUCTO = {
        'RESMA', 'GALON', 'ROLLO', 'UNIDAD', 'PAQUETE', 'CAJA', 'FUNDA',
        'KILO', 'PAR', 'METRO', 'LITRO', 'BOTELLA', 'SACO', 'TIRA'
    }

    def __init__(self, ruta_pdf: str):
        self.ruta_pdf = Path(ruta_pdf)
        if not self.ruta_pdf.exists() or self.ruta_pdf.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"No se encontró un PDF válido en: {self.ruta_pdf}")

    def _es_unidad_producto(self, palabra: str) -> bool:
        """Verifica si una palabra es una unidad válida de producto."""
        return palabra.upper() in self.UNIDADES_PRODUCTO

    def _extraer_lineas_producto(self, lineas: list) -> list:
        """Extrae líneas que contienen productos, combinando fragmentos."""
        productos = []
        i = 0

        while i < len(lineas):
            linea = lineas[i].strip()

            # Saltar líneas vacías o muy cortas
            if not linea or len(linea) < 8:
                i += 1
                continue

            # Buscar línea que comience con una unidad
            palabras = linea.split()
            if palabras and self._es_unidad_producto(palabras[0]):
                producto_completo = linea
                j = i + 1

                # Combinar con líneas siguientes que parezcan fragmentos
                while j < len(lineas) and j < i + 4:
                    siguiente = lineas[j].strip()

                    # Si la siguiente línea no está vacía y parece ser continuación
                    if (siguiente and len(siguiente) > 3 and
                        not siguiente[0].isupper() and  # no es nueva unidad
                        not self._es_unidad_producto(siguiente.split()[0] if siguiente.split() else "")):
                        producto_completo += " " + siguiente
                        j += 1
                    else:
                        break

                productos.append(producto_completo)
                i = j
            else:
                i += 1
        return productos

    def _extraer_descripcion_producto(self, linea_producto: str) -> str:
        """Extrae la descripción de una línea de producto con múltiples estrategias."""
        linea = linea_producto.strip()
        
        # Estrategia 1: Patrón estándar completo
        patron_estandar = re.compile(
            r"^(\w+)\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+(?:\d+(?:[.,]\d+)?\s+)?(?:\d+(?:[.,]\d+)?)?$"
        )
        
        match = patron_estandar.match(linea)
        if match:
            unidad = match.group(1)
            descripcion_cruda = match.group(2)
            cantidad = match.group(3)
            
            if self._es_unidad_producto(unidad.upper()):
                # Limpiar la descripción: eliminar unidades duplicadas y limpiar espacios
                descripcion_limpia = self._limpiar_descripcion(descripcion_cruda, unidad)
                return descripcion_limpia
        
        # Estrategia 2: Patrón más flexible - buscar unidad seguida de texto y números
        palabras = linea.split()
        if len(palabras) >= 3:
            unidad = palabras[0]
            
            if self._es_unidad_producto(unidad.upper()):
                # Buscar la posición donde empiezan los números (cantidad/precios)
                descripcion_partes = []
                i = 1
                
                # Recorrer palabras hasta encontrar números
                while i < len(palabras):
                    palabra = palabras[i]
                    # Si parece un número, hemos llegado al final de la descripción
                    if re.match(r'^\d+(?:[.,]\d+)?$', palabra):
                        break
                    descripcion_partes.append(palabra)
                    i += 1
                
                if descripcion_partes:
                    descripcion_cruda = " ".join(descripcion_partes)
                    descripcion_limpia = self._limpiar_descripcion(descripcion_cruda, unidad)
                    return descripcion_limpia
        
        return ""

    def _limpiar_descripcion(self, descripcion: str, unidad: str) -> str:
        """Limpia la descripción eliminando unidades duplicadas y espacios extra."""
        # Eliminar la unidad si aparece duplicada al final de la descripción
        unidad_upper = unidad.upper()
        descripcion_upper = descripcion.upper()
        
        # Si la descripción termina con la unidad, eliminarla
        if descripcion_upper.endswith(unidad_upper):
            descripcion = descripcion[:len(descripcion) - len(unidad)].rstrip()
        
        # Limpiar espacios múltiples
        descripcion = re.sub(r'\s+', ' ', descripcion)
        
        return descripcion.strip()

    def extraer_descripciones(self) -> List[str]:
        """Extrae todas las descripciones de productos del PDF."""
        descripciones = []

        try:
            with pdfplumber.open(self.ruta_pdf) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text() or ""
                    lineas = texto.split('\n')

                    # Extraer líneas de productos
                    lineas_producto = self._extraer_lineas_producto(lineas)

                    for linea_producto in lineas_producto:
                        descripcion = self._extraer_descripcion_producto(linea_producto)
                        if descripcion:
                            descripciones.append(descripcion)

        except Exception as e:
            print(f"❌ Error procesando PDF: {e}")
            return []

        # Eliminar duplicados manteniendo el orden
        vistas = set()
        descripciones_unicas = []
        for desc in descripciones:
            if desc not in vistas:
                vistas.add(desc)
                descripciones_unicas.append(desc)

        return descripciones_unicas

    def mostrar_descripciones(self) -> None:
        """Muestra las descripciones en terminal."""
        descripciones = self.extraer_descripciones()

        if not descripciones:
            print("⚠️ No se encontraron descripciones de productos en el PDF.")
            return

        print(f"\n📋 DESCRIPCIONES DE PRODUCTOS ENCONTRADAS ({len(descripciones)} productos):\n")
        print("=" * 80)

        for i, descripcion in enumerate(descripciones, 1):
            print(f"{i:3}. {descripcion}")

        print("=" * 80)
        print(f"\n✅ Total: {len(descripciones)} productos encontrados")


def main():
    """Función principal."""
    if len(sys.argv) != 2:
        print("Uso: python extractor_descripciones.py <ruta_al_pdf>")
        print("Ejemplo: python extractor_descripciones.py pedido1.pdf")
        sys.exit(1)

    ruta_pdf = sys.argv[1]

    try:
        extractor = ExtractorDescripcionesCorrecto(ruta_pdf)
        extractor.mostrar_descripciones()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
