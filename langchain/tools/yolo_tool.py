from langchain.tools import Tool
import requests

def detectar_objetos(image_path: str) -> str:
    with open(image_path, "rb") as f:
        response = requests.post("http://yolo:8002/detect", files={"file": f})
    return response.json().get("result", "No se detectaron objetos")

yolo_tool = Tool(
    name="Detector_YOLOv5",
    func=detectar_objetos,
    description="Detecta objetos y daños visibles con YOLOv5."
)
