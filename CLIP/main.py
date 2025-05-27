from fastapi import FastAPI, UploadFile, File
from clip_handler import classify_image  # este es tu módulo CLIP
import uvicorn

app = FastAPI()

@app.post("/classify")
async def classify(file: UploadFile = File(...)):
    result = classify_image(await file.read())
    return {"result": result}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
