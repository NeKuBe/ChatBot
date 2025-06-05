# langchain_handler/main_router.py

from cliente import get_cliente_info
from intencion import detectar_intencion_flujo
from flujo_inicial import manejar_saludo_inicial
# futuros import: flujo_diagnostico, flujo_seguimiento, etc.

def process_message(message: str, sender_id: str) -> list[str]:
    # Paso 1: Saludo o flujo inicial
    respuesta_inicial = manejar_saludo_inicial(message, sender_id)
    if respuesta_inicial:
        return respuesta_inicial

    # Paso 2: Obtener info del cliente y detectar intención
    cliente_info = get_cliente_info(sender_id)
    nombre = cliente_info["nombre"]
    estado_flujo = cliente_info["estado_flujo"]

    intencion = detectar_intencion_flujo(message)
    flujo = intencion["flujo"]

    # Paso 3: Enrutamiento según intención
    if flujo == "diagnostico":
        from flujos.flujo_diagnostico import manejar_diagnostico
        return manejar_diagnostico(message, sender_id, nombre)
    
    elif flujo == "agendar":
        from flujos.flujo_agendar import manejar_agendar
        return manejar_agendar(message, sender_id, nombre)
    
    elif flujo == "seguimiento":
        from flujos.flujo_seguimiento import manejar_seguimiento
        return manejar_seguimiento(sender_id, nombre)

    elif flujo == "garantia":
        from flujos.flujo_garantia import manejar_garantia
        return manejar_garantia(sender_id, nombre)

    elif flujo == "venta":
        return ["¡Claro! Tenemos algunos accesorios y servicios disponibles. ¿Qué estás buscando en particular?"]

    elif flujo == "saludo":
        return [f"¡Hola {nombre}!" if nombre else "¡Hola! ¿En qué te puedo ayudar hoy?"]

    else:
        return ["No estoy seguro de haber entendido. ¿Me puedes explicar un poco más lo que necesitas?"]
