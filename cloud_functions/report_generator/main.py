"""Cloud Function: Report Generator — Genera resúmenes financieros estructurados."""


def handle_report(payload: dict) -> dict:
    """Punto de entrada del report generator."""
    tipo = payload.get("tipo_reporte")
    datos = payload.get("datos", {})

    generators = {
        "resumen_mensual": _resumen_mensual,
        "comparativa_sabores": _comparativa_sabores,
        "recomendacion_precio": _recomendacion_precio,
        "analisis_canal": _analisis_canal,
    }

    func = generators.get(tipo)
    if not func:
        return {
            "status": "error",
            "error": {"code": "UNKNOWN_REPORT_TYPE", "message": f"Tipo '{tipo}' no soportado."},
        }

    try:
        reporte = func(datos)
        return {"status": "success", "data": {"tipo_reporte": tipo, "reporte": reporte}}
    except Exception as e:
        return {"status": "error", "error": {"code": "INTERNAL_ERROR", "message": str(e)}}


def _resumen_mensual(datos: dict) -> dict:
    periodo = datos.get("periodo", "")
    ingresos = datos.get("ingresos_totales", 0)
    costos = datos.get("costos_produccion", 0)
    gastos = datos.get("gastos_operativos", 0)
    margen_bruto = datos.get("margen_bruto", 0)
    margen_pct = datos.get("margen_bruto_pct", 0)
    unidades = datos.get("unidades_totales", 0)

    return {
        "titulo": f"Resumen Financiero — {periodo}",
        "secciones": [
            {
                "subtitulo": "Resultados generales",
                "contenido": (
                    f"En {periodo} vendiste {unidades} unidades con ingresos de {ingresos} MXN. "
                    f"Costos de producción: {costos} MXN. Gastos operativos: {gastos} MXN. "
                    f"Margen bruto: {margen_bruto} MXN ({margen_pct}%)."
                ),
            },
        ],
    }


def _comparativa_sabores(datos: dict) -> dict:
    sabores = datos.get("sabores", [])
    secciones = []
    for i, s in enumerate(sabores, 1):
        secciones.append({
            "subtitulo": f"#{i} — {s.get('sabor', '').capitalize()}",
            "contenido": (
                f"Margen: {s.get('margen_porcentaje', 0)}% ({s.get('margen_absoluto', 0)} MXN/unidad). "
                f"Unidades vendidas: {s.get('unidades_vendidas', 0)}. "
                f"Ingresos: {s.get('ingresos', 0)} MXN."
            ),
        })
    return {"titulo": "Comparativa de Sabores por Rentabilidad", "secciones": secciones}


def _recomendacion_precio(datos: dict) -> dict:
    sabor = datos.get("sabor", "")
    precio_actual = datos.get("precio_actual", 0)
    precio_sugerido = datos.get("precio_sugerido", 0)
    margen_actual = datos.get("margen_actual_pct", 0)
    margen_nuevo = datos.get("margen_nuevo_pct", 0)

    return {
        "titulo": f"Recomendación de Precio — {sabor.capitalize()}",
        "sabor": sabor,
        "precio_actual": precio_actual,
        "precio_sugerido": precio_sugerido,
        "secciones": [
            {
                "subtitulo": "Análisis",
                "contenido": (
                    f"Precio actual: {precio_actual} MXN (margen {margen_actual}%). "
                    f"Precio sugerido: {precio_sugerido} MXN (margen estimado {margen_nuevo}%)."
                ),
            },
            {
                "subtitulo": "Recomendación",
                "contenido": (
                    f"Ajustar precio de {precio_actual} a {precio_sugerido} MXN. "
                    f"Impacto: margen sube de {margen_actual}% a {margen_nuevo}%."
                ),
            },
        ],
    }


def _analisis_canal(datos: dict) -> dict:
    canales = datos.get("canales", [])
    secciones = []
    for c in canales:
        secciones.append({
            "subtitulo": c.get("canal", "").capitalize(),
            "contenido": (
                f"Unidades: {c.get('unidades_vendidas', 0)}. "
                f"Ingresos: {c.get('ingresos', 0)} MXN. "
                f"Margen: {c.get('margen_porcentaje', 0)}%."
            ),
        })
    return {"titulo": "Análisis por Canal de Venta", "secciones": secciones}


def main(request):
    """HTTP Cloud Function entry point."""
    import json
    body = request.get_json(silent=True) or {}
    result = handle_report(body.get("payload", {}))
    return json.dumps(result), 200, {"Content-Type": "application/json"}
