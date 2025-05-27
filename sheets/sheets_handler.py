import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales_google.json", scope)
client = gspread.authorize(creds)

def get_diagnosticos():
    sheet = client.open("ggtech_diagnostico_y_stock").worksheet("Diagnóstico")
    data = sheet.get_all_records()
    return data