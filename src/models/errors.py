"""Códigos de error estandarizados para BrewFinance Agent."""


# ─── Error codes por tool ───

TOOL_ERRORS = {
    # sheets_reader
    "SHEET_NOT_FOUND": {"http": 404, "message": "La hoja solicitada no existe."},
    "INVALID_FILTER": {"http": 400, "message": "El filtro contiene campos inválidos."},
    "EMPTY_RESULT": {"http": 200, "message": "La consulta no retornó registros."},

    # sheets_writer
    "VALIDATION_FAILED": {"http": 400, "message": "Uno o más campos no pasan validación."},
    "INVALID_SHEET": {"http": 400, "message": "No se puede escribir en esa hoja."},
    "UNKNOWN_SABOR": {"http": 400, "message": "Sabor no reconocido."},
    "UNKNOWN_CANAL": {"http": 400, "message": "Canal no reconocido."},
    "DUPLICATE_DETECTED": {"http": 200, "message": "Registro duplicado detectado."},

    # calculator
    "UNKNOWN_OPERATION": {"http": 400, "message": "Operación no soportada."},
    "MISSING_PARAMS": {"http": 400, "message": "Faltan parámetros requeridos."},
    "INVALID_DATA": {"http": 400, "message": "Datos con formato incorrecto."},
    "DIVISION_BY_ZERO": {"http": 422, "message": "División por cero en el cálculo."},
    "INSUFFICIENT_DATA": {"http": 422, "message": "Datos insuficientes para el cálculo."},

    # report_generator
    "UNKNOWN_REPORT_TYPE": {"http": 400, "message": "Tipo de reporte no soportado."},
    "MISSING_DATA": {"http": 400, "message": "Faltan campos requeridos en datos."},
    "INVALID_DATA_FORMAT": {"http": 400, "message": "Formato de datos incorrecto."},

    # Comunes
    "SHEETS_API_ERROR": {"http": 502, "message": "Error de conexión con Google Sheets."},
    "AUTH_ERROR": {"http": 401, "message": "Credenciales inválidas o expiradas."},
    "RATE_LIMIT": {"http": 429, "message": "Cuota de API excedida."},
    "INTERNAL_ERROR": {"http": 500, "message": "Error interno del servidor."},
}

# ─── Constantes de negocio ───

VALID_SHEETS = ["Ventas", "Costos", "Gastos"]
WRITABLE_SHEETS = ["Ventas", "Gastos"]
VALID_SABORES = ["mango", "fresa", "limon", "jengibre", "menta"]
VALID_CANALES = ["gimnasio", "redes"]
VALID_PRESENTACIONES = ["345ml", "1L"]
VALID_CATEGORIAS_GASTO = ["ingredientes", "envases", "transporte", "marketing", "operativo", "otro"]
VALID_OPERATIONS = [
    "margen_por_sabor", "margen_por_canal", "proyeccion_ventas",
    "punto_equilibrio", "resumen_periodo", "comparar_presentaciones"
]
VALID_REPORT_TYPES = ["resumen_mensual", "comparativa_sabores", "recomendacion_precio", "analisis_canal"]


class BrewFinanceError(Exception):
    """Excepción base del agente."""
    def __init__(self, error_code: str, detail: str = ""):
        self.error_code = error_code
        self.detail = detail or TOOL_ERRORS.get(error_code, {}).get("message", "Error desconocido")
        self.http_status = TOOL_ERRORS.get(error_code, {}).get("http", 500)
        super().__init__(self.detail)
