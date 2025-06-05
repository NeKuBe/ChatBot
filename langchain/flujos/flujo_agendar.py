# langchain_handler/flujos/flujo_agendar.py

def manejar_agendar(message: str, sender_id: str, nombre: str | None) -> list[str]:
    # Aquí podrías integrar con Google Calendar, Telegram o n8n
    # Por ahora, damos respuesta simple

    mensajes = []

    if nombre:
        mensajes.append(f"Claro {nombre}, puedo ayudarte a agendar una cita.")
    else:
        mensajes.append("Claro, puedo ayudarte a agendar una cita.")

    mensajes.append("¿Qué día y hora te gustaría traer tu consola o equipo?")
    mensajes.append("Por lo general atendemos de lunes a sábado entre 11 AM y 6 PM.")

    return mensajes
