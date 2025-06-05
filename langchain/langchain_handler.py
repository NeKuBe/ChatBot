from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMemory
from langchain.schema.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from chromadb import HttpClient
from tools.sheets_diagnostico_tool import sheet_tool
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
import psycopg2
import time
import random
import re
import warnings

warnings.filterwarnings("ignore", message=".*sentence-transformers.*")

# === Clase de memoria persistente ===
class PostgresConversationMemory(BaseMemory):
    def __init__(self, sender_id: str, db_config: dict):
        self._sender_id = sender_id
        self._db_config = db_config

    @property
    def sender_id(self):
        return self._sender_id

    @property
    def memory_variables(self):
        return ["chat_history"]

    @property
    def memory_key(self):
        return "chat_history"

    def _connect(self):
        return psycopg2.connect(**self._db_config)

    def load_memory_variables(self, inputs):
        conn = self._connect()
        cur = conn.cursor()
        # Cargar últimos 8 mensajes para mantener contexto relevante
        cur.execute("""
            SELECT role, content FROM chat_history
            WHERE sender_id = %s 
            AND content != '--- Nueva consulta ---'
            ORDER BY timestamp DESC LIMIT 8
        """, (self.sender_id,))
        messages = []
        for role, content in reversed(cur.fetchall()):
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        cur.close()
        conn.close()
        return {"chat_history": messages}

    def save_context(self, inputs, outputs):
        conn = self._connect()
        cur = conn.cursor()
        user_input = inputs.get("input") or inputs.get("question", "")
        ai_output = outputs.get("output") or outputs.get("answer", "")
        
        cur.execute("""
            INSERT INTO chat_history (sender_id, role, content)
            VALUES (%s, %s, %s), (%s, %s, %s)
        """, (
            self.sender_id, "user", user_input,
            self.sender_id, "ai", ai_output
        ))
        conn.commit()
        cur.close()
        conn.close()

    def clear(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_history WHERE sender_id = %s", (self.sender_id,))
        conn.commit()
        cur.close()
        conn.close()

# === Config DB ===
db_config = {
    "host": "postgresql",
    "port": 5432,
    "dbname": "ggtech",
    "user": "NeKuBe",
    "password": "Linkmaster11"
}

# === Cargar documentos y configurar LLM ===
loader = PyPDFLoader("docs/ggtech_base.pdf")
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
client = HttpClient(host="chroma", port=8000)
vectorstore = Chroma.from_documents(docs, embeddings, collection_name="ggtech_base", client=client)
retriever = vectorstore.as_retriever()

llm = ChatOllama(base_url="http://ollama:11434", model="llama3.2", temperature=0.3)

# === Funciones de gestión de clientes ===
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
    """Guarda/actualiza información del cliente"""
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
    """Actualiza solo el estado del flujo"""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
        UPDATE clientes SET estado_flujo = %s WHERE sender_id = %s
    """, (estado, sender_id))
    conn.commit()
    cur.close()
    conn.close()

# === Funciones de análisis de intención ===
def detectar_intencion_flujo(message: str) -> dict:
    """Detecta la intención específica del usuario según el flujo"""
    message_lower = message.lower()
    
    # Intenciones específicas del flujo
    intenciones = {
        # F1: Diagnóstico / Cotización
        "diagnostico": {
            "palabras": ["cuanto cuesta", "precio", "reparar", "arreglar", "diagnostico", "cotizacion"],
            "flujo": "diagnostico"
        },
        
        # F2: Stock / Venta (mencionas accesorios en tu PDF)
        "venta": {
            "palabras": ["venden", "comprar", "accesorios", "stock", "disponible", "tienen"],
            "flujo": "venta"
        },
        
        # F3: Seguimiento
        "seguimiento": {
            "palabras": ["como va", "estado", "listo", "cuando", "seguimiento", "estatus"],
            "flujo": "seguimiento"
        },
        
        # F4: Garantía
        "garantia": {
            "palabras": ["garantia", "garantía", "problema despues", "no funciona otra vez"],
            "flujo": "garantia"
        },
        
        # F5: Agendar
        "agendar": {
            "palabras": ["cita", "agendar", "horario", "cuando llevar", "apartar"],
            "flujo": "agendar"
        },
        
        # Saludo inicial
        "saludo": {
            "palabras": ["hola", "buenos dias", "buenas tardes", "que tal"],
            "flujo": "saludo"
        }
    }
    
    for intencion, data in intenciones.items():
        if any(palabra in message_lower for palabra in data["palabras"]):
            return {"tipo": intencion, "flujo": data["flujo"], "confianza": "alta"}
    
    return {"tipo": "chat_libre", "flujo": "chat_libre", "confianza": "baja"}

def extraer_nombre(texto: str) -> str | None:
    """Extrae nombre del texto"""
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

def usar_nombre_natural(nombre: str, mensaje_count: int = 0) -> bool:
    """Decide si usar el nombre de forma natural"""
    # Usar nombre en:
    # - Primer mensaje después del saludo
    # - Cada 4-5 mensajes aproximadamente
    # - Mensajes importantes (cotizaciones, confirmaciones)
    if mensaje_count == 0:  # Primer mensaje
        return True
    elif mensaje_count % random.randint(4, 6) == 0:  # Cada 4-6 mensajes
        return True
    else:
        return False

def dividir_respuesta_en_mensajes(respuesta: str, max_largo: int = 140) -> list[str]:
    """Divide respuestas largas en mensajes más naturales"""
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

    # Añadir emojis ocasionalmente
    emojis = ["🔧", "🎮", "⚡", "✅", "📍", "👍"]
    for i in range(len(mensajes)):
        if len(mensajes[i]) > 30 and random.randint(1, 3) == 1:
            if not any(emoji in mensajes[i] for emoji in emojis):
                mensajes[i] += " " + random.choice(emojis)
    
    return "|||".join(mensajes)
    
 # Agregar estas funciones al archivo langchain_handler.py

def detectar_aceptacion(message: str) -> bool:
    """Detecta si el cliente acepta la cotización"""
    palabras_aceptacion = [
        "si", "sí", "dale", "ok", "okay", "está bien", "me parece", 
        "acepto", "perfecto", "va", "sale", "cuando", "donde llevar",
        "está bien", "por mi bien", "me convence", "vamos"
    ]
    return any(palabra in message.lower() for palabra in palabras_aceptacion)

def generar_ticket_cliente(sender_id: str, nombre: str, problema: str, cotizacion: str) -> str:
    """Genera ticket/nota de servicio para cliente que acepta"""
    try:
        # Obtener información adicional del cliente si está disponible
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Crear tabla de tickets si no existe
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
        
        # Insertar ticket básico
        cur.execute("""
            INSERT INTO tickets (sender_id, nombre, problema, cotizacion)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (sender_id, nombre, problema, cotizacion))
        
        ticket_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return f"¡Perfecto {nombre}! Voy a generar tu nota de servicio #{ticket_id}."
        
    except Exception as e:
        print(f"Error creando ticket: {e}")
        return f"¡Perfecto {nombre}! Procedo con tu nota de servicio."

def solicitar_datos_ticket(sender_id: str) -> str:
    """Solicita datos adicionales para completar el ticket"""
    return "Para completar tu nota necesito: apellido y número de teléfono. ¿Me los puedes proporcionar?"

def procesar_datos_ticket(sender_id: str, message: str) -> str:
    """Procesa datos adicionales del ticket"""
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Verificar si hay ticket pendiente
        cur.execute("""
            SELECT id, nombre, problema, cotizacion FROM tickets 
            WHERE sender_id = %s AND estado = 'pendiente_datos'
            ORDER BY fecha_creacion DESC LIMIT 1
        """, (sender_id,))
        
        ticket = cur.fetchone()
        if not ticket:
            cur.close()
            conn.close()
            return None
            
        ticket_id, nombre, problema, cotizacion = ticket
        
        # Extraer apellido y teléfono del mensaje
        apellido, telefono = extraer_datos_contacto(message)
        
        if apellido and telefono:
            # Actualizar ticket completo
            cur.execute("""
                UPDATE tickets SET apellido = %s, telefono = %s, estado = 'completo'
                WHERE id = %s
            """, (apellido, telefono, ticket_id))
            conn.commit()
            
            # Generar resumen del ticket
            resumen = f"""📋 NOTA DE SERVICIO #{ticket_id}
            
Cliente: {nombre} {apellido}
Teléfono: {telefono}
Problema: {problema}
Cotización: {cotizacion}

¡Listo! Trae tu dispositivo cuando gustes. Ubicación: Misión de San Jorge 2702, Nueva Galicia."""
            
            cur.close()
            conn.close()
            return resumen
            
        else:
            cur.close()
            conn.close()
            return "Necesito tu apellido y número de teléfono. Ejemplo: 'López 6671234567'"
            
    except Exception as e:
        print(f"Error procesando datos: {e}")
        return "Error procesando datos. ¿Puedes repetir apellido y teléfono?"

def extraer_datos_contacto(text: str) -> tuple[str, str]:
    """Extrae apellido y teléfono del texto"""
    # Buscar teléfono (10 dígitos)
    telefono_match = re.search(r'\b(\d{10})\b', text)
    telefono = telefono_match.group(1) if telefono_match else ""
    
    # Extraer apellido (palabra antes o después del teléfono)
    words = text.split()
    apellido = ""
    
    for word in words:
        if not word.isdigit() and len(word) > 2 and word.isalpha():
            apellido = word.capitalize()
            break
    
    return apellido, telefono

def get_estado_ticket_cliente(sender_id: str) -> str:
    """Obtiene el estado del ticket del cliente"""
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


# === Función principal del flujo ===
# Cambiar la configuración del agente para evitar errores:

def process_message(message: str, sender_id: str) -> list[str]:
    try:
        cliente_info = get_cliente_info(sender_id)
        nombre = cliente_info["nombre"]
        estado_flujo = cliente_info["estado_flujo"]

        # Manejo de nombres (igual que antes)
        if not nombre:
            nombre_detectado = extraer_nombre(message)
            if nombre_detectado:
                guardar_cliente_info(sender_id, nombre_detectado, "registrado")
                return [f"¡Perfecto {nombre_detectado}! ¿En qué puedo ayudarte hoy?"]
            else:
                return ["¡Hola! Soy tu técnico de GG-Tech. ¿Cómo te llamas?"]

        # Manejo directo de consultas de precios SIN agente para evitar errores
        if any(palabra in message.lower() for palabra in ["cuanto", "precio", "costo", "sale"]):
            try:
                # Llamar directamente a la herramienta
                resultado = sheet_tool.func(message)
                
                # Agregar contexto y pregunta de seguimiento
                respuesta_final = f"{resultado} ¿Te parece bien el presupuesto?"
                
                actualizar_estado_flujo(sender_id, "diagnostico")
                return dividir_respuesta_en_mensajes(respuesta_final)
                
            except Exception as e:
                print(f"Error en consulta directa: {e}")
                return ["Error consultando precios. ¿Podrías repetir tu consulta?"]

        # Para otras consultas, usar agente SIMPLIFICADO
        try:
            memory = PostgresConversationMemory(sender_id=sender_id, db_config=db_config)
            
            # CONFIGURACIÓN SIMPLIFICADA DEL AGENTE
            agent = initialize_agent(
                tools=[sheet_tool],
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Cambiar tipo de agente
                memory=memory,
                verbose=False,  # Reducir verbosidad
                handle_parsing_errors=True,
                max_iterations=2,  # Reducir iteraciones
                early_stopping_method="force",  # Forzar parada
                return_intermediate_steps=False,  # No retornar pasos intermedios
                agent_kwargs={
                    "prefix": f"""Eres un técnico de GG-Tech. Cliente: {nombre}.

HERRAMIENTAS DISPONIBLES:
- ConsultarPreciosGGTech: Solo para consultas de precios

REGLAS SIMPLES:
1. Para precios de reparación → usa ConsultarPreciosGGTech
2. Para info general → responde directamente
3. Máximo 140 caracteres
4. Garantía: 3 meses

FORMATO DE RESPUESTA REQUERIDO:
Thought: [tu análisis]
Action: [herramienta si necesaria]
Action Input: [consulta]
Observation: [resultado]
Final Answer: [tu respuesta final]""",
                    "suffix": """

Pregunta: {input}
{agent_scratchpad}""",
                    "format_instructions": """Usa exactamente este formato:

Thought: Necesito analizar qué hacer
Action: NombreDeLaHerramienta  
Action Input: consulta específica
Observation: resultado de la herramienta
Thought: Ahora puedo responder
Final Answer: respuesta al usuario

O si no necesitas herramienta:

Thought: Puedo responder directamente
Final Answer: respuesta al usuario""",
                    "input_variables": ["input", "agent_scratchpad"]
                }
            )

            response = agent.run(input=message)
            
            return dividir_respuesta_en_mensajes(response)
            
        except Exception as agent_error:
            print(f"Error en agente: {agent_error}")
            
            # FALLBACK DIRECTO para evitar errores
            if "garantia" in message.lower():
                return ["Todos los trabajos tienen garantía de 3 meses. ¿Qué necesitas reparar?"]
            elif "ubicacion" in message.lower() or "donde" in message.lower():
                return ["Estamos en Misión de San Jorge 2702, Nueva Galicia. ¿En qué más puedo ayudarte?"]
            else:
                return ["¿En qué puedo ayudarte? Puedo cotizar reparaciones o darte info general."]

    except Exception as e:
        print(f"Error general: {e}")
        return ["Algo salió mal. ¿Podrías repetir tu consulta?"]