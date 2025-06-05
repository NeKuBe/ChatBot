import re
import random

def detectar_intencion_flujo(message: str) -> dict:
    message_lower = message.lower()

    intenciones = {
        "diagnostico": {
            "palabras": ["cuanto cuesta", "precio", "reparar", "arreglar", "diagnostico", "cotizacion"],
            "flujo": "diagnostico"
        },
        "venta": {
            "palabras": ["venden", "comprar", "accesorios", "stock", "disponible", "tienen"],
            "flujo": "venta"
        },
        "seguimiento": {
            "palabras": ["como va", "estado", "listo", "cuando", "seguimiento", "estatus"],
            "flujo": "seguimiento"
        },
        "garantia": {
            "palabras": ["garantia", "garantía", "problema despues", "no funciona otra vez"],
            "flujo": "garantia"
        },
        "agendar": {
            "palabras": ["cita", "agendar", "horario", "cuando llevar", "apartar"],
            "flujo": "agendar"
        },
        "saludo": {
            "palabras": ["hola", "buenos dias", "buenas tardes", "que tal"],
            "flujo": "saludo"
        }
    }

    for intencion, data in intenciones.items():
        if any(p in message_lower for p in data["palabras"]):
            return {"tipo": intencion, "flujo": data["flujo"], "confianza": "alta"}

    return {"tipo": "chat_libre", "flujo": "chat_libre", "confianza": "baja"}

def extraer_nombre(texto: str) -> str | None:
    patrones = [
        r"[Mm]e llamo ([\w\-áéíóúÁÉÍÓÚñÑ]+)",
        r"[Ss]oy ([\w\-áéíóúÁÉÍÓÚñÑ]+)",
        r"[Mm]i nombre (?:es|:) ([\w\-áéíóúÁÉÍÓÚñÑ]+)",
        r"^([\w\-áéíóúÁÉÍÓÚñÑ]{3,15})$"
    ]
    texto = texto.strip()
    for pat in patrones:
        match = re.match(pat, texto)
        if match:
            return match.group(1).capitalize()
    return None

def dividir_respuesta_en_mensajes(respuesta: str, max_largo: int = 140) -> list[str]:
    """Divide textos largos en mensajes más conversacionales"""
    if "\n\n" in respuesta:
        mensajes = [p.strip() for p in respuesta.split("\n\n") if p.strip()]
    else:
        oraciones = respuesta.split(". ")
        mensajes = []
        actual = ""
        for o in oraciones:
            if len(actual) + len(o) + 1 <= max_largo:
                actual += (". " if actual else "") + o
            else:
                if actual:
                    mensajes.append(actual.strip())
                actual = o
        if actual:
            mensajes.append(actual.strip())

    # Añadir emojis ligeros
    emojis = ["🔧", "🎮", "⚡", "✅", "📍", "👍"]
    for i in range(len(mensajes)):
        if len(mensajes[i]) > 30 and random.randint(1, 3) == 1:
            if not any(e in mensajes[i] for e in emojis):
                mensajes[i] += " " + random.choice(emojis)
    
    return mensajes
