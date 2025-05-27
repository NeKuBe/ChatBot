from langchain.tools import Tool
import requests

def usar_clip(image_path: str) -> str:
    with open(image_path, "rb") as f:
        response = requests.post("http://clip:8001/classify", files={"file": f})
    return response.json().get("result", "No se obtuvo resultado")

clip_tool = Tool(
    name="Clasificador_CLIP",
    func=usar_clip,
    description="Clasifica imágenes de consolas dañadas usando CLIP."
)
