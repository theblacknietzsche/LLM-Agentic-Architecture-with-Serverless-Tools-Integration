"""Cloud Function: Sheets Reader — Lee datos de Google Sheets (producción)."""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
SA_PATH = os.getenv("SHEETS_SERVICE_ACCOUNT_PATH")

SHEET_RANGES = {
    "Ventas": "Ventas!A:G",
    "Costos": "Costos!A:F",
    "Gastos": "Gastos!A:D",
}


def get_sheets_service():
    creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def main(request):
    """HTTP Cloud Function entry point."""
    body = request.get_json(silent=True) or {}
    payload = body.get("payload", {})
    hoja = payload.get("hoja", "")

    if hoja not in SHEET_RANGES:
        return json.dumps({
            "status": "error",
            "error": {"code": "SHEET_NOT_FOUND", "message": f"Hoja '{hoja}' no existe."},
        }), 404

    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=SHEET_RANGES[hoja],
        ).execute()

        rows = result.get("values", [])
        if not rows:
            return json.dumps({
                "status": "success",
                "data": {"hoja": hoja, "total_registros": 0, "registros": []},
            }), 200

        headers = [h.lower().strip() for h in rows[0]]
        registros = []
        for i, row in enumerate(rows[1:], start=2):
            record = {"fila": i}
            for j, header in enumerate(headers):
                record[header] = row[j] if j < len(row) else ""
            registros.append(record)

        # Aplicar filtros
        filtros = payload.get("filtros", {})
        for key, value in filtros.items():
            if key == "mes":
                registros = [r for r in registros if str(r.get("fecha", "")).startswith(value)]
            elif key in ("sabor", "canal", "presentacion", "categoria"):
                registros = [r for r in registros if str(r.get(key, "")).lower() == value.lower()]

        return json.dumps({
            "status": "success",
            "data": {"hoja": hoja, "total_registros": len(registros), "registros": registros},
        }), 200

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": {"code": "SHEETS_API_ERROR", "message": str(e)},
        }), 502
