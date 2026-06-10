"""Cloud Function: Calculator — Operaciones financieras para BrewFinance."""


def handle_calculation(payload: dict) -> dict:
    """Punto de entrada del calculator."""
    operacion = payload.get("operacion")
    params = payload.get("params", {})

    operations = {
        "margen_por_sabor": _margen_por_sabor,
        "margen_por_canal": _margen_por_canal,
        "proyeccion_ventas": _proyeccion_ventas,
        "punto_equilibrio": _punto_equilibrio,
        "resumen_periodo": _resumen_periodo,
        "comparar_presentaciones": _comparar_presentaciones,
    }

    func = operations.get(operacion)
    if not func:
        return {
            "status": "error",
            "error": {
                "code": "UNKNOWN_OPERATION",
                "message": f"Operación '{operacion}' no soportada. Válidas: {', '.join(operations.keys())}",
            },
        }

    try:
        resultado = func(params)
        return {"status": "success", "data": {"operacion": operacion, "resultado": resultado}}
    except ZeroDivisionError:
        return {"status": "error", "error": {"code": "DIVISION_BY_ZERO", "message": "División por cero en el cálculo."}}
    except Exception as e:
        return {"status": "error", "error": {"code": "INTERNAL_ERROR", "message": str(e)}}


def _margen_por_sabor(params: dict) -> list[dict]:
    ventas = params.get("ventas", [])
    costos = params.get("costos", [])
    costo_map = {c["sabor"]: c.get("costo_unitario_total", c.get("costo_unitario", 0)) for c in costos}

    # Agregar ventas por sabor
    sabor_data = {}
    for v in ventas:
        sabor = v.get("sabor", "")
        qty = v.get("cantidad", 0)
        precio = v.get("precio_unitario", 0)
        if sabor not in sabor_data:
            sabor_data[sabor] = {"unidades": 0, "ingresos": 0}
        sabor_data[sabor]["unidades"] += qty
        sabor_data[sabor]["ingresos"] += round(qty * precio, 2)

    resultados = []
    for sabor, data in sabor_data.items():
        costo_unit = costo_map.get(sabor, 0)
        costo_total = round(data["unidades"] * costo_unit, 2)
        margen_abs = round(data["ingresos"] - costo_total, 2)
        margen_pct = round((margen_abs / data["ingresos"]) * 100, 2) if data["ingresos"] > 0 else 0

        resultados.append({
            "sabor": sabor,
            "unidades_vendidas": data["unidades"],
            "ingresos": data["ingresos"],
            "costo_total": costo_total,
            "margen_absoluto": margen_abs,
            "margen_porcentaje": margen_pct,
        })

    resultados.sort(key=lambda x: x["margen_porcentaje"], reverse=True)
    return resultados


def _margen_por_canal(params: dict) -> list[dict]:
    ventas = params.get("ventas", [])
    costos = params.get("costos", [])
    costo_map = {c["sabor"]: c.get("costo_unitario_total", c.get("costo_unitario", 0)) for c in costos}

    canal_data = {}
    for v in ventas:
        canal = v.get("canal", "")
        qty = v.get("cantidad", 0)
        precio = v.get("precio_unitario", 0)
        sabor = v.get("sabor", "")
        costo_unit = costo_map.get(sabor, 0)

        if canal not in canal_data:
            canal_data[canal] = {"unidades": 0, "ingresos": 0, "costos": 0}
        canal_data[canal]["unidades"] += qty
        canal_data[canal]["ingresos"] += round(qty * precio, 2)
        canal_data[canal]["costos"] += round(qty * costo_unit, 2)

    resultados = []
    for canal, data in canal_data.items():
        margen_abs = round(data["ingresos"] - data["costos"], 2)
        margen_pct = round((margen_abs / data["ingresos"]) * 100, 2) if data["ingresos"] > 0 else 0
        resultados.append({
            "canal": canal,
            "unidades_vendidas": data["unidades"],
            "ingresos": data["ingresos"],
            "costo_total": data["costos"],
            "margen_absoluto": margen_abs,
            "margen_porcentaje": margen_pct,
        })

    return resultados


def _proyeccion_ventas(params: dict) -> dict:
    historico = params.get("ventas_historicas", [])
    meses = params.get("meses_a_proyectar", 3)

    if len(historico) < 2:
        return {"error": "Se necesitan al menos 2 meses de datos para proyectar."}

    valores = [h["unidades"] for h in historico]
    promedio = round(sum(valores) / len(valores))
    tendencia = "creciente" if valores[-1] > valores[0] else "decreciente" if valores[-1] < valores[0] else "estable"

    proyecciones = []
    for i in range(1, meses + 1):
        mes_base = historico[-1].get("mes", "")
        year, month = int(mes_base[:4]), int(mes_base[5:7])
        new_month = month + i
        new_year = year + (new_month - 1) // 12
        new_month = ((new_month - 1) % 12) + 1
        proyecciones.append({
            "mes": f"{new_year}-{new_month:02d}",
            "unidades_estimadas": promedio,
        })

    confianza = "baja" if len(historico) <= 3 else "media" if len(historico) <= 6 else "alta"

    return {
        "metodo": "promedio_movil",
        "datos_historicos": valores,
        "tendencia": tendencia,
        "proyecciones": proyecciones,
        "confianza": confianza,
        "nota": f"Proyección basada en {len(historico)} meses de datos.",
    }


def _punto_equilibrio(params: dict) -> dict:
    costos_fijos = params.get("costos_fijos_mensuales", 0)
    precio = params.get("precio_unitario", 0)
    costo_unit = params.get("costo_unitario", 0)

    margen_contrib = precio - costo_unit
    if margen_contrib <= 0:
        return {"error": "El margen de contribución es ≤ 0. No se puede calcular punto de equilibrio."}

    unidades_eq = round(costos_fijos / margen_contrib)
    ingreso_eq = round(unidades_eq * precio, 2)

    return {
        "unidades_equilibrio": unidades_eq,
        "ingreso_equilibrio": ingreso_eq,
        "margen_contribucion_unitario": round(margen_contrib, 2),
        "interpretacion": f"Necesitas vender al menos {unidades_eq} unidades/mes para cubrir costos fijos de {costos_fijos} MXN.",
    }


def _resumen_periodo(params: dict) -> dict:
    ventas = params.get("ventas", [])
    costos = params.get("costos", [])
    gastos = params.get("gastos", [])
    periodo = params.get("periodo", "")

    costo_map = {c["sabor"]: c.get("costo_unitario_total", c.get("costo_unitario", 0)) for c in costos}

    total_ingresos = sum(v.get("cantidad", 0) * v.get("precio_unitario", 0) for v in ventas)
    total_unidades = sum(v.get("cantidad", 0) for v in ventas)
    total_costos_prod = sum(v.get("cantidad", 0) * costo_map.get(v.get("sabor", ""), 0) for v in ventas)
    total_gastos = sum(g.get("monto", 0) for g in gastos)

    margen_bruto = total_ingresos - total_costos_prod
    margen_neto = margen_bruto - total_gastos
    margen_bruto_pct = round((margen_bruto / total_ingresos) * 100, 2) if total_ingresos > 0 else 0

    return {
        "periodo": periodo,
        "unidades_totales": total_unidades,
        "ingresos_totales": round(total_ingresos, 2),
        "costos_produccion": round(total_costos_prod, 2),
        "gastos_operativos": round(total_gastos, 2),
        "margen_bruto": round(margen_bruto, 2),
        "margen_bruto_pct": margen_bruto_pct,
        "margen_neto": round(margen_neto, 2),
    }


def _comparar_presentaciones(params: dict) -> list[dict]:
    ventas = params.get("ventas", [])
    costos = params.get("costos", [])
    costo_map = {}
    for c in costos:
        key = f"{c['sabor']}_{c.get('presentacion', '345ml')}"
        costo_map[key] = c.get("costo_unitario_total", c.get("costo_unitario", 0))

    pres_data = {}
    for v in ventas:
        pres = v.get("presentacion", "345ml")
        qty = v.get("cantidad", 0)
        precio = v.get("precio_unitario", 0)
        sabor = v.get("sabor", "")
        costo_key = f"{sabor}_{pres}"
        costo_unit = costo_map.get(costo_key, 0)

        if pres not in pres_data:
            pres_data[pres] = {"unidades": 0, "ingresos": 0, "costos": 0}
        pres_data[pres]["unidades"] += qty
        pres_data[pres]["ingresos"] += round(qty * precio, 2)
        pres_data[pres]["costos"] += round(qty * costo_unit, 2)

    resultados = []
    for pres, data in pres_data.items():
        margen_abs = round(data["ingresos"] - data["costos"], 2)
        margen_pct = round((margen_abs / data["ingresos"]) * 100, 2) if data["ingresos"] > 0 else 0
        resultados.append({
            "presentacion": pres,
            "unidades_vendidas": data["unidades"],
            "ingresos": data["ingresos"],
            "costo_total": data["costos"],
            "margen_absoluto": margen_abs,
            "margen_porcentaje": margen_pct,
        })

    return resultados


# ─── Entry point para Cloud Functions ───
def main(request):
    """HTTP Cloud Function entry point."""
    import json
    body = request.get_json(silent=True) or {}
    result = handle_calculation(body.get("payload", {}))
    return json.dumps(result), 200, {"Content-Type": "application/json"}
