"""Almacenamiento en memoria para el Mock Sheets API con datos de prueba."""

from datetime import date

# ─── Datos de prueba: 3 meses de ventas ───
VENTAS = [
    # Abril 2026
    {"fila": 2, "fecha": "2026-04-03", "sabor": "mango", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 3, "fecha": "2026-04-05", "sabor": "fresa", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 4, "fecha": "2026-04-08", "sabor": "limon", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 40.00, "canal": "gimnasio"},
    {"fila": 5, "fecha": "2026-04-10", "sabor": "jengibre", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 50.00, "canal": "gimnasio"},
    {"fila": 6, "fecha": "2026-04-12", "sabor": "menta", "presentacion": "345ml", "cantidad": 2, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 7, "fecha": "2026-04-15", "sabor": "mango", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 45.00, "canal": "redes"},
    {"fila": 8, "fecha": "2026-04-18", "sabor": "fresa", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 45.00, "canal": "redes"},
    {"fila": 9, "fecha": "2026-04-20", "sabor": "mango", "presentacion": "1L", "cantidad": 1, "precio_unitario": 90.00, "canal": "redes"},
    {"fila": 10, "fecha": "2026-04-22", "sabor": "limon", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 40.00, "canal": "gimnasio"},
    {"fila": 11, "fecha": "2026-04-25", "sabor": "mango", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 45.00, "canal": "gimnasio"},
    # Mayo 2026
    {"fila": 12, "fecha": "2026-05-02", "sabor": "mango", "presentacion": "345ml", "cantidad": 6, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 13, "fecha": "2026-05-05", "sabor": "fresa", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 14, "fecha": "2026-05-07", "sabor": "limon", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 40.00, "canal": "redes"},
    {"fila": 15, "fecha": "2026-05-10", "sabor": "jengibre", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 50.00, "canal": "gimnasio"},
    {"fila": 16, "fecha": "2026-05-12", "sabor": "menta", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 17, "fecha": "2026-05-15", "sabor": "mango", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 45.00, "canal": "redes"},
    {"fila": 18, "fecha": "2026-05-18", "sabor": "fresa", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 19, "fecha": "2026-05-20", "sabor": "mango", "presentacion": "1L", "cantidad": 1, "precio_unitario": 90.00, "canal": "gimnasio"},
    {"fila": 20, "fecha": "2026-05-22", "sabor": "limon", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 40.00, "canal": "gimnasio"},
    {"fila": 21, "fecha": "2026-05-25", "sabor": "mango", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 45.00, "canal": "gimnasio"},
    # Junio 2026
    {"fila": 22, "fecha": "2026-06-02", "sabor": "mango", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 23, "fecha": "2026-06-04", "sabor": "fresa", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 24, "fecha": "2026-06-06", "sabor": "limon", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 40.00, "canal": "gimnasio"},
    {"fila": 25, "fecha": "2026-06-08", "sabor": "jengibre", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 50.00, "canal": "gimnasio"},
    {"fila": 26, "fecha": "2026-06-09", "sabor": "menta", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 45.00, "canal": "redes"},
    {"fila": 27, "fecha": "2026-06-10", "sabor": "mango", "presentacion": "345ml", "cantidad": 7, "precio_unitario": 45.00, "canal": "gimnasio"},
    {"fila": 28, "fecha": "2026-06-12", "sabor": "fresa", "presentacion": "345ml", "cantidad": 3, "precio_unitario": 45.00, "canal": "redes"},
    {"fila": 29, "fecha": "2026-06-14", "sabor": "mango", "presentacion": "1L", "cantidad": 1, "precio_unitario": 90.00, "canal": "redes"},
    {"fila": 30, "fecha": "2026-06-15", "sabor": "limon", "presentacion": "345ml", "cantidad": 5, "precio_unitario": 40.00, "canal": "gimnasio"},
    {"fila": 31, "fecha": "2026-06-16", "sabor": "fresa", "presentacion": "345ml", "cantidad": 4, "precio_unitario": 45.00, "canal": "gimnasio"},
]

# ─── Costos de producción por sabor y presentación ───
COSTOS = [
    {"sabor": "mango", "presentacion": "345ml", "costo_ingredientes": 10.00, "costo_envase": 4.50, "costo_mano_obra": 3.00, "costo_unitario_total": 17.50},
    {"sabor": "fresa", "presentacion": "345ml", "costo_ingredientes": 11.50, "costo_envase": 4.50, "costo_mano_obra": 3.00, "costo_unitario_total": 19.00},
    {"sabor": "limon", "presentacion": "345ml", "costo_ingredientes": 8.80, "costo_envase": 4.00, "costo_mano_obra": 3.00, "costo_unitario_total": 15.80},
    {"sabor": "jengibre", "presentacion": "345ml", "costo_ingredientes": 13.00, "costo_envase": 4.50, "costo_mano_obra": 3.00, "costo_unitario_total": 20.50},
    {"sabor": "menta", "presentacion": "345ml", "costo_ingredientes": 9.50, "costo_envase": 4.50, "costo_mano_obra": 3.00, "costo_unitario_total": 17.00},
    {"sabor": "mango", "presentacion": "1L", "costo_ingredientes": 22.00, "costo_envase": 10.00, "costo_mano_obra": 6.00, "costo_unitario_total": 38.00},
    {"sabor": "fresa", "presentacion": "1L", "costo_ingredientes": 25.00, "costo_envase": 10.00, "costo_mano_obra": 6.00, "costo_unitario_total": 41.00},
    {"sabor": "limon", "presentacion": "1L", "costo_ingredientes": 19.00, "costo_envase": 9.50, "costo_mano_obra": 6.00, "costo_unitario_total": 34.50},
    {"sabor": "jengibre", "presentacion": "1L", "costo_ingredientes": 28.00, "costo_envase": 10.00, "costo_mano_obra": 6.00, "costo_unitario_total": 44.00},
    {"sabor": "menta", "presentacion": "1L", "costo_ingredientes": 21.00, "costo_envase": 10.00, "costo_mano_obra": 6.00, "costo_unitario_total": 37.00},
]

# ─── Gastos operativos (último mes) ───
GASTOS = [
    {"fila": 2, "fecha": "2026-06-01", "categoria": "envases", "descripcion": "Botellas 345ml x100", "monto": 450.00},
    {"fila": 3, "fecha": "2026-06-03", "categoria": "ingredientes", "descripcion": "Fruta de temporada (mango, fresa)", "monto": 380.00},
    {"fila": 4, "fecha": "2026-06-05", "categoria": "transporte", "descripcion": "Entrega semanal al gimnasio", "monto": 80.00},
    {"fila": 5, "fecha": "2026-06-08", "categoria": "ingredientes", "descripcion": "Jengibre fresco y menta", "monto": 220.00},
    {"fila": 6, "fecha": "2026-06-10", "categoria": "marketing", "descripcion": "Promoción Instagram + Facebook", "monto": 150.00},
    {"fila": 7, "fecha": "2026-06-12", "categoria": "transporte", "descripcion": "Entrega semanal al gimnasio", "monto": 80.00},
    {"fila": 8, "fecha": "2026-06-15", "categoria": "operativo", "descripcion": "Etiquetas personalizadas x200", "monto": 300.00},
]

# ─── Idempotency keys almacenadas ───
IDEMPOTENCY_KEYS: set = set()


def get_next_fila(hoja: str) -> int:
    """Retorna el siguiente número de fila disponible."""
    if hoja == "Ventas":
        return max((r["fila"] for r in VENTAS), default=1) + 1
    elif hoja == "Gastos":
        return max((r["fila"] for r in GASTOS), default=1) + 1
    return 1
