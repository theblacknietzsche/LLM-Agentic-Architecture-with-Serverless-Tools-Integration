"""Cloud Function: Sheets Writer — Escribe datos en Google Sheets (producción)."""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
SA_PATH = os.getenv("SHEETS_SERVICE_ACCOUNT_PATH")

COLUMN_ORDER = {
    "Ventas": ["fecha", "sabor", "presentacion", "cantidad", "precio_unitario", "canal"],
    "Gastos": ["fecha", "categoria", "descripcion", "monto"],
}


def get_sheets_service():
    creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def main(request):
    """HTTP Cloud Function entry point."""
    body = request.get_json(silent=True) or {}
    payload = body.get("payload", {})
    hoja = payload.get("hoja", "")
    registro = payload.get("registro", {})
    idem_key = payload.get("idempotency_key", "")

    if hoja not in COLUMN_ORDER:
        return json.dumps({
            "status": "error",
            "error": {"code": "INVALID_SHEET", "message": f"No se puede escribir en '{hoja}'."},
        }), 400

    try:
        service = get_sheets_service()
        columns = COLUMN_ORDER[hoja]
        row = [str(registro.get(col, "")) for col in columns]

        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{hoja}!A:Z",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()

        return json.dumps({
            "status": "success",
            "data": {
                "hoja": hoja,
                "registro": registro,
                "idempotency_key": idem_key,
                "duplicado": False,
            },
        }), 200

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": {"code": "SHEETS_API_ERROR", "message": str(e)},
        }), 502
