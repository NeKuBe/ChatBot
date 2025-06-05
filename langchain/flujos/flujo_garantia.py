# langchain_handler/flujos/flujo_garantia.py

def manejar_garantia(sender_id: str, nombre: str | None) -> list[str]:
    mensajes = []

    if nombre:
        mensajes.append(f"Hola {nombre}, todos nuestros servicios tienen garantía de 3 meses 👌")
    else:
        mensajes.append("Todos nuestros servicios tienen garantía de 3 meses 💼")

    mensajes.append("Si ya trajiste tu equipo antes y tiene algún detalle, dime tu nombre completo o teléfono para revisarlo.")
    mensajes.append("O si fue reciente, dime qué está pasando y lo revisamos sin costo.")

    return mensajes
