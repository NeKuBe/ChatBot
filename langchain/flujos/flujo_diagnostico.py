from ..intencion import dividir_respuesta_en_mensajes, detectar_aceptacion
from ..cliente import actualizar_estado_flujo
from tools.sheets_diagnostico_tool import sheet_tool
from ..tickets import generar_ticket_cliente, solicitar_datos_ticket, procesar_datos_ticket, get_estado_ticket_cliente

def manejar_diagnostico(message: str, sender_id: str, nombre: str | None) -> list[str]:
    try:
        # Si el usuario está dando datos de contacto para completar el ticket
        estado_ticket = get_estado_ticket_cliente(sender_id)
        if estado_ticket == "pendiente_datos":
            resultado = procesar_datos_ticket(sender_id, message)
            return dividir_respuesta_en_mensajes(resultado)

        # Intentar obtener cotización automática
        resultado = sheet_tool.func(message)
        respuesta = f"{resultado} ¿Te interesa que genere una nota de servicio con estos datos?"

        # Cambiar estado del flujo
        actualizar_estado_flujo(sender_id, "diagnostico")

        return dividir_respuesta_en_mensajes(respuesta)

    except Exception as e:
        print(f"[Error en flujo_diagnostico] {e}")
        return ["Hubo un problema al procesar tu diagnóstico. ¿Puedes intentar explicar el problema nuevamente?"]
