import re
import pdfplumber

PDF_PATH = "pedido.pdf"

# Palabras de unidad que aparecen en el PDF (puedes agregar más si hiciera falta)
UNIT_WORDS = {
    "Unidad", "RESMA", "Caja", "Rollo", "Paquete",
    "Funda", "Galon", "Kilo", "Par", "Unidad."
}

# Filas con "unidad + descripción + cant + p.uni + p.total" en UNA MISMA LÍNEA
LINE_W_UNIT = re.compile(
    r"^(?P<uni>\S+)\s+(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)

# Filas donde la UNIDAD VIENE EN LÍNEA ANTERIOR -> aquí solo hay "desc + cant + p.uni + p.total"
LINE_WO_UNIT = re.compile(
    r"^(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)

SKIP_IF_CONTAINS = (
    "Uni. Descripción", "Subtotal", "TOTAL", "IVA", "Proveedor",
    "ORDEN DE COMPRA", "Fecha:", "Dirección:", "Teléfono:", "Política:",
    "Razón", "RUC:", "E-mail", "Datos de facturación", "Aprueba:", "Recibe:", "Analiza:", "Solicita:"
)

def should_skip(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    for kw in SKIP_IF_CONTAINS:
        if kw in s:
            return True
    return False

def clean_unit(u: str) -> str:
    return u.rstrip(".")

def main():
    rows = []
    with pdfplumber.open(PDF_PATH) as pdf:
        pending_unit = None  # si una línea es solo "Paquete", "Unidad", etc., se guarda aquí
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            for raw in text.splitlines():
                line = raw.strip()
                if should_skip(line):
                    continue

                # ¿La línea es SOLO la unidad?
                if line in UNIT_WORDS:
                    pending_unit = clean_unit(line)
                    continue

                # Intento 1: toda la fila viene en la misma línea (con unidad al inicio)
                m = LINE_W_UNIT.match(line)
                if m and clean_unit(m.group("uni")) in UNIT_WORDS:
                    d = m.groupdict()
                    d["uni"] = clean_unit(d["uni"])
                    rows.append(d)
                    pending_unit = None
                    continue

                # Intento 2: la unidad venía en la línea anterior; esta línea trae desc + números
                if pending_unit:
                    m2 = LINE_WO_UNIT.match(line)
                    if m2:
                        d = m2.groupdict()
                        d["uni"] = pending_unit
                        rows.append(d)
                        pending_unit = None
                        continue

                # Si no encaja, la ignoramos (encabezados raros, saltos, etc.)

    if not rows:
        print("⚠️ No se detectaron filas. Revisa que 'pedido.pdf' sea el archivo correcto.")
        return

    # Imprimir en terminal
    print(f"{'Uni.':<10} | {'Descripción':<70} | {'Cant':>4} | {'P. Uni':>8} | {'P. Total':>9}")
    print("-" * 110)
    for r in rows:
        desc = r["desc"].strip()
        cant = r["cant"]
        puni = r["puni"].replace(",", ".")
        ptotal = r["ptotal"].replace(",", ".")
        uni = r["uni"]
        print(f"{uni:<10} | {desc[:70]:<70} | {cant:>4} | {puni:>8} | {ptotal:>9}")

if __name__ == "__main__":
    main()
