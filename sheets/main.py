from fastapi import FastAPI
from sheets_handler import get_diagnosticos
from fastapi.encoders import jsonable_encoder

app = FastAPI()

@app.post("/consultar-diagnostico")
async def consultar_diagnostico(data: dict):
    componente = data.get("componente", "").lower()
    modelo = data.get("modelo", "").lower()
    
    try:
        registros = get_diagnosticos()
        resultados = []
        
        for row in registros:
            if componente in row['componente'].lower():
                if row.get("modelo_exacto", "").lower() == "sí" and modelo:
                    if modelo in row.get('modelo_referencia', '').lower():
                        resultados.append(row)
                else:
                    resultados.append(row)
        
        if not resultados:
            return {"resultado": f"No se encontró ningún diagnóstico para {componente}."}
        
        mensajes = []
        for r in resultados:
            precio = r['precio_mano_obra']
            stock = r['stock']
            pieza = r['pieza_necesaria']
            necesita_modelo = r.get("modelo_exacto", "").lower() == "sí"
            
            if stock.lower() == "no":
                mensaje = (
                    f"🛠️ Diagnóstico: {r['diagnostico_probable']}\n"
                    f"💸 Mano de obra: ${precio}\n"
                    f"📦 Pieza: {pieza} (no disponible en stock)\n"
                    f"🚚 Buscar en tiendas online: Mercado Libre, Amazon, AliExpress\n"
                    f"⚠️ Requiere adelanto por el costo de la pieza.\n"
                )
                if necesita_modelo:
                    mensaje += "🔍 Requiere modelo exacto (ej. CUH-1215A)"
                mensajes.append(mensaje)
            else:
                mensajes.append(
                    f"🛠️ Diagnóstico: {r['diagnostico_probable']}\n"
                    f"💸 Mano de obra: ${precio}\n"
                    f"📦 Pieza: {pieza} (en stock)"
                )
        
        return {"resultado": "\n\n".join(mensajes)}
    
    except Exception as e:
        return {"error": str(e), "resultado": f"Error al consultar diagnósticos: {str(e)}"}