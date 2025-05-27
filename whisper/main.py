from fastapi import FastAPI, File, UploadFile
from whisper_handler import transcribe_audio
import shutil
import os

app = FastAPI()

@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    result = transcribe_audio(temp_path)
    return result

