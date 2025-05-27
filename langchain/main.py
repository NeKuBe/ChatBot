from fastapi import FastAPI, Request
from langchain_handler import process_message
import uvicorn

app = FastAPI()

@app.post("/langchain")
async def langchain(req: Request):
    try:
        data = await req.json()
        print("📩 Data recibida:", data)

        message = data.get("message", "")
        sender_id = data.get("sender_id", "")

        if not message or not sender_id:
            return {"error": "Faltan campos 'message' o 'sender_id'"}
        
        response = process_message(message, sender_id)
        return {"response": response}
    except Exception as e:
        print("💥 Error en el handler:", str(e))
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003)
