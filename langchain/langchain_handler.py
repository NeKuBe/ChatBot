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

# Suprimir warnings innecesarios
warnings.filterwarnings("ignore", message=".*sentence-transformers.*")

# === Clase de memoria persistente en PostgreSQL ===
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
        cur.execute("""
            SELECT role, content FROM chat_history
            WHERE sender_id = %s ORDER BY timestamp ASC
        """, (self.sender_id,))
        messages = []
        for role, content in cur.fetchall():
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

# === Cargar documento PDF ===
loader = PyPDFLoader("docs/ggtech_base.pdf")
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
client = HttpClient(host="chroma", port=8000)
vectorstore = Chroma.from_documents(docs, embeddings, collection_name="ggtech_base", client=client)
retriever = vectorstore.as_retriever()

llm = ChatOllama(base_url="http://ollama:11434", model="llama3.2", temperature=0.7)

# === Funciones auxiliares ===
def get_nombre_cliente(sender_id: str) -> str | None:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM clientes WHERE sender_id = %s", (sender_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def guardar_nombre_cliente(sender_id: str, nombre: str):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clientes (sender_id, nombre)
        VALUES (%s, %s)
        ON CONFLICT (sender_id) DO UPDATE SET nombre = EXCLUDED.nombre
    """, (sender_id, nombre))
    conn.commit()
    cur.close()
    conn.close()

def dividir_respuesta_en_mensajes(respuesta: str, max_largo: int = 130) -> list[str]:
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

    emojis = ["😉", "🎮", "🔧", "✅", "📍", "👍"]
    for i in range(len(mensajes)):
        if not mensajes[i].endswith("💬") and len(mensajes[i]) > 20:
            mensajes[i] += " " + random.choice(emojis)
    return "|||".join(mensajes)

def extraer_nombre(texto: str) -> str | None:
    patrones = [
        r"[Mm]e llamo (\w+)",
        r"[Ss]oy (\w+)", 
        r"[Mm]i nombre es (\w+)"
    ]
    for pat in patrones:
        match = re.search(pat, texto)
        if match:
            return match.group(1).capitalize()
    return None

# === Proceso principal mejorado ===
def process_message(message: str, sender_id: str) -> list[str]:
    try:
        nombre = get_nombre_cliente(sender_id)

        # Manejo inicial de nombres
        if not nombre:
            if any(palabra in message.lower() for palabra in ["me llamo", "soy", "mi nombre es"]):
                nombre_detectado = extraer_nombre(message)
                if nombre_detectado:
                    guardar_nombre_cliente(sender_id, nombre_detectado)
                    return [f"¡Perfecto {nombre_detectado}! ¿En qué puedo ayudarte hoy? 😊"]
            return ["¡Hola! Soy tu técnico de GG-Tech. ¿Cómo te llamas para personalizar tu atención? 👨🔧"]

        # Configuración del agente conversacional
        memory = PostgresConversationMemory(sender_id=sender_id, db_config=db_config)
        chat_history = memory.load_memory_variables({}).get("chat_history", [])

        agent = initialize_agent(
            tools=[sheet_tool],
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=2,
            agent_kwargs={
                "system_message": f"""Eres técnico especializado de GG-Tech. Respuestas naturales y técnicas.
                
                Reglas estrictas:
                1. Nunca usar formatos de lista
                2. Usar herramienta automáticamente con términos como: fuente, hdmi, placa, pantalla
                3. Pedir detalles solo si falta información crítica
                4. Mantener conversación coloquial pero profesional
                
                Ejemplo bueno ✅:
                Usuario: "Mi PS5 se apaga solo"
                Tú: "¿El modelo es CUH-1215A? ¿Notaste sobrecalentamiento?"
                """
            }
        )

        # Procesamiento inteligente
        response = agent.run({
            "input": f"{message} (Contexto técnico: {nombre})",
            "chat_history": chat_history
        })
        
        return dividir_respuesta_en_mensajes(response)

    except Exception as e:
        error_msg = f"""🔧 ¡Ups! Algo no salió bien. Intenta formular tu consulta como:
        - "Mi Xbox no da video"
        - "¿Cuánto cuesta reparar un HDMI?"
        - "La PS5 hace ruido raro"
        """
        return [error_msg]