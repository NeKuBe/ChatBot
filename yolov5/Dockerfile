FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Instala Python, pip y otras dependencias
RUN apt-get update && apt-get install -y python3 python3-pip git libgl1-mesa-glx libglib2.0-0

WORKDIR /app

# Clona yolov5 e instala requerimientos
RUN git clone https://github.com/ultralytics/yolov5.git . 
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Instala FastAPI y uvicorn para la API
RUN pip3 install fastapi uvicorn python-multipart

# Copia tu main.py (la API)
COPY main.py .

# (Opcional) copia un modelo local si quieres evitar download
# COPY yolov5s.pt .

# Expone puerto 8001 (puedes cambiarlo)
EXPOSE 8001

# Ejecuta uvicorn para exponer FastAPI en la GPU
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]


