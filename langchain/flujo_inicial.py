from cliente import get_cliente_info, guardar_cliente_info, actualizar_estado_flujo
from intencion import detectar_intencion_flujo, extraer_nombre

def manejar_saludo_inicial(message: str, sender_id: str) -> list[str] | None:
    """
    Determina si se debe saludar o pedir nombre según el estado del flujo e intención.
    """
    cliente_info = get_cliente_info(sender_id)
    nombre = cliente_info["nombre"]
    estado_flujo = cliente_info["estado_flujo"]
    
    intencion = detectar_intencion_flujo(message)
    flujo_detectado = intencion["flujo"]

    # Si es un usuario completamente nuevo, saludar
    if estado_flujo == "nuevo":
        actualizar_estado_flujo(sender_id, "esperando_intencion")
        return ["¡Hola! Soy tu técnico de GG Tech. ¿En qué te puedo ayudar?"]

    # Si no hay nombre guardado y ya está en una intención relevante (diagnóstico o agendar)
    if not nombre and flujo_detectado in ["diagnostico", "agendar"]:
        nombre_detectado = extraer_nombre(message)
        if nombre_detectado:
            guardar_cliente_info(sender_id, nombre_detectado, "registrado")
            return [f"¡Gracias {nombre_detectado}! ¿Qué consola necesitas revisar?"]
        else:
            return ["¿Cómo te llamas para registrar tu nota de servicio?"]

    # En cualquier otro caso, no hacer nada especial
    return None
