from fastapi import FastAPI, UploadFile, File
import easyocr
import numpy as np
import cv2

app = FastAPI()
reader = easyocr.Reader(['es', 'en'], gpu=True)

@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    result = reader.readtext(img)
    return {"text": result}