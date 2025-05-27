from langchain.tools import Tool
import requests

def transcribir_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        response = requests.post("http://whisper:8003/transcribe", files={"file": f})
    return response.json().get("text", "No se pudo transcribir")

whisper_tool = Tool(
    name="Transcriptor_Whisper",
    func=transcribir_audio,
    description="Transcribe notas de voz del cliente sobre problemas."
)
