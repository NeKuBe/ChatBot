from fastapi import FastAPI, UploadFile, File
import httpx
import uvicorn

app = FastAPI()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image_bytes = await file.read()
    async with httpx.AsyncClient() as client:
        clip_response = await client.post("http://chatbot-clip:8001/classify", files={"file": ("image.jpg", image_bytes)})
        yolo_response = await client.post("http://chatbot-yolov5:8002/detect", files={"file": ("image.jpg", image_bytes)})
        ocr_response = await client.post("http://chatbot-ocr:8004/ocr", files={"file": ("image.jpg", image_bytes)})
    
    return {
        "clip": clip_response.json(),
        "yolo": yolo_response.json(),
        "ocr": ocr_response.json()
    }
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
