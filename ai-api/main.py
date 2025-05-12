from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

from faster_whisper import WhisperModel
import torch
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.datasets import LoadImages
from yolov5.utils.general import non_max_suppression
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torchvision.transforms as T

app = FastAPI()

# --- CARGA DE MODELOS ---
# Whisper (Español)
whisper_model = WhisperModel("small", compute_type="auto")

# YOLOv5
yolo_model = DetectMultiBackend("yolov5/yolov5s.pt", device='cuda' if torch.cuda.is_available() else 'cpu')

# CLIP
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# --- TRANSCRIPCIÓN DE AUDIO ---
@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    with NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    segments, _ = whisper_model.transcribe(tmp_path, language="es")
    transcription = " ".join([seg.text for seg in segments])
    Path(tmp_path).unlink()  # Eliminar archivo temporal

    return JSONResponse(content={"transcription": transcription})


# --- DETECCIÓN DE OBJETOS EN IMÁGENES (YOLO) ---
@app.post("/detect")
async def detect_image(file: UploadFile = File(...)):
    with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        image_path = tmp.name

    dataset = LoadImages(image_path, img_size=640, stride=yolo_model.stride, auto=True)
    results = []

    for path, img, im0s, vid_cap, s in dataset:
        img = torch.from_numpy(img).to(yolo_model.device).float() / 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        pred = yolo_model(img, augment=False)
        pred = non_max_suppression(pred, 0.25, 0.45, None, False)

        for det in pred:
            if len(det):
                for *xyxy, conf, cls in det:
                    results.append({
                        "class": int(cls),
                        "confidence": float(conf),
                        "bbox": [float(x.item()) for x in xyxy]
                    })

    Path(image_path).unlink()
    return JSONResponse(content={"detections": results})


# --- CLASIFICACIÓN POR TEXTO (CLIP) ---
@app.post("/clip")
async def clip_match(file: UploadFile = File(...), text: str = "pantalla con error"):
    with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        image_path = tmp.name

    image = Image.open(image_path).convert("RGB")
    inputs = clip_processor(text=[text], images=image, return_tensors="pt", padding=True)
    outputs = clip_model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)

    Path(image_path).unlink()
    return {"text": text, "confidence": probs[0][0].item()}
