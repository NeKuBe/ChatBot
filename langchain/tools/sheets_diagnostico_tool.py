# toolfrom langchain.tools import Tool
from langchain.tools import Tool 
import requests
from typing import Optional

def buscar_diagnostico(componente: str, modelo: Optional[str] = None) -> str:
    try:
        response = requests.post(
            "http://sheets:8004/consultar-diagnostico",
            json={
                "componente": componente,
                "modelo": modelo if modelo else ""
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            return f"⚠️ {data['error']}"
        return data.get("resultado", "No se encontraron resultados.")
    
    except requests.exceptions.RequestException as e:
        return f"⚠️ Error de conexión con el servicio Sheets: {str(e)}"
    except Exception as e:
        return f"⚠️ Error inesperado: {str(e)}"

sheet_tool = Tool.from_function(
    func=buscar_diagnostico,
    name="ConsultarPreciosGGTech",
    description=(
        "Usa esta herramienta para obtener diagnóstico técnico, precio de mano de obra y disponibilidad de piezas. "
        "Requiere el nombre del componente (ej. 'fuente de poder') y opcionalmente el modelo (ej. 'CUH-1215A')."
    )
)