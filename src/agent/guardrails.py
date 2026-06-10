"""Guardrails: validación pre-ejecución de tool calls."""

from datetime import datetime, date
from src.models.schemas import ValidationResult
from src.models.errors import (
    VALID_SABORES, VALID_CANALES, VALID_PRESENTACIONES,
    VALID_SHEETS, WRITABLE_SHEETS, VALID_OPERATIONS,
    VALID_REPORT_TYPES, VALID_CATEGORIAS_GASTO,
)


def validate_tool_call(tool_call: dict) -> ValidationResult:
    """Valida un tool call antes de ejecutarlo."""
    name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    if name == "sheets_reader":
        return _validate_sheets_reader(args)
    elif name == "sheets_writer":
        return _validate_sheets_writer(args)
    elif name == "calculator":
        return _validate_calculator(args)
    elif name == "report_generator":
        return _validate_report_generator(args)
    else:
        return ValidationResult(
            is_valid=False,
            error_code="UNKNOWN_TOOL",
            error_message=f"Tool '{name}' no reconocido.",
        )


def _validate_sheets_reader(args: dict) -> ValidationResult:
    hoja = args.get("hoja")
    if not hoja:
        return ValidationResult(
            is_valid=False, error_code="MISSING_PARAMS",
            error_message="El campo 'hoja' es requerido.", field="hoja",
        )
    if hoja not in VALID_SHEETS:
        return ValidationResult(
            is_valid=False, error_code="SHEET_NOT_FOUND",
            error_message=f"Hoja '{hoja}' no existe. Válidas: {', '.join(VALID_SHEETS)}",
            field="hoja",
        )
    # Validar filtros si existen
    filtros = args.get("filtros", {})
    if "canal" in filtros and filtros["canal"] not in VALID_CANALES:
        return ValidationResult(
            is_valid=False, error_code="INVALID_FILTER",
            error_message=f"Canal '{filtros['canal']}' inválido. Válidos: {', '.join(VALID_CANALES)}",
            field="filtros.canal",
        )
    if "presentacion" in filtros and filtros["presentacion"] not in VALID_PRESENTACIONES:
        return ValidationResult(
            is_valid=False, error_code="INVALID_FILTER",
            error_message=f"Presentación '{filtros['presentacion']}' inválida. Válidas: {', '.join(VALID_PRESENTACIONES)}",
            field="filtros.presentacion",
        )
    return ValidationResult(is_valid=True)


def _validate_sheets_writer(args: dict) -> ValidationResult:
    hoja = args.get("hoja")
    registro = args.get("registro", {})
    idempotency_key = args.get("idempotency_key")

    # Hoja válida y writable
    if not hoja or hoja not in WRITABLE_SHEETS:
        return ValidationResult(
            is_valid=False, error_code="INVALID_SHEET",
            error_message=f"No se puede escribir en '{hoja}'. Hojas escribibles: {', '.join(WRITABLE_SHEETS)}",
            field="hoja",
        )

    # Idempotency key requerido
    if not idempotency_key:
        return ValidationResult(
            is_valid=False, error_code="MISSING_PARAMS",
            error_message="El campo 'idempotency_key' es requerido.", field="idempotency_key",
        )

    # Validaciones específicas para Ventas
    if hoja == "Ventas":
        sabor = registro.get("sabor", "").lower()
        if sabor and sabor not in VALID_SABORES:
            return ValidationResult(
                is_valid=False, error_code="UNKNOWN_SABOR",
                error_message=f"Sabor '{sabor}' no reconocido. Válidos: {', '.join(VALID_SABORES)}",
                field="registro.sabor",
            )

        canal = registro.get("canal", "").lower()
        if canal and canal not in VALID_CANALES:
            return ValidationResult(
                is_valid=False, error_code="UNKNOWN_CANAL",
                error_message=f"Canal '{canal}' no reconocido. Válidos: {', '.join(VALID_CANALES)}",
                field="registro.canal",
            )

        presentacion = registro.get("presentacion", "")
        if presentacion and presentacion not in VALID_PRESENTACIONES:
            return ValidationResult(
                is_valid=False, error_code="VALIDATION_FAILED",
                error_message=f"Presentación '{presentacion}' inválida. Válidas: {', '.join(VALID_PRESENTACIONES)}",
                field="registro.presentacion",
            )

        cantidad = registro.get("cantidad")
        if cantidad is not None:
            if not isinstance(cantidad, int) or cantidad < 1 or cantidad > 1000:
                return ValidationResult(
                    is_valid=False, error_code="VALIDATION_FAILED",
                    error_message="'cantidad' debe ser entero positivo ≤ 1,000.",
                    field="registro.cantidad",
                )

        precio = registro.get("precio_unitario")
        if precio is not None:
            if not isinstance(precio, (int, float)) or precio <= 0 or precio > 500:
                return ValidationResult(
                    is_valid=False, error_code="VALIDATION_FAILED",
                    error_message="'precio_unitario' debe ser > 0 y ≤ 500.",
                    field="registro.precio_unitario",
                )

        fecha = registro.get("fecha")
        if fecha:
            try:
                parsed = datetime.strptime(fecha, "%Y-%m-%d").date()
                if parsed > date.today():
                    return ValidationResult(
                        is_valid=False, error_code="VALIDATION_FAILED",
                        error_message="La fecha no puede ser futura.",
                        field="registro.fecha",
                    )
            except ValueError:
                return ValidationResult(
                    is_valid=False, error_code="VALIDATION_FAILED",
                    error_message="Fecha debe estar en formato YYYY-MM-DD.",
                    field="registro.fecha",
                )

    # Validaciones para Gastos
    if hoja == "Gastos":
        categoria = registro.get("categoria", "").lower()
        if categoria and categoria not in VALID_CATEGORIAS_GASTO:
            return ValidationResult(
                is_valid=False, error_code="VALIDATION_FAILED",
                error_message=f"Categoría '{categoria}' inválida. Válidas: {', '.join(VALID_CATEGORIAS_GASTO)}",
                field="registro.categoria",
            )

        monto = registro.get("monto")
        if monto is not None:
            if not isinstance(monto, (int, float)) or monto <= 0 or monto > 100000:
                return ValidationResult(
                    is_valid=False, error_code="VALIDATION_FAILED",
                    error_message="'monto' debe ser > 0 y ≤ 100,000.",
                    field="registro.monto",
                )

    return ValidationResult(is_valid=True)


def _validate_calculator(args: dict) -> ValidationResult:
    operacion = args.get("operacion")
    if not operacion or operacion not in VALID_OPERATIONS:
        return ValidationResult(
            is_valid=False, error_code="UNKNOWN_OPERATION",
            error_message=f"Operación '{operacion}' no soportada. Válidas: {', '.join(VALID_OPERATIONS)}",
            field="operacion",
        )
    if "params" not in args:
        return ValidationResult(
            is_valid=False, error_code="MISSING_PARAMS",
            error_message="El campo 'params' es requerido.", field="params",
        )
    return ValidationResult(is_valid=True)


def _validate_report_generator(args: dict) -> ValidationResult:
    tipo = args.get("tipo_reporte")
    if not tipo or tipo not in VALID_REPORT_TYPES:
        return ValidationResult(
            is_valid=False, error_code="UNKNOWN_REPORT_TYPE",
            error_message=f"Tipo '{tipo}' no soportado. Válidos: {', '.join(VALID_REPORT_TYPES)}",
            field="tipo_reporte",
        )
    if "datos" not in args:
        return ValidationResult(
            is_valid=False, error_code="MISSING_DATA",
            error_message="El campo 'datos' es requerido.", field="datos",
        )
    return ValidationResult(is_valid=True)
