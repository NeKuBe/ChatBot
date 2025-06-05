# langchain_handler/flujos/flujo_venta.py

def manejar_venta(message: str, sender_id: str, nombre: str | None) -> list[str]:
    mensajes = []

    if nombre:
        mensajes.append(f"Hola {nombre}, sí tenemos algunos accesorios disponibles 👉")
    else:
        mensajes.append("Sí tenemos algunos accesorios y refacciones disponibles 🏠")

    mensajes.append("Por ahora manejamos ventas solo locales. ¿Qué estás buscando exactamente?")
    mensajes.append("Si me das el modelo o tipo de accesorio, te digo si lo tengo en stock.")

    return mensajes
