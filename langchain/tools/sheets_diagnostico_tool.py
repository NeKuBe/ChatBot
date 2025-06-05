from langchain.tools import Tool 
import requests
from typing import Optional
import time

def buscar_diagnostico(consulta: str) -> str:
    """Busca diagnóstico en Google Sheets - versión simplificada"""
    
    # Procesar consulta para extraer mejor información
    dispositivo, sintoma = extraer_info_basica(consulta)
    
    try:
        response = requests.post(
            "http://sheets:8004/consultar-diagnostico",
            json={
                "componente": sintoma,
                "modelo": dispositivo
            },
            timeout=8
        )
        
        if response.status_code != 200:
            return "Sistema de precios no disponible. Contacta directamente."
            
        data = response.json()
        
        if "error" in data:
            return "Sistema en mantenimiento. Trae tu dispositivo para cotización directa."
            
        resultado = data.get("resultado", "")
        
        if not resultado or "no se encontró" in resultado.lower():
            return "No encontré precio específico. Trae el dispositivo para diagnóstico ($100)."
        
        return resultado
        
    except requests.exceptions.Timeout:
        return "Sistema ocupado. Intenta en unos minutos."
    except Exception as e:
        return "Error de conexión. Sistema temporalmente no disponible."

def extraer_info_basica(consulta: str) -> tuple[str, str]:
    """Extrae información básica de la consulta"""
    consulta = consulta.lower()
    
    # Dispositivos
    dispositivo = ""
    if "series s" in consulta:
        dispositivo = "Xbox Series S"
    elif "series x" in consulta:
        dispositivo = "Xbox Series X"
    elif "xbox one x" in consulta:
        dispositivo = "Xbox One Fat/S/X"
    elif "xbox one s" in consulta:
        dispositivo = "Xbox One Fat/S/X"
    elif "xbox one" in consulta:
        dispositivo = "Xbox One Fat/S/X"
    elif "xbox 360" in consulta:
        dispositivo = "Xbox 360"
    elif "control" in consulta and "series" in consulta:
        dispositivo = "Control Xbox Series"
    elif "control" in consulta and "one" in consulta:
        dispositivo = "Control Xbox One"
    elif "control" in consulta and "360" in consulta:
        dispositivo = "Control Xbox 360"
    elif "control" in consulta:
        dispositivo = "Control Xbox One"
    
    # Síntomas
    sintoma = ""
    if "mantenimiento" in consulta or "limpieza" in consulta or "servicio" in consulta:
        sintoma = "Se sobrecalienta, hace ruido el ventilador, la consola se apaga al estar jugando"
    elif "hdmi" in consulta or "imagen" in consulta or "video" in consulta or "pantalla" in consulta:
        sintoma = "No muestra imagen en pantalla, puerto HDMI dañado visiblemente"
    elif "joystick" in consulta or "drift" in consulta or "palanca" in consulta or "mueve solo" in consulta:
        sintoma = "joystick con drift, se mueve solo, palanca rota"
    elif "gatillo rb" in consulta or "gatillo lb" in consulta:
        sintoma = "gatillo rb/lb no funciona"
    elif "gatillo rt" in consulta or "gatillo lt" in consulta:
        sintoma = "gatillo rt/lt no funciona"
    elif "gatillo" in consulta:
        sintoma = "gatillo rt/lt no funciona"
    elif "botones" in consulta or "boton" in consulta:
        sintoma = "botones a/b/x/y no funcionan, botones se atascan"
    elif "no prende" in consulta or "no enciende" in consulta or "enciende y se apaga" in consulta:
        sintoma = "No enciende, enciende y se apaga, hace sonido y/o enciende luz"
    else:
        sintoma = consulta
    
    return dispositivo, sintoma

# Herramienta simplificada
sheet_tool = Tool.from_function(
    func=buscar_diagnostico,
    name="ConsultarPreciosGGTech",
    description="Consulta precios de reparación. Usa solo para preguntas de precios."
)
