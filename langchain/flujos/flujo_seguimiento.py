# langchain_handler/flujos/flujo_seguimiento.py
from ..tickets import get_estado_ticket_cliente

def manejar_seguimiento(sender_id: str, nombre: str | None) -> list[str]:
    estado = get_estado_ticket_cliente(sender_id)

    if estado == "completo":
        return [f"Tu nota de servicio está registrada {nombre or ''}. Estamos trabajando en tu equipo. Te avisaremos cuando esté listo."]
    elif estado == "pendiente_datos":
        return ["Tenemos tu nota creada, pero faltan algunos datos. ¿Podrías darme tu apellido y teléfono?"]
    elif estado == "sin_ticket":
        return ["No encontré una nota reciente con tu número. ¿Quieres que hagamos una? 🛠️"]
    else:
        return [f"Tu estado actual es: {estado}. Si necesitas algo más, aquí estoy ✨"]
