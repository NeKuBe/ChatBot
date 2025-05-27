import torch
import clip
from PIL import Image
import io

# Cargar modelo CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Subcategorías organizadas
YOLO_LABELS = [
    "No enciende (luz apagada en consola)",
    "Sin imagen (consola muestra luz de que esta encendida)",
    "Imagen distorsionada o con artefactos",
    "Sobrecalentamiento o polvo en ventilacion",
    "Lector optico danado o atorado",
    "HDMI o USB visiblemente danados",
    "Carcasa rota o botones rotos",
    "Presencia de liquidos u oxido visible",
    "Joystick con drift (posicion anormal)",
    "Botones danados o caidos en control",
    "Luz LED en control sin encender",
    "Olor a quemado o componentes chamuscados",
    "Consola abierta o con modificaciones visibles"
]

OCR_LABELS = [
    "Error: No se pudo iniciar el sistema",
    "Codigo de error CE-34878-0",
    "Pantalla de actualizacion fallida",
    "Sistema bloqueado o pantalla de advertencia",
    "Mensaje: Disco no reconocido",
    "Sin conexion: Error de red",
    "Error al iniciar sesion en cuenta",
    "Advertencia de sobrecalentamiento",
    "No se detecta dispositivo Bluetooth",
    "Microfono no disponible",
    "Descarga corrupta o incompleta",
    "Juego danado o no inicia"
    "Pantalla azul visible (BSOD o error grafico)",
]

def classify_image(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_input = preprocess(image).unsqueeze(0).to(device)

    def predict(labels):
        text_inputs = torch.cat([clip.tokenize(label) for label in labels]).to(device)
        with torch.no_grad():
            logits_per_image, _ = model(image_input, text_inputs)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        top_idx = probs.argmax()
        return labels[top_idx], probs[top_idx]

    yolo_label, yolo_conf = predict(YOLO_LABELS)
    ocr_label, ocr_conf = predict(OCR_LABELS)

    if yolo_conf > ocr_conf:
        return {"label": yolo_label, "confidence": float(yolo_conf), "category": "YOLO"}
    else:
        return {"label": ocr_label, "confidence": float(ocr_conf), "category": "OCR"}
