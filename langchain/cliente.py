import psycopg2

# Config global, puedes mover esto a un config.py en el futuro
db_config = {
    "host": "postgresql",
    "port": 5432,
    "dbname": "ggtech",
    "user": "NeKuBe",
    "password": "Linkmaster11"
}

def get_cliente_info(sender_id: str) -> dict:
    """Obtiene información completa del cliente"""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("SELECT nombre, estado_flujo FROM clientes WHERE sender_id = %s", (sender_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        return {"nombre": result[0], "estado_flujo": result[1]}
    return {"nombre": None, "estado_flujo": "nuevo"}

def guardar_cliente_info(sender_id: str, nombre: str, estado_flujo: str = "activo"):
    """Guarda o actualiza la info básica del cliente"""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clientes (sender_id, nombre, estado_flujo)
        VALUES (%s, %s, %s)
        ON CONFLICT (sender_id) DO UPDATE SET 
            nombre = EXCLUDED.nombre,
            estado_flujo = EXCLUDED.estado_flujo
    """, (sender_id, nombre, estado_flujo))
    conn.commit()
    cur.close()
    conn.close()

def actualizar_estado_flujo(sender_id: str, estado: str):
    """Actualiza solo el estado del flujo actual"""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
        UPDATE clientes SET estado_flujo = %s WHERE sender_id = %s
    """, (estado, sender_id))
    conn.commit()
    cur.close()
    conn.close()
