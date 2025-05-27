from fastapi import FastAPI, UploadFile, File
import torch
from PIL import Image
import io

app = FastAPI()

# Carga modelo yolov5 con GPU (device='cuda')
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.to('cuda')

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    image_bytes = await file.read()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Inferencia
    results = model(img)

    # Formatea resultados (json)
    data = results.pandas().xyxy[0].to_dict(orient="records")

    return {"results": data}
