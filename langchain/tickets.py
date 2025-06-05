import psycopg2
import re

from cliente import get_cliente_info

# Puedes mover esto a config.py si lo deseas centralizado
db_config = {
    "host": "postgresql",
    "port": 5432,
    "dbname": "ggtech",
    "user": "NeKuBe",
    "password": "Linkmaster11"
}

def generar_ticket_cliente(sender_id: str, nombre: str, problema: str, cotizacion: str) -> str:
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                sender_id VARCHAR(100),
                nombre VARCHAR(100),
                apellido VARCHAR(100),
                telefono VARCHAR(20),
                problema TEXT,
                cotizacion TEXT,
                estado VARCHAR(50) DEFAULT 'pendiente_datos',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            INSERT INTO tickets (sender_id, nombre, problema, cotizacion)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (sender_id, nombre, problema, cotizacion))

        ticket_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return f"¡Perfecto {nombre}! Tu nota de servicio es la #{ticket_id}. ¿Me das tu apellido y número de teléfono para completarla?"

    except Exception as e:
        print(f"[Error generando ticket] {e}")
        return f"¡Perfecto {nombre}! Voy a generar tu nota de servicio. ¿Me das tu apellido y número de teléfono?"

def solicitar_datos_ticket(sender_id: str) -> str:
    return "¿Cuál es tu apellido y tu número de teléfono? Ejemplo: López 6671234567"

def procesar_datos_ticket(sender_id: str, message: str) -> str:
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        cur.execute("""
            SELECT id, nombre, problema, cotizacion FROM tickets 
            WHERE sender_id = %s AND estado = 'pendiente_datos'
            ORDER BY fecha_creacion DESC LIMIT 1
        """, (sender_id,))
        ticket = cur.fetchone()

        if not ticket:
            cur.close()
            conn.close()
            return "No encontré un ticket pendiente. ¿Te interesa que lo genere de nuevo?"

        ticket_id, nombre, problema, cotizacion = ticket

        apellido, telefono = extraer_datos_contacto(message)

        if apellido and telefono:
            cur.execute("""
                UPDATE tickets SET apellido = %s, telefono = %s, estado = 'completo'
                WHERE id = %s
            """, (apellido, telefono, ticket_id))
            conn.commit()

            resumen = f"""📋 NOTA DE SERVICIO #{ticket_id}

Cliente: {nombre} {apellido}
Teléfono: {telefono}
Problema: {problema}
Cotización: {cotizacion}

¡Listo! Trae tu dispositivo cuando gustes.
Ubicación: Misión de San Jorge 2702, Nueva Galicia."""
            cur.close()
            conn.close()
            return resumen
        else:
            cur.close()
            conn.close()
            return "Necesito tu apellido y número. Ejemplo: Hernández 6671234567"

    except Exception as e:
        print(f"[Error procesando datos ticket] {e}")
        return "Hubo un problema al guardar tus datos. ¿Puedes intentar de nuevo?"

def extraer_datos_contacto(text: str) -> tuple[str, str]:
    telefono_match = re.search(r'\b(\d{10})\b', text)
    telefono = telefono_match.group(1) if telefono_match else ""

    palabras = text.split()
    apellido = next((w.capitalize() for w in palabras if w.isalpha() and len(w) > 2), "")

    return apellido, telefono

def get_estado_ticket_cliente(sender_id: str) -> str:
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            SELECT estado FROM tickets 
            WHERE sender_id = %s 
            ORDER BY fecha_creacion DESC LIMIT 1
        """, (sender_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else "sin_ticket"
    except:
        return "sin_ticket"
